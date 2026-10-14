/* app.js — экраны приложения «Репетитор ЦТ: Математика».
 *
 * Один и тот же код работает в Android WebView и в окне Windows: слой
 * платформы скрыт в CT.bridge (core.js). Здесь только интерфейс:
 * главная, варианты ЦТ, экзамен с таймером, тренировка, разбор ошибок с
 * однотипными заданиями, статистика, формулы, инструменты, настройки и «О
 * программе» с кликабельными контактами разработчика.
 *
 * Screens of the app; platform access always goes through CT.bridge.
 */
(function (global) {
  'use strict';

  var doc = global.document;
  var CT = global.CT;
  var U = CT.util, I = CT.i18n, B = CT.bridge, C = CT.content, A = CT.answer, M = CT.math, AN = CT.analytics;

  /* ------------------------------------------------------------------ *
   * 0. DOM helpers
   * ------------------------------------------------------------------ */
  function el(tag, attrs, children) {
    var node = doc.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (key) {
        if (key === 'class') node.className = attrs[key];
        else if (key === 'text') node.textContent = attrs[key];
        else if (key === 'html') node.innerHTML = attrs[key];
        else if (key.indexOf('on') === 0 && typeof attrs[key] === 'function') node.addEventListener(key.slice(2), attrs[key]);
        else if (attrs[key] !== null && attrs[key] !== undefined) node.setAttribute(key, attrs[key]);
      });
    }
    (children || []).forEach(function (child) {
      if (child === null || child === undefined) return;
      node.appendChild(typeof child === 'string' ? doc.createTextNode(child) : child);
    });
    return node;
  }
  function h(html) { var wrap = el('div', { html: html }); return wrap.firstElementChild; }
  function esc(text) {
    return String(text === null || text === undefined ? '' : text)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  function t(key) { return I.t.apply(I, arguments); }
  function $(sel, root) { return (root || doc).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || doc).querySelectorAll(sel)); }
  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }
  function go(hash) { global.location.hash = hash; }

  /* ------------------------------------------------------------------ *
   * 1. Локальное состояние и хранилище
   * ------------------------------------------------------------------ */
  var DEFAULT_SETTINGS = {
    lang: 'ru', theme: 'system', fontScale: 1, examMinutes: 180, dailyGoal: 20,
    autoAdvance: true, sound: true, vibrate: true, autoUpdate: true, baseUrl: '',
    keepScreenOn: true, simpleCalc: false,
  };

  var S = CT.store = {
    settings: Object.assign({}, DEFAULT_SETTINGS),
    progress: AN.empty(),
    session: null,
    loaded: false,
    dirty: {},

    load: function () {
      var self = this;
      return Promise.all([
        B.loadBlob('settings').catch(function () { return null; }),
        B.loadBlob('progress').catch(function () { return null; }),
        B.loadBlob('session').catch(function () { return null; }),
      ]).then(function (data) {
        var settings = data[0] || {};
        Object.keys(DEFAULT_SETTINGS).forEach(function (key) {
          if (settings[key] === undefined) settings[key] = DEFAULT_SETTINGS[key];
        });
        // «Портативный» отпечаток: экзамен по умолчанию 180 минут, цель — 20 заданий
        self.settings = settings;
        var progress = data[1] || {};
        var empty = AN.empty();
        Object.keys(empty).forEach(function (key) {
          if (progress[key] === undefined) progress[key] = empty[key];
        });
        self.progress = progress;
        self.session = data[2] || null;
        I.setLang(self.settings.lang);
        self.loaded = true;
        return self;
      });
    },

    /** Сохранение с задержкой (blobs пишутся файлом на диск). */
    save: function (key, value, immediate) {
      var self = this;
      this.dirty[key] = true;
      var write = function () {
        delete self.dirty[key];
        B.saveBlob(key, JSON.stringify(value)).catch(function (error) {
          if (global.console) global.console.warn('save ' + key + ' failed', error);
        });
      };
      if (immediate) { write(); return; }
      clearTimeout(this['_timer_' + key]);
      this['_timer_' + key] = setTimeout(write, 350);
    },
    saveSettings: function (immediate) { this.save('settings', this.settings, immediate); },
    saveProgress: function (immediate) { this.save('progress', this.progress, immediate); },
    saveSession: function (immediate) { this.save('session', this.session, immediate); },

    /** Сброс успеваемости (настройки и контакты не трогаем). */
    resetProgress: function () {
      this.progress = AN.empty();
      this.session = null;
      this.saveProgress(true);
      this.saveSession(true);
    },

    /** Запись решённого задания в общую статистику. */
    recordTask: function (task, correct, seconds) {
      AN.record(this.progress, task, correct, seconds);
      this.saveProgress();
    },
  };

  /* ------------------------------------------------------------------ *
   * 2. Ход теста / test runner model
   * ------------------------------------------------------------------ */
  var RUN = CT.runner = {

    /** Новый экзаменационный прогон по варианту года. */
    startVariant: function (variant, mode) {
      S.session = {
        id: U.uid(), kind: 'variant', mode: mode, year: variant.year,
        title: (I.lang === 'en' ? 'Variant ' : 'Вариант ') + variant.year,
        order: variant.tasks.map(function (task) { return task.id; }),
        answers: {}, checked: {}, marked: [], index: 0,
        startedAt: new Date().toISOString(), seconds: 0, finished: false,
      };
      S.saveSession(true);
      return S.session;
    },

    /** Бесконечная тренировка по теме (банк ЦТ + однотипные задания). */
    startPractice: function (topic, onlyAnalogous) {
      var pool = (onlyAnalogous ? C.analogByTopic(topic) : C.tasksByTopic(topic).concat(C.analogByTopic(topic)));
      if (!pool.length) pool = C.analogous.slice();
      var ids = U.shuffle(pool).map(function (task) { return task.id; });
      S.session = {
        id: U.uid(), kind: 'practice', mode: 'train', year: 0, topic: topic,
        title: C.topicTitle(topic), order: ids, answers: {}, checked: {}, marked: [], index: 0,
        startedAt: new Date().toISOString(), seconds: 0, finished: false, endless: true,
      };
      S.saveSession(true);
      return S.session;
    },

    /** Прогон по набору заданий (например, «отработка ошибок»). */
    startSet: function (tasks, title, mode) {
      S.session = {
        id: U.uid(), kind: 'set', mode: mode || 'train', year: 0, title: title,
        order: tasks.map(function (task) { return task.id; }),
        answers: {}, checked: {}, marked: [], index: 0,
        startedAt: new Date().toISOString(), seconds: 0, finished: false,
      };
      S.saveSession(true);
      return S.session;
    },

    current: function () {
      var run = S.session;
      if (!run) return null;
      return C.taskById(run.order[run.index]) || null;
    },
    taskAt: function (index) {
      var run = S.session;
      if (!run || index < 0 || index >= run.order.length) return null;
      return C.taskById(run.order[index]);
    },
    step: function (delta) {
      var run = S.session;
      if (!run) return;
      run.index = U.clamp(run.index + delta, 0, run.order.length - 1);
      S.saveSession();
    },
    jump: function (index) {
      var run = S.session;
      if (!run) return;
      run.index = U.clamp(index, 0, run.order.length - 1);
      S.saveSession();
    },
    mark: function (taskId) {
      var run = S.session;
      if (!run) return;
      var at = run.marked.indexOf(taskId);
      if (at >= 0) run.marked.splice(at, 1); else run.marked.push(taskId);
      S.saveSession();
    },

    /** Записать ответ. */
    setAnswer: function (taskId, value) {
      var run = S.session;
      if (!run) return;
      run.answers[taskId] = value;
      S.saveSession();
    },

    /** Проверить текущее задание (режим тренировки). */
    checkCurrent: function () {
      var run = S.session, task = this.current();
      if (!run || !task) return null;
      var user = run.answers[task.id];
      var correct = A.check(user, task);
      run.checked[task.id] = correct;
      S.recordTask(task, correct, 0);
      S.saveSession();
      return correct;
    },

    /** Завершить прогон и записать попытку целиком. */
    finish: function () {
      var run = S.session;
      if (!run || run.finished) return null;
      var self = this;
      var results = run.order.map(function (id) {
        var task = C.taskById(id);
        if (!task) return null;
        var user = run.answers[id];
        var correct = run.mode === 'exam' ? A.check(user, task) : !!run.checked[id];
        return { taskId: id, part: task.part, topic: task.topic, correct: correct, user: user === undefined ? '' : user };
      }).filter(Boolean);
      var answered = results.filter(function (r) { return String(r.user).trim() !== ''; }).length;
      results.forEach(function (result) {
        if (String(result.user).trim() === '' && run.mode === 'exam') result.correct = false;
      });
      var attempt = {
        id: run.id, kind: run.kind, mode: run.mode, year: run.year, title: run.title,
        startedAt: run.startedAt, finishedAt: new Date().toISOString(),
        seconds: run.seconds || 0, answered: answered,
        results: results,
      };
      run.finished = true;
      var perTask = results.length ? (run.seconds || 0) / results.length : 0;
      results.forEach(function (result) {
        // в тренировке задание уже записано в момент проверки — не считаем дважды
        if (run.mode !== 'exam' && run.checked[result.taskId] !== undefined) return;
        AN.record(S.progress, C.taskById(result.taskId) || result, result.correct, perTask);
      });
      S.progress.attempts = (S.progress.attempts || []).concat([attempt]);
      S.progress.streak = AN.computeStreak(S.progress);
      S.saveProgress(true);
      S.saveSession(true);
      B.keepScreenOn(false);
      return attempt;
    },

    /** Задания, разобранные неверно в последней попытке. */
    wrongTasks: function (attempt) {
      return (attempt ? attempt.results : []).filter(function (r) { return !r.correct; })
        .map(function (r) { return C.taskById(r.taskId); })
        .filter(Boolean);
    },

    /** Однотипные задания к списку ошибок (для закрепления). */
    analogousFor: function (tasks, limit) {
      var out = [], seen = {};
      tasks.forEach(function (task) {
        var sameTopic = C.analogByTopic(task.topic);
        var pool = sameTopic.length ? sameTopic : C.analogous;
        var picked = 0;
        for (var i = 0; i < pool.length && picked < (limit || 2); i++) {
          var candidate = pool[(i + task.n) % pool.length];
          if (seen[candidate.id]) continue;
          seen[candidate.id] = true;
          out.push(candidate);
          picked++;
        }
      });
      return out;
    },
  };

  /* ------------------------------------------------------------------ *
   * 3. Общие куски интерфейса
   * ------------------------------------------------------------------ */
  var UI = {};
  var chromeBound = false;

  /** Обработчики шапки: логотип, настройки и переключатель RU↔EN. */
  UI.bindChrome = function () {
    if (chromeBound) return;
    chromeBound = true;
    var brand = $('#brand');
    if (brand) brand.addEventListener('click', function () { go('#/home'); });
    var settings = $('#btn-settings');
    if (settings) settings.addEventListener('click', function () { go('#/settings'); });
    var language = $('#lang-toggle');
    if (language) language.addEventListener('click', function () {
      UI.changeLanguage(I.lang === 'ru' ? 'en' : 'ru');
    });
  };

  UI.changeLanguage = function (lang) {
    // These fields are local UI state rather than progress/session blobs.
    // Translate the screen without clearing an analogous answer or a search.
    var formulaSearch = $('#view input[type="search"]');
    var query = formulaSearch ? formulaSearch.value : null;
    var analogues = $$('.analogous-item', $('#view')).map(function (item) {
      return { id: item.getAttribute('data-task-id'), value: $('.answer-input', item).value,
        status: $('.feedback', item).classList.contains('good') ? 'good'
          : ($('.feedback', item).classList.contains('bad') ? 'bad' : null),
        solution: !$('.analogous-solution', item).classList.contains('hidden'),
        study: !$('.analogous-study', item).classList.contains('hidden') };
    });
    I.setLang(lang);
    S.settings.lang = I.lang;
    S.saveSettings(true);
    UI.chrome();
    UI.render();
    var newSearch = $('#view input[type="search"]');
    if (query !== null && newSearch) {
      newSearch.value = query;
      newSearch.dispatchEvent(new global.Event('input', { bubbles: true }));
    }
    $$('.analogous-item', $('#view')).forEach(function (item) {
      var saved = analogues.filter(function (state) { return state.id === item.getAttribute('data-task-id'); })[0];
      if (!saved) return;
      $('.answer-input', item).value = saved.value;
      $('.analogous-solution', item).classList.toggle('hidden', !saved.solution);
      if (saved.status) {
        var feedback = $('.feedback', item);
        feedback.className = 'feedback ' + saved.status;
        feedback.textContent = t(saved.status === 'good' ? 'answer_correct' : 'answer_incorrect');
      }
      if (saved.study) {
        var holder = $('.analogous-study', item);
        var block = UI.studyBlock(C.taskById(saved.id));
        if (block) { holder.appendChild(block); holder.classList.remove('hidden'); }
      }
    });
    if ($('#modal').classList.contains('open') && modalRefresh) modalRefresh(true);
  };

  /** Тема и размер шрифта: применяются к <html>, чтобы CSS подхватил сразу. */
  UI.applyAppearance = function () {
    var root = global.document && global.document.documentElement;
    if (!root) return;
    var theme = S.settings.theme || 'system';
    if (theme === 'system') root.removeAttribute('data-theme');
    else root.setAttribute('data-theme', theme);
    root.style.setProperty('--font-scale', String(S.settings.fontScale || 1));
    if (global.matchMedia && theme === 'system') {
      try {
        if (global.matchMedia('(prefers-color-scheme: dark)').matches) root.setAttribute('data-theme', 'dark');
      } catch (error) { /* системная тема недоступна — остаётся светлая */ }
    }
  };

  /** Шапка с переключателем языка и кнопкой настроек. */
  UI.chrome = function () {
    var langBtn = $('#lang-toggle');
    langBtn.textContent = I.lang === 'ru' ? 'EN' : 'RU';
    langBtn.title = t('language');
    $('#brand-name').textContent = t('app_name');
    doc.title = t('app_name');
    UI.applyAppearance();
  };

  /** Тост-уведомление (копится в контейнере #toast). */
  var toastTimer = null;
  CT.toast = function (message) {
    var box = $('#toast');
    if (!box) return;
    box.textContent = message;
    box.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { box.classList.remove('show'); }, 2600);
  };
  // CT.bridge.notify ищет тост интерфейса здесь
  CT.app = { toast: function (message) { CT.toast(message); } };

  // A theory window can be opened from the formula sheet. Retain the actual
  // DOM nodes (including input values and handlers), rather than rebuilding the
  // parent tool and losing its search query. No session/progress blobs change.
  var modalStack = [], modalFocus = null, modalRefresh = null;

  /** Модальное окно: принимает узел и заголовок. */
  UI.modal = function (title, node, options) {
    options = options || {};
    var overlay = $('#modal');
    var sheet = $('.sheet', overlay);
    if (options.push && overlay.classList.contains('open')) {
      modalStack.push({ nodes: Array.prototype.slice.call(sheet.childNodes),
        className: sheet.className, scrollTop: sheet.scrollTop, focus: doc.activeElement,
        lang: I.lang, refresh: modalRefresh });
    } else if (!options.keepHistory) {
      modalStack = [];
      modalFocus = doc.activeElement;
    }
    modalRefresh = options.refresh || null;
    clear(sheet);
    sheet.className = 'sheet' + (options.wide ? ' wide' : '') + (options.tall ? ' tall' : '');
    var head = el('div', { class: 'sheet-head' });
    if (modalStack.length) {
      var back = el('button', { class: 'icon-btn modal-back', type: 'button', text: '←', 'aria-label': t('prev') });
      back.addEventListener('click', UI.backModal);
      head.appendChild(back);
    }
    head.appendChild(el('h2', { id: 'modal-title', text: title }));
    if (options.language) {
      var language = el('button', { class: 'icon-btn lang modal-lang', type: 'button',
        text: I.lang === 'ru' ? 'EN' : 'RU', 'aria-label': t('language') });
      language.addEventListener('click', function () { UI.changeLanguage(I.lang === 'ru' ? 'en' : 'ru'); });
      head.appendChild(language);
    }
    var close = el('button', { class: 'icon-btn modal-close', type: 'button', text: '✕', 'aria-label': t('close') });
    close.addEventListener('click', UI.closeModal);
    head.appendChild(close);
    sheet.appendChild(head);
    var body = el('div', { class: 'sheet-body' });
    body.appendChild(node);
    sheet.appendChild(body);
    if (options.footer) sheet.appendChild(options.footer);
    sheet.scrollTop = 0;
    overlay.classList.add('open');
    doc.body.classList.add('modal-open');
    overlay.setAttribute('aria-hidden', 'false');
    overlay.setAttribute('aria-labelledby', 'modal-title');
    close.focus();
    return sheet;
  };
  UI.backModal = function () {
    var previous = modalStack.pop();
    if (!previous) { UI.closeModal(); return; }
    var sheet = $('.sheet', $('#modal'));
    clear(sheet);
    sheet.className = previous.className;
    previous.nodes.forEach(function (node) { sheet.appendChild(node); });
    sheet.scrollTop = previous.scrollTop;
    modalRefresh = previous.refresh;
    if (previous.lang !== I.lang && modalRefresh) {
      var focusKey = previous.focus && previous.focus.getAttribute('data-focus-key');
      modalRefresh(true);
      sheet.scrollTop = previous.scrollTop;
      if (focusKey) {
        var replacement = $$('[data-focus-key]', sheet).filter(function (node) { return node.getAttribute('data-focus-key') === focusKey; })[0];
        if (replacement) replacement.focus();
      }
      return;
    }
    if (previous.focus && previous.focus.isConnected) previous.focus.focus();
  };
  UI.closeModal = function () {
    var overlay = $('#modal');
    if (!overlay) return;
    overlay.classList.remove('open');
    doc.body.classList.remove('modal-open');
    overlay.setAttribute('aria-hidden', 'true');
    modalStack = [];
    modalRefresh = null;
    clear($('.sheet', overlay));
    if (modalFocus && modalFocus.isConnected) modalFocus.focus();
    else if ($('#view')) $('#view').focus();
    modalFocus = null;
  };
  CT.closeModal = UI.closeModal;

  doc.addEventListener('keydown', function (event) {
    if (!$('#modal').classList.contains('open')) return;
    if (event.key === 'Escape') { event.preventDefault(); UI.backModal(); return; }
    if (event.key !== 'Tab') return;
    var controls = $$('button:not(:disabled), input:not(:disabled), textarea:not(:disabled), a[href]', $('.sheet'));
    if (!controls.length) return;
    var first = controls[0], last = controls[controls.length - 1];
    if (event.shiftKey && (doc.activeElement === first || !$('.sheet').contains(doc.activeElement))) {
      event.preventDefault(); last.focus();
    } else if (!event.shiftKey && (doc.activeElement === last || !$('.sheet').contains(doc.activeElement))) {
      event.preventDefault(); first.focus();
    }
  });

  /** Подтверждение с двумя кнопками. */
  UI.confirm = function (message, onYes, yesLabel) {
    var node = el('div', {});
    node.appendChild(el('p', { text: message }));
    var row = el('div', { class: 'rowline end' });
    var no = el('button', { class: 'btn ghost', text: t('cancel') });
    no.addEventListener('click', UI.closeModal);
    var yes = el('button', { class: 'btn primary', text: yesLabel || t('yes') });
    yes.addEventListener('click', function () { UI.closeModal(); onYes(); });
    row.appendChild(no); row.appendChild(yes);
    node.appendChild(row);
    UI.modal(t('confirmation'), node);
  };

  /** Полоса-диаграмма значений (без canvas — работает везде). */
  UI.bars = function (items, options) {
    options = options || {};
    var wrap = el('div', { class: 'bars' });
    var max = Math.max.apply(null, items.map(function (item) { return item.value; }).concat([1]));
    items.forEach(function (item) {
      var row = el('div', { class: 'bar-row' });
      row.appendChild(el('div', { class: 'bar-label', text: item.label }));
      var track = el('div', { class: 'bar-track' });
      var fill = el('div', { class: 'bar-fill' });
      fill.style.width = Math.round(item.value / max * 100) + '%';
      if (item.color) fill.style.background = item.color;
      track.appendChild(fill);
      row.appendChild(track);
      row.appendChild(el('div', { class: 'bar-value', text: item.text || String(item.value) }));
      if (item.action) {
        row.classList.add('clickable');
        row.addEventListener('click', item.action);
      }
      wrap.appendChild(row);
    });
    if (!items.length) wrap.appendChild(el('p', { class: 'muted', text: t('no_data_yet') }));
    return wrap;
  };

  /** Круговая шкала процента (SVG, масштабируется). */
  UI.ring = function (percent, label) {
    var size = 132, radius = 56, circumference = 2 * Math.PI * radius;
    var value = U.clamp(percent, 0, 100);
    var svg = '<svg viewBox="0 0 ' + size + ' ' + size + '" class="ring" role="img">' +
      '<circle cx="' + size / 2 + '" cy="' + size / 2 + '" r="' + radius + '" class="ring-track"/>' +
      '<circle cx="' + size / 2 + '" cy="' + size / 2 + '" r="' + radius + '" class="ring-fill" ' +
      'stroke-dasharray="' + circumference + '" stroke-dashoffset="' +
      (circumference * (1 - value / 100)).toFixed(1) + '"/>' +
      '<text x="' + size / 2 + '" y="' + (size / 2 + 6) + '" text-anchor="middle" class="ring-text">' +
      Math.round(value) + '%</text></svg>';
    var wrap = el('div', { class: 'ring-wrap' });
    wrap.appendChild(h(svg));
    if (label) wrap.appendChild(el('div', { class: 'muted small', text: label }));
    return wrap;
  };

  /** Карточка задания с полем ответа и (в тренировке) разбором. */
  UI.taskCard = function (task, run, options) {
    options = options || {};
    var card = el('div', { class: 'card task-card' });
    var head = el('div', { class: 'task-head' });
    var badge = task.part === 'A' ? 'А' + task.n : 'В' + task.n;
    head.appendChild(el('span', { class: 'badge', text: badge }));
    head.appendChild(el('span', { class: 'muted small', text: C.topicTitle(task.topic) }));
    if (task.difficulty) head.appendChild(el('span', { class: 'muted small', text: '★'.repeat(task.difficulty) }));
    if (run && run.marked.indexOf(task.id) >= 0) head.appendChild(el('span', { class: 'badge warn', text: t('marked') }));
    card.appendChild(head);

    card.appendChild(el('div', { class: 'task-text', text: I.pick(task.text) }));

    var stored = run ? run.answers[task.id] : undefined;
    if (task.answerType === 'choice') {
      var options_ = I.pick(task.options) || [];
      var list = el('div', { class: 'options' });
      options_.forEach(function (option, index) {
        var letter = 'абвгде'.charAt(index);
        var isStored = stored !== undefined && A.normalize(stored) === A.normalize(option);
        var btn = el('button', {
          class: 'option' + (isStored ? ' selected' : ''),
          type: 'button',
          'data-index': index,
        });
        btn.appendChild(el('span', { class: 'letter', text: letter + ')' }));
        btn.appendChild(el('span', { class: 'option-value', text: option }));
        btn.addEventListener('click', function () {
          if (!run) return;
          RUN.setAnswer(task.id, option);
          UI.render();
        });
        list.appendChild(btn);
      });
      card.appendChild(list);
      if (options.onCheck) {
        // в тренировке вариант ответа проверяется кнопкой — как и задание с ответом
        var choiceRow = el('div', { class: 'answer-row' });
        var choiceCheck = el('button', { class: 'btn primary', text: t('check_answer') });
        choiceCheck.addEventListener('click', function () { options.onCheck(); });
        choiceRow.appendChild(choiceCheck);
        card.appendChild(choiceRow);
      }
    } else {
      var input = el('input', {
        class: 'answer-input', type: 'text', value: stored === undefined ? '' : stored,
        placeholder: t('answer_placeholder'), 'aria-label': t('answer_label'),
      });
      input.addEventListener('input', function () {
        if (run) RUN.setAnswer(task.id, input.value);
      });
      var row = el('div', { class: 'answer-row' });
      row.appendChild(input);
      if (options.onCheck) {
        var checkBtn2 = el('button', { class: 'btn primary', text: t('check_answer') });
        checkBtn2.addEventListener('click', function () { RUN.setAnswer(task.id, input.value); options.onCheck(); });
        row.appendChild(checkBtn2);
      }
      card.appendChild(row);
      card.appendChild(el('div', { class: 'muted small', text: t('answer_hint') }));
    }
    return card;
  };

  /** Build a figure only from finite coordinates and a fixed SVG allowlist.
   * Downloaded content can never supply markup, event attributes, URLs or CSS.
   * Validate the entire drawing before creating it: one bad last node rejects
   * the whole SVG. Captions remain readable even if a future pack is malformed.
   */
  UI.diagramSvg = function (figure) {
    var namespace = 'http://www.w3.org/2000/svg';
    var fields = { line: ['x1', 'y1', 'x2', 'y2'], circle: ['cx', 'cy', 'r'],
      ellipse: ['cx', 'cy', 'rx', 'ry'], rect: ['x', 'y', 'width', 'height'],
      polyline: ['points'], polygon: ['points'], text: ['x', 'y', 'text', 'anchor'] };
    var roles = ['axis', 'grid', 'primary', 'secondary', 'helper', 'region', 'point', 'openpoint', 'text'];
    if (!figure || figure.width !== 420 || figure.height !== 280 || !Array.isArray(figure.drawing) ||
        !figure.drawing.length || figure.drawing.length > 250) return null;
    var bilingual = function (value) {
      return value && ['ru', 'en'].every(function (lang) { return typeof value[lang] === 'string' && value[lang].trim(); });
    };
    var numeric = function (key, value) {
      var bound = key.charAt(0) === 'y' || ['cy', 'ry', 'height'].indexOf(key) >= 0 ? 280 : 420;
      return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= bound &&
        (['r', 'rx', 'ry', 'width', 'height'].indexOf(key) < 0 || value > 0);
    };
    if (!bilingual(figure.title) || !bilingual(figure.caption)) return null;
    var valid = figure.drawing.every(function (item) {
      var allowed = item && typeof item.kind === 'string' && Object.prototype.hasOwnProperty.call(fields, item.kind) ? fields[item.kind] : null;
      if (!allowed || roles.indexOf(item.role) < 0 || typeof item.filled !== 'boolean' ||
          Object.keys(item).some(function (key) { return ['kind', 'role', 'filled'].concat(allowed).indexOf(key) < 0; })) return false;
      return allowed.every(function (key) {
        var value = item[key];
        if (key === 'points') return Array.isArray(value) && value.length >= (item.kind === 'polygon' ? 3 : 2) &&
          value.length <= 500 && value.every(function (point) {
            return Array.isArray(point) && point.length === 2 && numeric('x', point[0]) && numeric('y', point[1]);
          });
        if (key === 'text') return bilingual(value);
        if (key === 'anchor') return ['start', 'middle', 'end'].indexOf(value) >= 0;
        return numeric(key, value);
      });
    });
    if (!valid) return null;
    var svg = doc.createElementNS(namespace, 'svg');
    svg.setAttribute('viewBox', '0 0 420 280');
    svg.setAttribute('class', 'diagram-svg');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', I.pick(figure.title) + '. ' + I.pick(figure.caption));
    svg.setAttribute('data-figure', figure.id);
    var title = doc.createElementNS(namespace, 'title');
    title.textContent = I.pick(figure.title);
    var desc = doc.createElementNS(namespace, 'desc');
    desc.textContent = I.pick(figure.caption);
    svg.appendChild(title); svg.appendChild(desc);
    figure.drawing.forEach(function (item) {
      var node = doc.createElementNS(namespace, item.kind);
      node.setAttribute('class', 'diagram-' + item.role + (item.filled ? ' diagram-filled' : ''));
      fields[item.kind].forEach(function (key) {
        if (key === 'text') node.textContent = I.pick(item.text);
        else if (key === 'anchor') node.setAttribute('text-anchor', item.anchor);
        else if (key === 'points') node.setAttribute('points', item.points.map(function (point) { return point.join(','); }).join(' '));
        else node.setAttribute(key, String(item[key]));
      });
      if (item.kind !== 'text') node.setAttribute('vector-effect', 'non-scaling-stroke');
      svg.appendChild(node);
    });
    return svg;
  };

  UI.diagramLegend = function (figure) {
    var legend = el('div', { class: 'diagram-legend' });
    (Array.isArray(figure.legend) ? figure.legend : []).forEach(function (item) {
      if (!item || ['primary', 'secondary', 'helper', 'axis', 'region', 'point'].indexOf(item.role) < 0) return;
      var label = el('span', { class: 'diagram-legend-item' });
      label.appendChild(el('span', { class: 'diagram-key diagram-' + item.role, 'aria-hidden': 'true' }));
      label.appendChild(el('span', { text: I.pick(item.text) }));
      legend.appendChild(label);
    });
    return legend;
  };

  /** Nested viewer: touch/keyboard zoom, internal panning, same one-level Back. */
  UI.openDiagram = function (figure) {
    var state = { scale: 1, x: 0, y: 0 };
    var render = function (keepHistory) {
      var wrap = el('div', { class: 'diagram-viewer', 'data-figure': figure.id });
      var controls = el('div', { class: 'diagram-controls' });
      var smaller = el('button', { class: 'btn diagram-zoom-out', type: 'button', text: '−', 'aria-label': t('theory_zoom_out') });
      var larger = el('button', { class: 'btn diagram-zoom-in', type: 'button', text: '+', 'aria-label': t('theory_zoom_in') });
      var fit = el('button', { class: 'btn diagram-zoom-reset', type: 'button', text: t('theory_zoom_reset') });
      var status = el('span', { class: 'diagram-zoom-status', 'aria-live': 'polite' });
      [smaller, larger, fit, status].forEach(function (node) { controls.appendChild(node); });
      var viewport = el('div', { class: 'diagram-viewport', tabindex: '0', 'aria-label': t('theory_pan_hint') });
      var svg = UI.diagramSvg(figure);
      if (svg) viewport.appendChild(svg);
      else viewport.appendChild(el('p', { text: t('theory_visual_unavailable') }));
      var update = function () {
        if (svg) svg.style.width = (state.scale * 100) + '%';
        status.textContent = t('theory_zoom_fmt', Math.round(state.scale * 100) + '%');
        smaller.disabled = state.scale <= 1;
        larger.disabled = state.scale >= 3;
      };
      smaller.addEventListener('click', function () { state.scale = Math.max(1, state.scale - .5); update(); });
      larger.addEventListener('click', function () { state.scale = Math.min(3, state.scale + .5); update(); });
      fit.addEventListener('click', function () {
        state.scale = 1; state.x = state.y = 0; viewport.scrollLeft = viewport.scrollTop = 0; update();
      });
      viewport.addEventListener('scroll', function () { state.x = viewport.scrollLeft; state.y = viewport.scrollTop; });
      update();
      wrap.appendChild(controls); wrap.appendChild(viewport);
      wrap.appendChild(UI.diagramLegend(figure));
      wrap.appendChild(el('p', { class: 'diagram-caption', text: I.pick(figure.caption) }));
      wrap.appendChild(el('p', { class: 'muted small', text: t('theory_pan_hint') }));
      var footer = el('div', { class: 'theory-footer' });
      var back = el('button', { class: 'btn', type: 'button', text: t('prev') });
      back.addEventListener('click', UI.backModal); footer.appendChild(back);
      UI.modal(I.pick(figure.title), wrap, { tall: true, wide: true, push: !keepHistory,
        keepHistory: !!keepHistory, language: true, refresh: render, footer: footer });
      viewport.scrollLeft = state.x; viewport.scrollTop = state.y;
    };
    render(false);
  };

  UI.diagramCard = function (figure, lessonId) {
    var block = el('figure', { class: 'theory-figure', 'data-figure': figure.id });
    block.appendChild(el('h4', { text: I.pick(figure.title) }));
    var svg = UI.diagramSvg(figure);
    block.appendChild(svg || el('p', { text: t('theory_visual_unavailable') }));
    block.appendChild(UI.diagramLegend(figure));
    block.appendChild(el('figcaption', { class: 'diagram-caption', text: I.pick(figure.caption) }));
    if (svg) {
      var enlarge = el('button', { class: 'btn diagram-enlarge', type: 'button', text: t('theory_enlarge'),
        'aria-haspopup': 'dialog', 'data-focus-key': 'figure-' + lessonId + '-' + figure.id });
      enlarge.addEventListener('click', function () { enlarge.focus(); UI.openDiagram(figure); });
      block.appendChild(enlarge);
    }
    return block;
  };

  /** Definitions, conditions of rules/theorems, and worked examples. */
  UI.openTheory = function (lessonIds, options) {
    options = options || {};
    var lessons = lessonIds.map(function (id) { return C.lessonById(id); }).filter(Boolean);
    if (!lessons.length) return;
    var render = function (keepHistory) {
      var savedScroll = keepHistory ? $('.sheet', $('#modal')).scrollTop : 0;
      var wrap = el('div', { class: 'theory-content' });
      if (options.formula) {
        wrap.appendChild(el('div', { class: 'banner info theory-formula', text: options.formula.formula }));
      }
      lessons.forEach(function (lesson) {
        var article = el('article', { class: 'theory-lesson', 'data-lesson': lesson.id });
        if (lessons.length > 1 || options.title) article.appendChild(el('h3', { text: I.pick(lesson.title) }));
        if (lesson.everyday) {
          var everyday = el('section', { class: 'theory-everyday' });
          everyday.appendChild(el('h3', { text: t('theory_everyday') }));
          (I.pick(lesson.everyday) || []).forEach(function (line) { everyday.appendChild(el('p', { text: line })); });
          article.appendChild(everyday);
        }
        [['definitions', 'theory_definitions'], ['rules', 'theory_rules']].forEach(function (section) {
          var block = el('section', { class: 'theory-' + section[0] });
          block.appendChild(el('h3', { text: t(section[1]) }));
          var list = el('ul', {});
          (I.pick(lesson[section[0]]) || []).forEach(function (line) { list.appendChild(el('li', { text: line })); });
          block.appendChild(list);
          article.appendChild(block);
        });
        var figures = (lesson.figures || []).map(function (id) { return C.figureById(id); }).filter(Boolean);
        if (figures.length) {
          var visuals = el('section', { class: 'theory-visuals' });
          visuals.appendChild(el('h3', { text: t('theory_visuals') }));
          figures.forEach(function (figure) { visuals.appendChild(UI.diagramCard(figure, lesson.id)); });
          article.appendChild(visuals);
        }
        (lesson.examples || []).forEach(function (example) {
          var block = el('section', { class: 'theory-example' });
          block.appendChild(el('h3', { text: t('theory_examples') }));
          block.appendChild(el('p', { text: I.pick(example.statement) }));
          var steps = el('ol', { class: 'steps' });
          (I.pick(example.steps) || []).forEach(function (step) { steps.appendChild(el('li', { text: step })); });
          block.appendChild(steps);
          article.appendChild(block);
        });
        wrap.appendChild(article);
      });
      var footer = el('div', { class: 'rowline theory-footer' });
      var back = el('button', { class: 'btn', type: 'button', text: t('prev') });
      back.addEventListener('click', UI.backModal);
      footer.appendChild(back);
      UI.modal(I.pick(options.title || lessons[0].title), wrap, { tall: true,
        push: !keepHistory, keepHistory: !!keepHistory, language: true,
        refresh: render, footer: footer });
      if (keepHistory) $('.sheet', $('#modal')).scrollTop = savedScroll;
    };
    render(false);
  };

  /** Native buttons: touch targets, keyboard activation and an explicit arrow. */
  UI.theoryButton = function (label, ids, className, title) {
    var button = el('button', { class: 'theory-trigger ' + (className || ''), type: 'button',
      title: t('theory_open'), 'aria-haspopup': 'dialog', 'data-lesson': ids.join(' ') });
    button.appendChild(el('span', { text: label }));
    button.appendChild(el('span', { class: 'theory-arrow', text: '›', 'aria-hidden': 'true' }));
    button.addEventListener('click', function () {
      button.focus();
      UI.openTheory(ids, { title: title });
    });
    return button;
  };

  UI.studyPoints = function (topic) {
    var study = C.studyFor(topic);
    var points = study ? (I.pick(study) || []) : [];
    var list = el('ul', { class: 'study-points' });
    points.forEach(function (point, index) {
      var id = (study.lessons || [])[index];
      list.appendChild(el('li', {}, [C.lessonById(id)
        ? UI.theoryButton(point, [id], 'study-point-link') : doc.createTextNode(point)]));
    });
    return list;
  };

  UI.formulaMatches = function (item, needle, group) {
    return !needle || (I.pick(item.name) + ' ' + (item.name.ru || '') + ' ' + (item.name.en || '') +
      ' ' + item.formula + ' ' + (group.ru || '') + ' ' + (group.en || '')).toLowerCase().indexOf(needle) >= 0;
  };

  UI.formulaRow = function (item) {
    var lesson = C.lessonById(item.lesson);
    var row = el(lesson ? 'button' : 'div', { class: 'formula-row' + (lesson ? ' theory-trigger formula-link' : ''),
      type: lesson ? 'button' : null, 'data-lesson': lesson ? lesson.id : null,
      title: lesson ? t('theory_open') : null, 'aria-haspopup': lesson ? 'dialog' : null });
    row.appendChild(el('span', { class: 'formula-name', text: I.pick(item.name) }));
    row.appendChild(el('span', { class: 'formula-body', text: item.formula }));
    if (lesson) {
      row.appendChild(el('span', { class: 'theory-arrow', text: '›', 'aria-hidden': 'true' }));
      row.addEventListener('click', function () {
        row.focus();
        UI.openTheory([lesson.id], { title: item.name, formula: item });
      });
    }
    return row;
  };

  /** One shared renderer in Study, error remediation and both formula sheets. */
  UI.formulaGroupCard = function (group, options) {
    options = options || {};
    var card = el('div', { class: (options.compact ? 'study-formulas' : 'card') + ' formula-group', 'data-group': group.id });
    var heading = el(options.compact ? 'h5' : 'h3', { class: 'formula-group-title' });
    var lessons = C.lessonsForGroup(group);
    heading.appendChild(lessons.length ? UI.theoryButton(I.pick(group),
      lessons.map(function (lesson) { return lesson.id; }), 'formula-group-link', group)
      : doc.createTextNode(I.pick(group)));
    card.appendChild(heading);
    (options.items || group.items || []).forEach(function (item) { card.appendChild(UI.formulaRow(item)); });
    return card;
  };

  /**
   * Тема для изучения: открывается сразу при неверном ответе.
   *
   * Короткий конспект темы и её формулы показываются прямо в разборе (ученик
   * не должен сам догадываться, что повторять), а кнопка ведёт на полный
   * экран темы с разобранными примерами.
   */
  UI.studyBlock = function (task) {
    if (!task) return null;
    var study = C.studyFor(task.topic);
    var groups = C.formulaGroupsFor(task.topic);
    if (!study && !groups.length) return null;
    var box = el('div', { class: 'study-topic', 'data-topic': task.topic });
    box.appendChild(el('h4', { text: t('study_topic_fmt', C.topicTitle(task.topic)) }));
    var points = study ? (I.pick(study) || []) : [];
    if (points.length) {
      box.appendChild(el('h5', { text: t('study_points') }));
      box.appendChild(UI.studyPoints(task.topic));
    }
    if (groups.length) {
      box.appendChild(el('h5', { text: t('study_formulas') }));
      groups.forEach(function (group) { box.appendChild(UI.formulaGroupCard(group, { compact: true })); });
    }
    var row = el('div', { class: 'rowline wrap' });
    var open = el('button', { class: 'btn primary', text: t('study_open') });
    open.addEventListener('click', function () { go('#/study/' + task.topic); });
    var practice = el('button', { class: 'btn ghost', text: t('study_practice') });
    practice.addEventListener('click', function () { go('#/practice/' + task.topic); });
    row.appendChild(open); row.appendChild(practice);
    box.appendChild(row);
    return box;
  };

  /** Разбор одного задания (используется в результатах и в тренажёре ошибок). */
  UI.breakdown = function (task, userAnswer, options) {
    options = options || {};
    var box = el('div', { class: 'breakdown' });

    var answers = el('div', { class: 'answer-compare' });
    answers.appendChild(h('<div class="compare-box ' + (A.check(userAnswer, task) ? 'good' : 'bad') + '">' +
      '<span class="compare-label">' + esc(t('your_answer')) + '</span>' +
      '<span class="compare-value">' + esc(userAnswer === undefined || userAnswer === '' ? '—' : userAnswer) + '</span></div>'));
    answers.appendChild(h('<div class="compare-box good"><span class="compare-label">' + esc(t('correct_answer')) +
      '</span><span class="compare-value">' + esc(A.pick(task.answer)) + '</span></div>'));
    box.appendChild(answers);

    var diagnoses = C.diagnoses(task);
    if (diagnoses.length) {
      var why = el('div', { class: 'why' });
      why.appendChild(el('h4', { text: t('why_wrong') }));
      var ul = el('ul', { class: 'diagnoses' });
      diagnoses.forEach(function (diagnosis) { ul.appendChild(el('li', { text: I.pick(diagnosis) })); });
      why.appendChild(ul);
      box.appendChild(why);
    }

    box.appendChild(el('h4', { text: t('solution') }));
    var steps = el('ol', { class: 'steps' });
    (I.pick(task.solution) || []).forEach(function (step) { steps.appendChild(el('li', { text: step })); });
    box.appendChild(steps);

    var hints = I.pick(task.hints) || [];
    if (hints.length) {
      var details = el('details', { class: 'hints' });
      details.appendChild(el('summary', { text: t('hints') }));
      var hintList = el('ul', {});
      hints.forEach(function (hint) { hintList.appendChild(el('li', { text: hint })); });
      details.appendChild(hintList);
      box.appendChild(details);
    }

    var meta = el('div', { class: 'muted small' });
    meta.textContent = [C.topicTitle(task.topic), task.src].filter(Boolean).join(' · ');
    box.appendChild(meta);

    // Неверный ответ: сразу открываем необходимую тему для изучения —
    // конспект и формулы этой темы, а не только правильный ответ.
    if (!A.check(userAnswer, task)) {
      var studyBlock = UI.studyBlock(task);
      if (studyBlock) box.appendChild(studyBlock);
    }

    if (options.analogous !== false) {
      var analogous = options.analogous || C.analogByTopic(task.topic).slice(0, 2);
      if (analogous.length) {
        box.appendChild(el('h4', { text: t('analogous_title') }));
        box.appendChild(el('p', { class: 'muted small', text: t('analogous_hint') }));
        analogous.forEach(function (item, index) { box.appendChild(UI.analogousItem(item, index + 1)); });
      }
    }
    return box;
  };

  /** Однотипное задание: ввести ответ, получить проверку и решение. */
  UI.analogousItem = function (task, index) {
    var wrap = el('div', { class: 'analogous-item', 'data-task-id': task.id });
    wrap.appendChild(el('div', { class: 'analogous-head', text: t('analogous_task_fmt', index) + ' · ' + C.topicTitle(task.topic) }));
    wrap.appendChild(el('div', { class: 'task-text', text: I.pick(task.text) }));
    var input = el('input', { class: 'answer-input', type: 'text', placeholder: t('answer_placeholder') });
    var check = el('button', { class: 'btn primary', text: t('check_answer') });
    var reveal = el('button', { class: 'btn ghost', text: t('show_solution') });
    var feedback = el('div', { class: 'feedback' });
    var solution = el('div', { class: 'hidden analogous-solution' });
    var steps = el('ol', { class: 'steps' });
    (I.pick(task.solution) || []).forEach(function (step) { steps.appendChild(el('li', { text: step })); });
    solution.appendChild(steps);
    var studyHolder = el('div', { class: 'hidden analogous-study' });
    var row = el('div', { class: 'answer-row' });
    row.appendChild(input); row.appendChild(check); row.appendChild(reveal);
    wrap.appendChild(row);
    wrap.appendChild(feedback);
    wrap.appendChild(solution);
    wrap.appendChild(studyHolder);
    check.addEventListener('click', function () {
      var ok = A.check(input.value, task);
      feedback.className = 'feedback ' + (ok ? 'good' : 'bad');
      feedback.textContent = ok ? t('answer_correct') : t('answer_incorrect');
      if (!ok) {
        solution.classList.remove('hidden');
        // Не только ссылка: тема аналогичного задания тоже открывается сразу.
        if (!studyHolder.firstChild) {
          var study = UI.studyBlock(task);
          if (study) studyHolder.appendChild(study);
        }
        studyHolder.classList.remove('hidden');
        if (typeof studyHolder.scrollIntoView === 'function') studyHolder.scrollIntoView({ block: 'start' });
      } else {
        studyHolder.classList.add('hidden');
      }
      S.recordTask(task, ok, 0);
      B.vibrate(ok ? 12 : 30);
    });
    reveal.addEventListener('click', function () { solution.classList.toggle('hidden'); });
    return wrap;
  };

  /* ------------------------------------------------------------------ *
   * 4. Экраны
   * ------------------------------------------------------------------ */
  var SCREENS = {};

  /** Главная. */
  SCREENS['#/home'] = function () {
    var totals = AN.totals(S.progress);
    var today = S.progress.daily[U.today()] || 0;
    var goal = S.settings.dailyGoal || 20;
    var root = el('section', { class: 'screen' });
    root.appendChild(h('<div class="hero"><h1>' + esc(t('app_name')) + '</h1>' +
      '<p class="muted">' + esc(t('app_tagline')) + '</p>' +
      '<div class="hero-actions">' +
      '<button class="btn primary" data-go="#/tests">' + esc(t('nav_tests')) + '</button>' +
      '<button class="btn" data-go="#/exam">' + esc(t('nav_exam')) + '</button>' +
      '<button class="btn" data-go="#/practice">' + esc(t('nav_practice')) + '</button>' +
      '</div></div>'));

    var cards = el('div', { class: 'grid-4' });
    cards.appendChild(h('<div class="card stat"><div class="stat-value">' + totals.tests + '</div><div class="muted">' + esc(t('stat_tests')) + '</div></div>'));
    cards.appendChild(h('<div class="card stat"><div class="stat-value">' + totals.tasks + '</div><div class="muted">' + esc(t('stat_tasks')) + '</div></div>'));
    cards.appendChild(h('<div class="card stat"><div class="stat-value">' + Math.round(totals.accuracy * 100) + '%</div><div class="muted">' + esc(t('stat_accuracy')) + '</div></div>'));
    cards.appendChild(h('<div class="card stat"><div class="stat-value">' + (S.progress.streak || 0) + '</div><div class="muted">' + esc(t('stat_streak')) + '</div></div>'));
    root.appendChild(cards);

    var goalCard = el('div', { class: 'card' });
    goalCard.appendChild(el('h3', { text: t('daily_goal') }));
    var progress = el('div', { class: 'progress' });
    var fill = el('div', { class: 'progress-fill' });
    fill.style.width = U.clamp(today / goal * 100, 0, 100) + '%';
    progress.appendChild(fill);
    goalCard.appendChild(progress);
    goalCard.appendChild(el('p', { class: 'muted small', text: t('daily_goal_fmt', today, goal) }));
    if (today >= goal) goalCard.appendChild(el('p', { class: 'banner good', text: t('goal_done') }));
    root.appendChild(goalCard);

    var weak = AN.weakTopics(S.progress, 3);
    if (weak.length) {
      var weakCard = el('div', { class: 'card' });
      weakCard.appendChild(el('h3', { text: t('weak_topics') }));
      weakCard.appendChild(UI.bars(weak.map(function (item) {
        return {
          label: C.topicTitle(item.topic),
          value: Math.round(item.rate * 100),
          text: Math.round(item.rate * 100) + '% · ' + item.total,
          color: item.rate < 0.5 ? '#e0555a' : (item.rate < 0.8 ? '#e0a84a' : '#4aa96c'),
          action: function () { go('#/practice/' + item.topic); },
        };
      })));
      root.appendChild(weakCard);
    }

    if (S.session && !S.session.finished) {
      var resume = el('div', { class: 'card accent' });
      resume.appendChild(el('h3', { text: t('resume_title') }));
      resume.appendChild(el('p', { class: 'muted', text: t('resume_text', S.session.title, S.session.index + 1, S.session.order.length) }));
      var resumeRow = el('div', { class: 'rowline' });
      var resumeBtn = el('button', { class: 'btn primary', text: t('resume') });
      resumeBtn.addEventListener('click', function () { go('#/run'); });
      var dropBtn = el('button', { class: 'btn ghost', text: t('discard') });
      dropBtn.addEventListener('click', function () {
        UI.confirm(t('discard_confirm'), function () { S.session = null; S.saveSession(true); UI.render(); });
      });
      resumeRow.appendChild(resumeBtn); resumeRow.appendChild(dropBtn);
      resume.appendChild(resumeRow);
      root.appendChild(resume);
    }
    return root;
  };

  /** Список вариантов. */
  SCREENS['#/tests'] = function () {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('nav_tests') }));
    root.appendChild(el('p', { class: 'muted', text: t('tests_intro') }));
    var variants = C.variants();
    var grid = el('div', { class: 'grid-2' });
    variants.forEach(function (variant) {
      var card = el('div', { class: 'card' });
      card.appendChild(el('h3', { text: (I.lang === 'en' ? 'Variant ' : 'Вариант ') + variant.year }));
      card.appendChild(el('p', { class: 'muted small', text: t('variant_parts_fmt', variant.partA, variant.partB) }));
      var row = el('div', { class: 'rowline' });
      var exam = el('button', { class: 'btn primary', text: t('start_exam') });
      exam.addEventListener('click', function () {
        RUN.startVariant(variant, 'exam');
        B.keepScreenOn(S.settings.keepScreenOn);
        go('#/run');
      });
      var train = el('button', { class: 'btn', text: t('start_train') });
      train.addEventListener('click', function () {
        RUN.startVariant(variant, 'train');
        B.keepScreenOn(S.settings.keepScreenOn);
        go('#/run');
      });
      row.appendChild(exam); row.appendChild(train);
      card.appendChild(row);
      grid.appendChild(card);
    });
    root.appendChild(grid);
    return root;
  };

  /** Отдельный экзамен (переход к выбору варианта). */
  SCREENS['#/exam'] = function () {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('nav_exam') }));
    root.appendChild(h('<div class="card"><p>' + esc(t('exam_rules_fmt', S.settings.examMinutes)) + '</p></div>'));
    root.appendChild(el('p', { class: 'muted', text: t('choose_variant') }));
    var grid = el('div', { class: 'grid-3' });
    C.variants().forEach(function (variant) {
      var btn = el('button', { class: 'btn big', text: String(variant.year) });
      btn.addEventListener('click', function () {
        RUN.startVariant(variant, 'exam');
        B.keepScreenOn(S.settings.keepScreenOn);
        go('#/run');
      });
      grid.appendChild(btn);
    });
    root.appendChild(grid);
    var custom = el('button', { class: 'btn', text: t('mixed_exam') });
    custom.addEventListener('click', function () {
      var pool = U.shuffle(C.bank).slice(0, 30);
      RUN.startSet(pool, t('mixed_exam_title'), 'exam');
      B.keepScreenOn(S.settings.keepScreenOn);
      go('#/run');
    });
    root.appendChild(custom);
    return root;
  };

  /** Прохождение: экзамен или тренировка. */
  SCREENS['#/run'] = function () {
    var run = S.session;
    if (!run) { go('#/tests'); return el('section', { class: 'screen' }); }
    if (run.finished) { go('#/result/' + run.id); return el('section', { class: 'screen' }); }
    var task = RUN.current();
    if (!task) { go('#/tests'); return el('section', { class: 'screen' }); }

    var root = el('section', { class: 'screen run-screen' });
    // во время варианта экран не гаснет (настройку можно выключить)
    B.keepScreenOn(!!S.settings.keepScreenOn);
    var head = el('div', { class: 'run-head' });
    head.appendChild(el('div', { class: 'run-title', text: run.title }));
    var timer = el('div', { class: 'timer', id: 'run-timer' });
    head.appendChild(timer);
    root.appendChild(head);

    var bar = el('div', { class: 'progress' });
    var fill = el('div', { class: 'progress-fill' });
    fill.style.width = ((run.index + 1) / run.order.length * 100) + '%';
    bar.appendChild(fill);
    root.appendChild(bar);
    root.appendChild(el('div', { class: 'muted small center', text: t('task_of_fmt', run.index + 1, run.order.length) }));

    // Экзамен: ответы проверяются только после завершения, кнопки «Проверить» нет.
    var card = UI.taskCard(task, run, run.mode === 'exam' ? {} : {
      onCheck: function () {
        var correct = RUN.checkCurrent();
        B.vibrate(correct ? 12 : 40);
        UI.render();
        if (!correct) {
          // при неверном ответе открываем необходимую тему: разбор с конспектом
          // темы уже отрисован — доводим его до экрана ученика
          var studyNode = doc.querySelector('.study-topic');
          if (studyNode && typeof studyNode.scrollIntoView === 'function') {
            studyNode.scrollIntoView({ block: 'start' });
          }
        }
        if (correct && S.settings.autoAdvance) {
          setTimeout(function () {
            if (!S.settings.autoAdvance) return;
            if (RUN.current() && RUN.current().id === task.id) { RUN.step(1); UI.render(); }
          }, 700);
        }
      },
    });
    root.appendChild(card);

    /** Подсказки: кнопка «подсказка» открывает 1–2 подсказки автора. */
    var hints = I.pick(task.hints) || [];
    var toolsCard = el('div', { class: 'card tools-strip' });
    var toolsRow = el('div', { class: 'rowline wrap' });
    var hintBtn = el('button', { class: 'btn ghost', text: t('tool_hint') });
    var hintShown = 0;
    hintBtn.disabled = !hints.length;
    hintBtn.addEventListener('click', function () {
      hintShown = Math.min(hintShown + 1, hints.length);
      UI.modal(t('hints'), el('div', {}, hints.slice(0, hintShown).map(function (text, index) {
        return el('p', { class: 'banner info', text: (index + 1) + '. ' + text });
      })));
      if (hintShown < hints.length) CT.toast(t('more_hints_fmt', hints.length - hintShown));
    });
    toolsRow.appendChild(hintBtn);
    [['calculator', t('tool_calculator')], ['sheet', t('tool_sheet')], ['scratch', t('tool_scratch')],
     ['graph', t('tool_graph')]].forEach(function (pair) {
      var btn = el('button', { class: 'btn ghost', text: pair[1] });
      btn.addEventListener('click', function () { TOOLS.open(pair[0], task); });
      toolsRow.appendChild(btn);
    });
    toolsCard.appendChild(toolsRow);
    root.appendChild(toolsCard);

    if (run.mode !== 'exam') {
      var status = run.checked[task.id];
      if (status !== undefined) {
        var feedback = el('div', { class: 'feedback ' + (status ? 'good' : 'bad') });
        feedback.textContent = status ? t('answer_correct') : t('answer_incorrect');
        root.appendChild(feedback);
        if (!status) {
          var breakdown = el('div', { class: 'card breakdown-card' });
          breakdown.appendChild(el('h3', { text: t('error_analysis') }));
          breakdown.appendChild(UI.breakdown(task, run.answers[task.id], { analogous: C.analogByTopic(task.topic).slice(0, 2) }));
          root.appendChild(breakdown);
        }
      }
    }

    var nav = el('div', { class: 'run-nav' });
    var prev = el('button', { class: 'btn', text: '← ' + t('prev') });
    prev.disabled = run.index === 0;
    prev.addEventListener('click', function () { RUN.step(-1); UI.render(); });
    var next = el('button', { class: 'btn', text: t('next') + ' →' });
    next.disabled = run.index >= run.order.length - 1;
    next.addEventListener('click', function () { RUN.step(1); UI.render(); });
    var mark = el('button', { class: 'btn ghost', text: t('mark') });
    mark.addEventListener('click', function () { RUN.mark(task.id); UI.render(); });
    var grid = el('button', { class: 'btn ghost', text: t('task_grid') });
    grid.addEventListener('click', function () { TOOLS.taskGrid(); });
    nav.appendChild(prev);
    nav.appendChild(mark);
    nav.appendChild(grid);
    nav.appendChild(next);
    root.appendChild(nav);

    var finishRow = el('div', { class: 'rowline center' });
    var finish = el('button', { class: 'btn primary', text: t('finish_test') });
    finish.addEventListener('click', function () {
      var unanswered = run.order.filter(function (id) {
        return String(run.answers[id] === undefined ? '' : run.answers[id]).trim() === '';
      }).length;
      var message = run.mode === 'exam' && unanswered
        ? t('unanswered_warning_fmt', unanswered)
        : t('finish_confirm');
      UI.confirm(message, function () {
        var attempt = RUN.finish();
        go('#/result/' + (attempt ? attempt.id : ''));
      }, t('finish_test'));
    });
    finishRow.appendChild(finish);
    root.appendChild(finishRow);

    if (run.mode === 'exam') startTimer(root, timer, run);
    else timer.textContent = U.duration(run.seconds, I.lang);

    return root;
  };

  /** Обратный отсчёт экзамена (перерисовывает только таймер). */
  var timerHandle = null;
  function startTimer(root, node, run) {
    clearInterval(timerHandle);
    var deadline = new Date(run.startedAt).getTime() + S.settings.examMinutes * 60000;
    var tick = function () {
      var left = Math.max(0, Math.round((deadline - Date.now()) / 1000));
      run.seconds = (S.settings.examMinutes * 60) - left;
      node.textContent = U.duration(left, I.lang);
      node.classList.toggle('low', left < 300);
      if (left <= 0) {
        clearInterval(timerHandle);
        CT.toast(t('time_is_up'));
        var attempt = RUN.finish();
        go('#/result/' + (attempt ? attempt.id : ''));
      }
    };
    tick();
    timerHandle = setInterval(tick, 1000);
  }

  /** Результаты попытки. */
  SCREENS['#/result'] = function (extra) {
    var attempt = findAttempt(extra);
    if (!attempt) { go('#/home'); return el('section', { class: 'screen' }); }
    var summary = AN.attemptSummary(attempt);
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('result_title') }));
    root.appendChild(el('p', { class: 'muted', text: attempt.title + ' · ' + U.formatDate(attempt.finishedAt, I.lang) }));

    var top = el('div', { class: 'grid-2' });
    var scoreCard = el('div', { class: 'card center' });
    scoreCard.appendChild(UI.ring(summary.percent * 100, t('percent_correct')));
    scoreCard.appendChild(el('p', { class: 'big', text: t('score_fmt', summary.correct, summary.total) }));
    top.appendChild(scoreCard);

    var details = el('div', { class: 'card' });
    details.appendChild(el('p', { text: t('part_a_fmt', summary.byPart.A.correct, summary.byPart.A.total) }));
    details.appendChild(el('p', { text: t('part_b_fmt', summary.byPart.B.correct, summary.byPart.B.total) }));
    details.appendChild(el('p', { text: t('time_spent_fmt', U.duration(summary.seconds, I.lang)) }));
    details.appendChild(el('p', { text: t('grade_fmt', summary.grade) }));
    top.appendChild(details);
    root.appendChild(top);

    var actions = el('div', { class: 'rowline wrap' });
    if (summary.mistakes.length) {
      var review = el('button', { class: 'btn primary', text: t('review_mistakes_fmt', summary.mistakes.length) });
      review.addEventListener('click', function () { go('#/mistakes/' + attempt.id); });
      actions.appendChild(review);
      var reinforce = el('button', { class: 'btn', text: t('reinforce') });
      reinforce.addEventListener('click', function () {
        var tasks = RUN.analogousFor(RUN.wrongTasks(attempt), 2);
        if (!tasks.length) { CT.toast(t('no_analogous')); return; }
        RUN.startSet(tasks, t('reinforce_title'), 'train');
        go('#/run');
      });
      actions.appendChild(reinforce);
    }
    var exportBtn = el('button', { class: 'btn ghost', text: t('export_report') });
    exportBtn.addEventListener('click', function () { exportReport(attempt); });
    actions.appendChild(exportBtn);
    var again = el('button', { class: 'btn ghost', text: t('to_tests') });
    again.addEventListener('click', function () { go('#/tests'); });
    actions.appendChild(again);
    root.appendChild(actions);

    var stats = AN.topicStats(S.progress);
    var topics = Object.keys(stats).map(function (key) {
      return { topic: key, rate: stats[key].rate, total: stats[key].total };
    }).sort(function (a, b) { return a.rate - b.rate; });
    if (topics.length) {
      var card = el('div', { class: 'card' });
      card.appendChild(el('h3', { text: t('by_topic') }));
      card.appendChild(UI.bars(topics.map(function (item) {
        return {
          label: C.topicTitle(item.topic), value: Math.round(item.rate * 100),
          text: Math.round(item.rate * 100) + '% · ' + item.total,
          color: item.rate < 0.5 ? '#e0555a' : (item.rate < 0.8 ? '#e0a84a' : '#4aa96c'),
        };
      })));
      root.appendChild(card);
    }
    return root;
  };

  function findAttempt(id) {
    if (!id) return (S.progress.attempts || [])[S.progress.attempts.length - 1] || null;
    var found = null;
    (S.progress.attempts || []).forEach(function (attempt) { if (attempt.id === id) found = attempt; });
    if (!found && S.session && S.session.id === id) {
      return { id: id, title: S.session.title, finishedAt: new Date().toISOString(), seconds: S.session.seconds, results: [] };
    }
    return found;
  }

  /** Полный разбор ошибок + однотипные задания. */
  SCREENS['#/mistakes'] = function (extra) {
    var attempt = findAttempt(extra);
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('mistakes_title') }));
    if (!attempt) { root.appendChild(el('p', { class: 'muted', text: t('no_data_yet') })); return root; }
    var wrong = RUN.wrongTasks(attempt);
    if (!wrong.length) {
      root.appendChild(h('<div class="banner good">' + esc(t('no_mistakes')) + '</div>'));
      return root;
    }
    root.appendChild(el('p', { class: 'muted', text: t('mistakes_intro_fmt', wrong.length) }));

    var reinforce = el('button', { class: 'btn primary', text: t('reinforce') });
    reinforce.addEventListener('click', function () {
      var tasks = RUN.analogousFor(wrong, 2);
      if (!tasks.length) { CT.toast(t('no_analogous')); return; }
      RUN.startSet(tasks, t('reinforce_title'), 'train');
      go('#/run');
    });
    root.appendChild(reinforce);

    var grouped = {};
    wrong.forEach(function (task) { (grouped[task.topic] = grouped[task.topic] || []).push(task); });

    wrong.forEach(function (task) {
      var result = null;
      (attempt.results || []).forEach(function (item) { if (item.taskId === task.id) result = item; });
      var card = el('div', { class: 'card' });
      var head = el('div', { class: 'task-head' });
      head.appendChild(el('span', { class: 'badge', text: (task.part === 'A' ? 'А' : 'В') + task.n }));
      head.appendChild(el('span', { class: 'muted small', text: C.topicTitle(task.topic) }));
      if (task.year) head.appendChild(el('span', { class: 'muted small', text: String(task.year) }));
      card.appendChild(head);
      card.appendChild(el('div', { class: 'task-text', text: I.pick(task.text) }));
      card.appendChild(UI.breakdown(task, result ? result.user : '', { analogous: C.analogByTopic(task.topic).slice(0, 2) }));
      root.appendChild(card);
    });

    var plan = el('div', { class: 'card accent' });
    plan.appendChild(el('h3', { text: t('repeat_topics') }));
    var ul = el('ul', {});
    Object.keys(grouped).forEach(function (topic) {
      var li = el('li', {});
      var link = el('a', { href: '#/study/' + topic, text: C.topicTitle(topic) });
      li.appendChild(link);
      li.appendChild(doc.createTextNode(' — ' + t('tasks_count_fmt', grouped[topic].length) + ' · '));
      li.appendChild(el('a', { href: '#/practice/' + topic, text: t('study_practice') }));
      ul.appendChild(li);
    });
    plan.appendChild(ul);
    root.appendChild(plan);
    return root;
  };

  /** Бесконечная тренировка: выбор темы или сразу тема из адреса. */
  SCREENS['#/practice'] = function (extra) {
    var root = el('section', { class: 'screen' });
    if (extra) {
      RUN.startPractice(extra, false);
      go('#/run');
      return root;
    }
    root.appendChild(el('h1', { text: t('nav_practice') }));
    root.appendChild(el('p', { class: 'muted', text: t('practice_intro') }));
    var stats = AN.topicStats(S.progress);
    var grid = el('div', { class: 'grid-3' });
    C.order.forEach(function (topic) {
      var entry = stats[topic];
      var card = el('button', { class: 'btn topic-btn' });
      card.appendChild(el('span', { class: 'topic-name', text: C.topicTitle(topic) }));
      card.appendChild(el('span', { class: 'muted small', text: entry
        ? t('topic_stats_fmt', Math.round(entry.rate * 100), entry.total)
        : t('tasks_count_fmt', C.tasksByTopic(topic).length + C.analogByTopic(topic).length) }));
      card.addEventListener('click', function () { RUN.startPractice(topic, false); B.keepScreenOn(S.settings.keepScreenOn); go('#/run'); });
      grid.appendChild(card);
    });
    root.appendChild(grid);
    return root;
  };

  /**
   * Изучение темы: конспект, формулы и разобранные примеры одной темы.
   *
   * Сюда приводит неверный ответ (разбор открывает эту тему сразу, кнопка
   * «Открыть тему» — сюда), раздел «Изучение» и план повторения в разборе
   * ошибок.
   */
  SCREENS['#/study'] = function (extra) {
    var root = el('section', { class: 'screen' });
    var topic = extra && C.topics[extra] ? extra : null;
    if (!topic) {
      root.appendChild(el('h1', { text: t('nav_study') }));
      root.appendChild(el('p', { class: 'muted', text: t('study_index_intro') }));
      var grid = el('div', { class: 'grid-3' });
      C.order.forEach(function (key) {
        var card = el('button', { class: 'btn topic-btn' });
        card.appendChild(el('span', { class: 'topic-name', text: C.topicTitle(key) }));
        card.appendChild(el('span', { class: 'muted small', text: t('tasks_count_fmt',
          C.tasksByTopic(key).length + C.analogByTopic(key).length) }));
        card.addEventListener('click', function () { go('#/study/' + key); });
        grid.appendChild(card);
      });
      root.appendChild(grid);
      return root;
    }

    root.appendChild(el('h1', { text: t('study_topic_fmt', C.topicTitle(topic)) }));
    root.appendChild(el('p', { class: 'muted', text: t('study_intro') }));
    if (S.session && !S.session.finished) {
      var returnBtn = el('button', { class: 'btn', text: t('return_to_task') });
      returnBtn.addEventListener('click', function () { go('#/run'); });
      root.appendChild(returnBtn);
    }

    var study = C.studyFor(topic);
    var points = study ? (I.pick(study) || []) : [];
    if (points.length) {
      var pointsCard = el('div', { class: 'card study-points-card' });
      pointsCard.appendChild(el('h3', { text: t('study_points') }));
      pointsCard.appendChild(UI.studyPoints(topic));
      root.appendChild(pointsCard);
    }

    var groups = C.formulaGroupsFor(topic);
    if (groups.length) {
      root.appendChild(el('h2', { text: t('study_formulas') }));
      var list = el('div', { class: 'formula-list' });
      groups.forEach(function (group) { list.appendChild(UI.formulaGroupCard(group)); });
      root.appendChild(list);
    }

    var examples = C.tasksByTopic(topic).concat(C.analogByTopic(topic)).slice(0, 3);
    if (examples.length) {
      root.appendChild(el('h2', { text: t('study_examples') }));
      examples.forEach(function (example) {
        var card = el('div', { class: 'card study-example' });
        card.appendChild(el('div', { class: 'task-text', text: I.pick(example.text) }));
        card.appendChild(el('p', {}, [el('strong', { text: t('correct_answer') + ': ' }),
          doc.createTextNode(A.pick(example.answer))]));
        var details = el('details', { class: 'hints' });
        details.appendChild(el('summary', { text: t('show_solution') }));
        var steps = el('ol', { class: 'steps' });
        (I.pick(example.solution) || []).forEach(function (step) { steps.appendChild(el('li', { text: step })); });
        details.appendChild(steps);
        card.appendChild(details);
        root.appendChild(card);
      });
    }

    var practice = el('button', { class: 'btn primary', text: t('study_practice') });
    practice.addEventListener('click', function () { go('#/practice/' + topic); });
    root.appendChild(practice);
    return root;
  };

  /** Статистика. */
  SCREENS['#/stats'] = function () {
    var totals = AN.totals(S.progress);
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('nav_stats') }));

    var cards = el('div', { class: 'grid-4' });
    cards.appendChild(h('<div class="card stat"><div class="stat-value">' + totals.tests + '</div><div class="muted">' + esc(t('stat_tests')) + '</div></div>'));
    cards.appendChild(h('<div class="card stat"><div class="stat-value">' + totals.tasks + '</div><div class="muted">' + esc(t('stat_tasks')) + '</div></div>'));
    cards.appendChild(h('<div class="card stat"><div class="stat-value">' + Math.round(totals.accuracy * 100) + '%</div><div class="muted">' + esc(t('stat_accuracy')) + '</div></div>'));
    cards.appendChild(h('<div class="card stat"><div class="stat-value">' + totals.minutes + '</div><div class="muted">' + esc(t('stat_minutes')) + '</div></div>'));
    root.appendChild(cards);

    var topicStats = AN.topicStats(S.progress);
    var topicItems = C.order.filter(function (topic) { return topicStats[topic]; }).map(function (topic) {
      return {
        label: C.topicTitle(topic), value: Math.round(topicStats[topic].rate * 100),
        text: Math.round(topicStats[topic].rate * 100) + '% · ' + topicStats[topic].total,
        color: topicStats[topic].rate < 0.5 ? '#e0555a' : (topicStats[topic].rate < 0.8 ? '#e0a84a' : '#4aa96c'),
        action: function () { go('#/practice/' + topic); },
      };
    });
    var topicCard = el('div', { class: 'card' });
    topicCard.appendChild(el('h3', { text: t('by_topic') }));
    topicCard.appendChild(UI.bars(topicItems));
    root.appendChild(topicCard);

    var yearStats = AN.yearStats(S.progress);
    if (Object.keys(yearStats).length) {
      var yearCard = el('div', { class: 'card' });
      yearCard.appendChild(el('h3', { text: t('by_year') }));
      yearCard.appendChild(UI.bars(Object.keys(yearStats).sort().map(function (year) {
        return {
          label: year, value: Math.round(yearStats[year].rate * 100),
          text: Math.round(yearStats[year].rate * 100) + '% · ' + t('tests_short_fmt', yearStats[year].tests),
        };
      })));
      root.appendChild(yearCard);
    }

    var daily = S.progress.daily || {};
    var days = Object.keys(daily).sort().slice(-14);
    if (days.length) {
      var dailyCard = el('div', { class: 'card' });
      dailyCard.appendChild(el('h3', { text: t('daily_activity') }));
      dailyCard.appendChild(UI.bars(days.map(function (day) {
        return { label: day.slice(5), value: daily[day], text: String(daily[day]) };
      })));
      root.appendChild(dailyCard);
    }

    var attempts = (S.progress.attempts || []).slice(-10).reverse();
    if (attempts.length) {
      var listCard = el('div', { class: 'card' });
      listCard.appendChild(el('h3', { text: t('last_attempts') }));
      var list = el('div', { class: 'attempt-list' });
      attempts.forEach(function (attempt) {
        var summary = AN.attemptSummary(attempt);
        var row = el('div', { class: 'attempt-row clickable' });
        row.appendChild(el('div', { class: 'attempt-title', text: attempt.title }));
        row.appendChild(el('div', { class: 'muted small', text: U.formatDate(attempt.finishedAt, I.lang) + ' · ' + U.duration(attempt.seconds, I.lang) }));
        row.appendChild(el('div', { class: 'attempt-score', text: summary.correct + '/' + summary.total }));
        row.appendChild(el('div', { class: 'muted small', text: Math.round(summary.percent * 100) + '%' }));
        row.addEventListener('click', function () { go('#/result/' + attempt.id); });
        list.appendChild(row);
      });
      listCard.appendChild(list);
      root.appendChild(listCard);
    }

    var actions = el('div', { class: 'rowline wrap' });
    var exportBtn = el('button', { class: 'btn', text: t('export_report') });
    exportBtn.addEventListener('click', function () { exportReport(null); });
    var reset = el('button', { class: 'btn ghost', text: t('reset_progress') });
    reset.addEventListener('click', function () {
      UI.confirm(t('reset_confirm'), function () { S.resetProgress(); CT.toast(t('progress_reset')); UI.render(); });
    });
    actions.appendChild(exportBtn); actions.appendChild(reset);
    root.appendChild(actions);
    return root;
  };

  /** Сборник формул. */
  SCREENS['#/formulas'] = function () {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('nav_formulas') }));
    var search = el('input', { class: 'answer-input', type: 'search', placeholder: t('search_formula') });
    root.appendChild(search);
    var list = el('div', { class: 'formula-list' });
    var render = function (query) {
      clear(list);
      var needle = String(query || '').trim().toLowerCase();
      C.formulas.forEach(function (group) {
        var items = group.items.filter(function (item) {
          return UI.formulaMatches(item, needle, group);
        });
        if (!items.length) return;
        list.appendChild(UI.formulaGroupCard(group, { items: items }));
      });
      if (!list.firstChild) list.appendChild(el('p', { class: 'muted', text: t('nothing_found') }));
    };
    search.addEventListener('input', function () { render(search.value); });
    render('');
    root.appendChild(list);
    return root;
  };

  /** Инструменты (калькулятор, черновик, график, сетка заданий). */
  var TOOLS = {
    open: function (name, task) {
      if (name === 'calculator') TOOLS.calculator();
      else if (name === 'sheet') TOOLS.sheet(task);
      else if (name === 'scratch') TOOLS.scratchpad(task);
      else if (name === 'graph') TOOLS.graph(task);
    },

    calculator: function () {
      var wrap = el('div', { class: 'calc' });
      var display = el('input', { class: 'answer-input calc-display', type: 'text', placeholder: '2*(3+4)+√9', inputmode: 'text' });
      var result = el('div', { class: 'calc-result' });
      var keys = el('div', { class: 'calc-keys' });
      var evaluate = function () {
        var value = M.eval(display.value);
        if (value === null) { result.className = 'calc-result bad'; result.textContent = t('calc_error'); return; }
        result.className = 'calc-result';
        result.textContent = '= ' + (typeof value === 'number' ? String(value).replace('.', I.lang === 'ru' ? ',' : '.') : value);
      };
      display.addEventListener('input', evaluate);
      display.addEventListener('keydown', function (event) { if (event.key === 'Enter') evaluate(); });
      var rows = [
        ['7', '8', '9', '⌫'],
        ['4', '5', '6', '÷'],
        ['1', '2', '3', '×'],
        ['0', ',', '−', '+'],
        ['(', ')', '^', '√('],
        ['sin(', 'cos(', 'π', '='],
      ];
      var insert = function (text) {
        var start = display.selectionStart || display.value.length;
        var value = display.value;
        var map = { '⌫': null, '÷': '/', '×': '*', '−': '-', ',': I.lang === 'ru' ? ',' : '.' };
        if (text === '⌫') {
          display.value = value.slice(0, Math.max(0, start - 1)) + value.slice(start);
        } else if (text === '=') {
          evaluate(); return;
        } else {
          var piece = map[text] !== undefined ? map[text] : text;
          display.value = value.slice(0, start) + piece + value.slice(start);
          display.selectionStart = display.selectionEnd = start + piece.length;
        }
        evaluate();
      };
      rows.forEach(function (row) {
        var line = el('div', { class: 'calc-row' });
        row.forEach(function (key) {
          var btn = el('button', { class: 'calc-key' + (key === '=' ? ' primary' : ''), text: key });
          btn.addEventListener('click', function () { insert(key); });
          line.appendChild(btn);
        });
        keys.appendChild(line);
      });
      wrap.appendChild(display);
      wrap.appendChild(result);
      wrap.appendChild(keys);
      wrap.appendChild(el('p', { class: 'muted small', text: t('calc_help') }));
      UI.modal(t('tool_calculator'), wrap);
      display.focus();
      evaluate();
    },

    sheet: function (task, query, options) {
      options = options || {};
      var wrap = el('div', { class: 'formula-list in-modal' });
      var search = el('input', { class: 'answer-input', type: 'search', placeholder: t('search_formula') });
      wrap.appendChild(search);
      var holder = el('div', {});
      wrap.appendChild(holder);
      var render = function (query) {
        clear(holder);
        var needle = String(query || '').trim().toLowerCase();
        C.formulas.forEach(function (group) {
          var items = group.items.filter(function (item) {
            return UI.formulaMatches(item, needle, group);
          });
          if (!items.length) return;
          holder.appendChild(UI.formulaGroupCard(group, { items: items }));
        });
      };
      search.addEventListener('input', function () { render(search.value); });
      search.value = query || '';
      render(search.value);
      UI.modal(t('tool_sheet'), wrap, { tall: true, keepHistory: !!options.keepHistory,
        language: true, refresh: function () { TOOLS.sheet(task, search.value, { keepHistory: true }); } });
    },

    scratchpad: function (task) {
      var wrap = el('div', {});
      var area = el('textarea', { class: 'scratch', rows: 12, placeholder: t('scratch_placeholder') });
      area.value = (S.progress.scratch && task && S.progress.scratch[task.id]) || '';
      var save = function () {
        S.progress.scratch = S.progress.scratch || {};
        S.progress.scratch[task && task.id || '_'] = area.value;
        S.saveProgress();
      };
      area.addEventListener('input', save);
      wrap.appendChild(area);
      var row = el('div', { class: 'rowline wrap' });
      var copy = el('button', { class: 'btn', text: t('copy') });
      copy.addEventListener('click', function () {
        try {
          area.select();
          doc.execCommand('copy');
          CT.toast(t('copied'));
        } catch (error) { CT.toast(t('copy_failed')); }
      });
      var clearBtn = el('button', { class: 'btn ghost', text: t('clear') });
      clearBtn.addEventListener('click', function () { area.value = ''; save(); });
      var insert = el('button', { class: 'btn ghost', text: t('insert_symbols') });
      insert.addEventListener('click', function () {
        ['√', 'π', '²', '³', '·', '−', '≤', '≥', '∠', '°'].forEach(function (symbol) {
          var btn = el('button', { class: 'btn small', text: symbol });
          btn.addEventListener('click', function () {
            var start = area.selectionStart || area.value.length;
            area.value = area.value.slice(0, start) + symbol + area.value.slice(start);
            area.selectionStart = area.selectionEnd = start + symbol.length;
            save();
            area.focus();
          });
          row.appendChild(btn);
        });
        insert.remove();
      });
      row.appendChild(copy); row.appendChild(clearBtn); row.appendChild(insert);
      wrap.appendChild(row);
      UI.modal(t('tool_scratch'), wrap, { tall: true });
      area.focus();
    },

    graph: function (task) {
      var wrap = el('div', {});
      var input = el('input', { class: 'answer-input', type: 'text', placeholder: 'x^2 - 3x + 2' });
      var canvas = el('canvas', { class: 'plot', width: 340, height: 260 });
      var info = el('div', { class: 'muted small' });
      var draw = function () {
        var ctx = canvas.getContext('2d');
        var width = canvas.width, height = canvas.height;
        var xmin = -10, xmax = 10, ymin = -10, ymax = 10;
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = getComputedStyle(doc.body).getPropertyValue('--surface-2') || '#fff';
        ctx.fillRect(0, 0, width, height);
        var toX = function (x) { return (x - xmin) / (xmax - xmin) * width; };
        var toY = function (y) { return height - (y - ymin) / (ymax - ymin) * height; };
        ctx.strokeStyle = getComputedStyle(doc.body).getPropertyValue('--border') || '#ccc';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, toY(0)); ctx.lineTo(width, toY(0));
        ctx.moveTo(toX(0), 0); ctx.lineTo(toX(0), height);
        ctx.stroke();
        var points = M.sample(input.value, xmin, xmax, 400);
        if (!points.length) { info.textContent = t('calc_error'); return; }
        ctx.strokeStyle = '#3b6fd4';
        ctx.lineWidth = 2;
        ctx.beginPath();
        var started = false;
        points.forEach(function (point) {
          if (!point) { started = false; return; }
          var px = toX(point.x), py = toY(point.y);
          if (!started) { ctx.moveTo(px, py); started = true; } else ctx.lineTo(px, py);
        });
        ctx.stroke();
        info.textContent = t('graph_hint');
      };
      input.addEventListener('input', draw);
      input.addEventListener('keydown', function (event) { if (event.key === 'Enter') draw(); });
      wrap.appendChild(el('p', { class: 'muted small', text: t('graph_help') }));
      wrap.appendChild(input);
      wrap.appendChild(canvas);
      wrap.appendChild(info);
      var symbols = el('div', { class: 'rowline wrap' });
      ['x^2', 'sqrt(x)', 'abs(x)', 'sin(x)', 'cos(x)', 'tan(x)', 'ln(x)'].forEach(function (piece) {
        var btn = el('button', { class: 'btn small', text: piece });
        btn.addEventListener('click', function () {
          input.value = input.value ? input.value + ' + ' + piece : piece;
          draw();
        });
        symbols.appendChild(btn);
      });
      wrap.appendChild(symbols);
      UI.modal(t('tool_graph'), wrap, { tall: true });
      draw();
    },

    /** Сетка заданий: переход к любому номеру, отметки и статусы. */
    taskGrid: function () {
      var run = S.session;
      if (!run) return;
      var wrap = el('div', {});
      wrap.appendChild(el('p', { class: 'muted small', text: t('task_grid_help') }));
      var grid = el('div', { class: 'task-grid' });
      run.order.forEach(function (id, index) {
        var task = C.taskById(id);
        var answered = String(run.answers[id] === undefined ? '' : run.answers[id]).trim() !== '';
        var state = answered ? (run.mode === 'exam' ? 'answered' : (run.checked[id] ? 'good' : 'bad')) : '';
        var btn = el('button', { class: 'grid-cell ' + state + (index === run.index ? ' current' : '') +
          (run.marked.indexOf(id) >= 0 ? ' marked' : ''), text: String(index + 1) });
        btn.addEventListener('click', function () { RUN.jump(index); UI.closeModal(); UI.render(); });
        if (!task) btn.disabled = true;
        grid.appendChild(btn);
      });
      wrap.appendChild(grid);
      var row = el('div', { class: 'rowline' });
      var finish = el('button', { class: 'btn primary', text: t('finish_test') });
      finish.addEventListener('click', function () {
        UI.closeModal();
        UI.confirm(t('finish_confirm'), function () {
          var attempt = RUN.finish();
          go('#/result/' + (attempt ? attempt.id : ''));
        }, t('finish_test'));
      });
      row.appendChild(finish);
      wrap.appendChild(row);
      UI.modal(t('task_grid'), wrap, { wide: true });
    },
  };
  CT.tools = TOOLS;

  /** Экспорт отчёта в самостоятельный HTML-файл. */
  function exportReport(attempt) {
    var totals = AN.totals(S.progress);
    var stats = AN.topicStats(S.progress);
    var rows = C.order.filter(function (topic) { return stats[topic]; }).map(function (topic) {
      return '<tr><td>' + esc(C.topicTitle(topic)) + '</td><td>' + stats[topic].correct + ' / ' + stats[topic].total +
        '</td><td>' + Math.round(stats[topic].rate * 100) + '%</td></tr>';
    }).join('');
    var attempts = (S.progress.attempts || []).map(function (item) {
      var summary = AN.attemptSummary(item);
      return '<tr><td>' + esc(item.title) + '</td><td>' + esc(U.formatDate(item.finishedAt, I.lang)) +
        '</td><td>' + summary.correct + ' / ' + summary.total + '</td><td>' + U.duration(item.seconds, I.lang) + '</td></tr>';
    }).join('');
    var mistakes = attempt ? RUN.wrongTasks(attempt).map(function (task) {
      return '<li><b>' + esc(I.pick(task.text)) + '</b><br>' + esc(I.pick(task.solution) || []) + '</li>';
    }).join('') : '';
    var html = '<!DOCTYPE html><html lang="' + I.lang + '"><head><meta charset="utf-8">' +
      '<title>' + esc(t('report_title')) + '</title><style>' +
      'body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:32px;color:#1c2330}' +
      'h1{font-size:22px}h2{font-size:17px;margin-top:26px}table{border-collapse:collapse;width:100%;margin-top:8px}' +
      'th,td{border:1px solid #ccd3de;padding:6px 8px;text-align:left;font-size:14px}' +
      'th{background:#eef2f8}.muted{color:#5b6472}.total{font-size:15px}</style></head><body>' +
      '<h1>' + esc(t('report_title')) + '</h1>' +
      '<p class="muted">' + esc(t('app_name')) + ' · ' + esc(U.formatDate(new Date().toISOString(), I.lang)) + '</p>' +
      '<p class="total"><b>' + esc(t('stat_tests')) + ':</b> ' + totals.tests + ' · <b>' + esc(t('stat_tasks')) +
      ':</b> ' + totals.tasks + ' · <b>' + esc(t('stat_accuracy')) + ':</b> ' + Math.round(totals.accuracy * 100) + '% · <b>' +
      esc(t('stat_time')) + ':</b> ' + totals.minutes + ' ' + esc(t('minutes_short')) + '</p>' +
      (rows ? '<h2>' + esc(t('by_topic')) + '</h2><table><tr><th>' + esc(t('topic')) + '</th><th>' + esc(t('correct_col')) +
        '</th><th>' + esc(t('percent_col')) + '</th></tr>' + rows + '</table>' : '') +
      (attempts ? '<h2>' + esc(t('last_attempts')) + '</h2><table><tr><th>' + esc(t('variant_col')) + '</th><th>' +
        esc(t('date_col')) + '</th><th>' + esc(t('correct_col')) + '</th><th>' + esc(t('time_col')) + '</th></tr>' +
        attempts + '</table>' : '') +
      (mistakes ? '<h2>' + esc(t('mistakes_title')) + '</h2><ul>' + mistakes + '</ul>' : '') +
      '<p class="muted">' + esc(t('developer')) + ': ' + esc(t('developer_name')) + ' · ziv@csl.by · +3753371412</p>' +
      '</body></html>';
    B.saveReport('progress', html).then(function (result) {
      CT.toast(result && result.path ? t('report_saved_fmt', result.path) : t('report_saved'));
    }).catch(function () { CT.toast(t('report_failed')); });
  }

  /* ------------------------------------------------------------------ *
   * 5. Настройки и «О программе»
   * ------------------------------------------------------------------ */
  SCREENS['#/settings'] = function () {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('nav_settings') }));

    var languageCard = el('div', { class: 'card' });
    languageCard.appendChild(el('h3', { text: t('language') }));
    var row = el('div', { class: 'rowline wrap' });
    [['ru', 'Русский'], ['en', 'English']].forEach(function (pair) {
      var btn = el('button', { class: 'btn' + (S.settings.lang === pair[0] ? ' primary' : ''), text: pair[1] });
      btn.addEventListener('click', function () {
        UI.changeLanguage(pair[0]);
      });
      row.appendChild(btn);
    });
    languageCard.appendChild(row);
    languageCard.appendChild(el('p', { class: 'muted small', text: t('language_hint') }));
    root.appendChild(languageCard);

    var examCard = el('div', { class: 'card' });
    examCard.appendChild(el('h3', { text: t('exam_settings') }));
    var minutes = el('input', { class: 'answer-input', type: 'number', min: 10, max: 300, value: S.settings.examMinutes });
    minutes.addEventListener('change', function () {
      S.settings.examMinutes = U.clamp(parseInt(minutes.value, 10) || 180, 10, 300);
      S.saveSettings(true);
    });
    examCard.appendChild(h('<label class="field"><span>' + esc(t('exam_minutes')) + '</span></label>'));
    examCard.appendChild(minutes);
    var goal = el('input', { class: 'answer-input', type: 'number', min: 5, max: 200, value: S.settings.dailyGoal });
    goal.addEventListener('change', function () {
      S.settings.dailyGoal = U.clamp(parseInt(goal.value, 10) || 20, 5, 200);
      S.saveSettings(true);
    });
    examCard.appendChild(h('<label class="field"><span>' + esc(t('daily_goal')) + '</span></label>'));
    examCard.appendChild(goal);
    root.appendChild(examCard);

    var lookCard = el('div', { class: 'card' });
    lookCard.appendChild(el('h3', { text: t('theme') }));
    var themeRow = el('div', { class: 'rowline wrap' });
    [['system', t('theme_system')], ['light', t('theme_light')], ['dark', t('theme_dark')]].forEach(function (pair) {
      var btn = el('button', { class: 'btn' + (S.settings.theme === pair[0] ? ' primary' : ''), text: pair[1] });
      btn.addEventListener('click', function () {
        S.settings.theme = pair[0];
        S.saveSettings(true);
        UI.applyAppearance(); UI.render();
      });
      themeRow.appendChild(btn);
    });
    lookCard.appendChild(themeRow);
    lookCard.appendChild(el('h3', { text: t('font_size') }));
    var fontRow = el('div', { class: 'rowline wrap' });
    [['font_small', 0.9], ['font_normal', 1], ['font_large', 1.15]].forEach(function (pair) {
      var btn = el('button', { class: 'btn' + (S.settings.fontScale === pair[1] ? ' primary' : ''), text: t(pair[0]) });
      btn.addEventListener('click', function () {
        S.settings.fontScale = pair[1];
        S.saveSettings(true);
        UI.applyAppearance(); UI.render();
      });
      fontRow.appendChild(btn);
    });
    lookCard.appendChild(fontRow);
    root.appendChild(lookCard);

    var switches = [
      ['autoAdvance', t('auto_advance'), t('auto_advance_hint')],
      ['vibrate', t('vibration'), ''],
      ['keepScreenOn', t('keep_screen_on'), ''],
      ['autoUpdate', t('auto_update'), ''],
    ];
    var switchCard = el('div', { class: 'card' });
    switchCard.appendChild(el('h3', { text: t('interface_settings') }));
    switches.forEach(function (entry) {
      var label = el('label', { class: 'switch' });
      var input = el('input', { type: 'checkbox' });
      input.checked = !!S.settings[entry[0]];
      input.addEventListener('change', function () {
        S.settings[entry[0]] = input.checked;
        S.saveSettings(true);
      });
      label.appendChild(input);
      label.appendChild(el('span', { text: entry[1] }));
      switchCard.appendChild(label);
      if (entry[2]) switchCard.appendChild(el('p', { class: 'muted small', text: entry[2] }));
    });
    root.appendChild(switchCard);

    var dataCard = el('div', { class: 'card' });
    dataCard.appendChild(el('h3', { text: t('data_settings') }));
    dataCard.appendChild(el('p', { class: 'muted small', text: t('data_hint') }));
    var dataRow = el('div', { class: 'rowline wrap' });
    var openData = el('button', { class: 'btn ghost', text: t('open_data_folder') });
    openData.addEventListener('click', function () {
      B.openFolder('data').then(function () { CT.toast(t('opened_folder')); })
        .catch(function () { CT.toast(t('open_folder_failed')); });
    });
    var exportBtn = el('button', { class: 'btn ghost', text: t('export_report') });
    exportBtn.addEventListener('click', function () { exportReport(null); });
    dataRow.appendChild(openData); dataRow.appendChild(exportBtn);
    dataCard.appendChild(dataRow);
    root.appendChild(dataCard);

    var about = el('div', { class: 'card' });
    var update = el('button', { class: 'btn', text: t('check_updates') });
    var updateInfo = el('p', { class: 'muted small' });
    update.addEventListener('click', function () {
      update.disabled = true;
      updateInfo.textContent = t('checking_updates');
      B.checkUpdates(S.settings.baseUrl, C.meta.contentVersion).then(function (result) {
        update.disabled = false;
        if (result.status === 'uptodate') updateInfo.textContent = t('update_uptodate');
        else if (result.status === 'updated' || result.status === 'ok') updateInfo.textContent = t('update_success_fmt', result.version);
        else updateInfo.textContent = t('update_failed');
        var message = updateInfo.textContent;
        if (result.status === 'updated' || result.status === 'ok') {
          // Show the new years immediately, not only after an app restart.
          return C.load().then(function () { UI.render(); CT.toast(message); });
        }
        CT.toast(message);
        return null;
      }).catch(function () {
        update.disabled = false;
        updateInfo.textContent = t('update_failed');
        CT.toast(t('update_failed'));
      });
    });
    about.appendChild(el('h3', { text: t('updates') }));
    about.appendChild(update);
    about.appendChild(updateInfo);
    about.appendChild(el('p', { class: 'muted small', text: t('content_version_fmt', C.meta.contentVersion || '—') }));
    root.appendChild(about);
    return root;
  };

  SCREENS['#/about'] = function () {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('about_title') }));
    var card = el('div', { class: 'card' });
    card.appendChild(el('p', { text: t('about_text') }));
    card.appendChild(el('h3', { text: t('developer') }));
    var contacts = el('div', { class: 'contacts' });
    var name = el('p', { class: 'big', text: t('developer_name') });
    contacts.appendChild(name);
    var email = el('a', { class: 'btn', href: 'mailto:ziv@csl.by?subject=' + encodeURIComponent(t('feedback_subject')), text: 'ziv@csl.by' });
    var phone = el('a', { class: 'btn', href: 'tel:+3753371412', text: '+375 33 714 12' });
    var whatsapp = el('a', { class: 'btn ghost', href: 'https://wa.me/3753371412', text: 'WhatsApp' });
    var repo = el('a', { class: 'btn ghost', href: C.meta.repo || 'https://github.com/zigorminsk-debug/mathematics', text: t('source_code') });
    [email, phone, whatsapp, repo].forEach(function (link) {
      link.addEventListener('click', function (event) {
        event.preventDefault();
        B.openExternal(link.getAttribute('href'));
      });
      contacts.appendChild(link);
    });
    contacts.appendChild(el('p', { class: 'muted small', text: t('contacts_hint') }));
    card.appendChild(contacts);
    card.appendChild(el('p', { class: 'muted small', text: t('disclaimer') }));
    card.appendChild(el('p', { class: 'muted small', text: t('version_fmt', B.info.version || '—', C.meta.contentVersion || '—') }));
    root.appendChild(card);
    return root;
  };

  SCREENS['#/tools'] = function () {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('nav_tools') }));
    root.appendChild(el('p', { class: 'muted', text: t('tools_intro') }));
    var grid = el('div', { class: 'grid-4' });
    [['calculator', t('tool_calculator'), '🧮'], ['sheet', t('tool_sheet'), '📐'],
     ['scratch', t('tool_scratch'), '📝'], ['graph', t('tool_graph'), '📈']].forEach(function (entry) {
      var btn = el('button', { class: 'btn big tool-btn' });
      btn.appendChild(el('span', { class: 'tool-icon', text: entry[2] }));
      btn.appendChild(el('span', { text: entry[1] }));
      btn.addEventListener('click', function () { TOOLS.open(entry[0], RUN.current()); });
      grid.appendChild(btn);
    });
    root.appendChild(grid);
    return root;
  };

  /* ------------------------------------------------------------------ *
   * 6. Роутер и запуск
   * ------------------------------------------------------------------ */
  var NAV = [
    ['#/home', 'nav_home', '🏠'],
    ['#/tests', 'nav_tests', '📚'],
    ['#/practice', 'nav_practice', '🔁'],
    ['#/study', 'nav_study', '📖'],
    ['#/stats', 'nav_stats', '📊'],
    ['#/formulas', 'nav_formulas', '📐'],
    ['#/tools', 'nav_tools', '🧰'],
    ['#/about', 'nav_about', 'ℹ️'],
  ];

  UI.renderNav = function () {
    var nav = $('#mainnav');
    if (!nav) return;
    clear(nav);
    var current = parseHash().name;
    NAV.forEach(function (entry) {
      var link = el('a', { href: entry[0], class: 'nav-link' + (entry[0] === current ? ' active' : '') });
      link.appendChild(el('span', { class: 'nav-icon', text: entry[2] }));
      link.appendChild(el('span', { text: t(entry[1]) }));
      nav.appendChild(link);
    });
  };

  /** Разбор адреса: «#/mistakes/<id>» → {name:'#/mistakes', extra:'<id>'} */
  function parseHash() {
    var raw = String(global.location.hash || '#/home').replace(/^#\/?/, '');
    var parts = raw.split('/').filter(function (piece) { return piece !== ''; });
    if (!parts.length) return { name: '#/home', extra: null };
    var name = '#/' + parts[0];
    return { name: name, extra: parts.slice(1).join('/') || null };
  }

  UI.render = function () {
    var route = parseHash();
    var screen = SCREENS[route.name] || SCREENS['#/home'];
    var view = $('#view');
    clear(view);
    try {
      view.appendChild(screen(route.extra));
    } catch (error) {
      if (global.console) global.console.error(error);
      view.appendChild(h('<div class="card"><p class="banner bad">' + esc(t('error_generic')) + '</p>' +
        '<pre class="small">' + esc(String(error && error.message || error)) + '</pre></div>'));
    }
    view.scrollTop = 0;
    UI.renderNav();
    UI.chrome();
  };
  CT.render = UI.render;

  /** Системная кнопка «назад» на Android: «exit» — выйти из приложения. */
  CT.onAndroidBack = function () {
    if ($('#modal').classList.contains('open')) { UI.backModal(); return null; }
    var route = parseHash();
    if (route.name === '#/home') return 'exit';
    if (route.name === '#/study' && route.extra) {
      go(S.session && !S.session.finished ? '#/run' : '#/study');
      return null;
    }
    var parent = { '#/run': '#/tests', '#/result': '#/home', '#/mistakes': '#/home',
      '#/study': '#/home', '#/settings': '#/home', '#/about': '#/home' }[route.name];
    go(parent || '#/home');
    return null;
  };

  var booted = false;

  CT.boot = function () {
    if (booted) return Promise.resolve(true);
    booted = true;
    var brand = $('#brand');
    if (brand) brand.addEventListener('click', function () { go('#/home'); });
    var settingsBtn = $('#btn-settings');
    if (settingsBtn) settingsBtn.addEventListener('click', function () { go('#/settings'); });
    I.setLang('ru');
    UI.bindChrome();
    return S.load().catch(function () { return S; }).then(function () {
      return C.load().catch(function (error) {
        if (global.console) global.console.error(error);
        return null;
      });
    }).then(function () {
      B.ready().then(function (info) {
        B.info = info || {};
        B.platform = B.info.platform || (B.native ? 'android' : 'windows');
        UI.render();
        // путь к папке с данными — виден в подвале и в окне «О программе»
        var folder = $('#app-folder');
        if (folder) folder.textContent = B.info.dataDir || '';
      });
      UI.chrome();
      UI.render();
      // Автообновление банка (настройка autoUpdate): без него новые варианты —
      // например 2026 года — сами на устройство не приходили, а кнопкой в
      // настройках пользовались не все. Ошибка сети просто пропускается.
      if (S.settings.autoUpdate) {
        B.checkUpdates(S.settings.baseUrl, C.meta.contentVersion).then(function (result) {
          var updated = result && (result.status === 'updated' || result.status === 'ok');
          if (updated && result.version && result.version !== C.meta.contentVersion) {
            return C.load().then(function () {
              // Do not replace a task/input while the student is answering it.
              if (parseHash().name !== '#/run') UI.render();
              CT.toast(t('update_success_fmt', result.version));
            });
          }
          return null;
        }).catch(function () { /* офлайн: работаем на встроенном банке */ });
      }
      // экран не гасим только во время теста — см. RUN.startVariant/startSet
      return true;
    });
  };

  global.addEventListener('hashchange', UI.render);
  doc.addEventListener('DOMContentLoaded', function () {
    CT.boot();
  });
  if (doc.readyState !== 'loading') CT.boot();
})(typeof globalThis !== 'undefined' ? globalThis : this);

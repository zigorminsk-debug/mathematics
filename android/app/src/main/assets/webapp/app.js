/* app.js — экраны приложения «Репетитор ЦТ: Русский язык».
 *
 * Один и тот же код работает в Android WebView и в окне Windows: слой
 * платформы скрыт в CT.bridge (core.js). Здесь только интерфейс: главная,
 * авторские варианты, экзамен с таймером, тренировка, разбор ошибок по
 * конкретному правилу с аналогичными упражнениями, изучение, «Правила»,
 * статистика, черновик и памятки, настройки и «О программе».
 *
 * Проверяемый русский материал (тексты, слова, предложения) никогда не
 * переводится: переключатель RU/EN меняет только интерфейс и пояснения.
 */
(function (global) {
  'use strict';

  var doc = global.document;
  var CT = global.CT;
  var U = CT.util, I = CT.i18n, B = CT.bridge, C = CT.content, A = CT.answer, AN = CT.analytics;
  var ACUTE = '\u0301';

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
  function ru(node) { node.setAttribute('lang', 'ru'); return node; }

  /* ------------------------------------------------------------------ *
   * 1. Локальное состояние и хранилище
   * ------------------------------------------------------------------ */
  var DEFAULT_SETTINGS = {
    lang: 'ru', theme: 'system', fontScale: 1, examMinutes: 120, dailyGoal: 20,
    autoAdvance: true, sound: true, vibrate: true, autoUpdate: true, baseUrl: '', keepScreenOn: true,
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
        self.settings = settings;
        var progress = data[1] || {};
        var empty = AN.empty();
        Object.keys(empty).forEach(function (key) { if (progress[key] === undefined) progress[key] = empty[key]; });
        self.progress = progress;
        self.session = data[2] || null;
        I.setLang(self.settings.lang);
        self.loaded = true;
        return self;
      });
    },

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

    resetProgress: function () {
      this.progress = AN.empty();
      this.session = null;
      this.saveProgress(true);
      this.saveSession(true);
    },

    recordTask: function (task, correct, seconds) {
      AN.record(this.progress, task, correct, seconds);
      this.saveProgress();
    },
  };

  /* ------------------------------------------------------------------ *
   * 2. Ход теста / test runner model
   * ------------------------------------------------------------------ */
  function newSession(kind, mode, title, ids, extra) {
    S.session = Object.assign({
      id: U.uid(), kind: kind, mode: mode, year: 0, title: title, order: ids,
      answers: {}, checked: {}, marked: [], index: 0,
      startedAt: new Date().toISOString(), seconds: 0, finished: false,
    }, extra || {});
    S.saveSession(true);
    return S.session;
  }

  var RUN = CT.runner = {
    startVariant: function (variant, mode) {
      return newSession('variant', mode, t('variant_title_fmt', variant.year),
        variant.tasks.map(function (task) { return task.id; }), { year: variant.year });
    },
    startPractice: function (topic) {
      var pool = C.tasksByTopic(topic).concat(C.analogByTopic(topic));
      if (!pool.length) pool = C.analogous.slice();
      return newSession('practice', 'train', C.topicTitle(topic), U.shuffle(pool).map(function (task) { return task.id; }),
        { topic: topic, endless: true });
    },
    /** Drill one concrete rule: its analogous exercises first, then bank tasks. */
    startRule: function (rule) {
      var analogs = U.shuffle(C.analogByRule(rule));
      var bank = U.shuffle(C.tasksByRule(rule).filter(function (task) { return task.kind === 'variant'; }));
      var ids = analogs.concat(bank).map(function (task) { return task.id; });
      return newSession('rule', 'train', t('rule_drill_fmt', C.ruleTitle(rule)), ids, { rule: rule });
    },
    startSet: function (tasks, title, mode) {
      return newSession('set', mode || 'train', title, tasks.map(function (task) { return task.id; }));
    },
    current: function () {
      var run = S.session;
      return run ? C.taskById(run.order[run.index]) || null : null;
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
    setAnswer: function (taskId, value) {
      var run = S.session;
      if (!run) return;
      run.answers[taskId] = value;
      S.saveSession();
    },
    checkCurrent: function () {
      var run = S.session, task = this.current();
      if (!run || !task) return null;
      var correct = A.check(run.answers[task.id], task);
      run.checked[task.id] = correct;
      S.recordTask(task, correct, 0);
      S.saveSession();
      return correct;
    },
    finish: function () {
      var run = S.session;
      if (!run || run.finished) return null;
      var results = run.order.map(function (id) {
        var task = C.taskById(id);
        if (!task) return null;
        var user = run.answers[id];
        var correct = run.mode === 'exam' ? A.check(user, task) : !!run.checked[id];
        return { taskId: id, part: task.part || 'T', topic: task.topic, rule: task.rule, correct: correct,
          user: user === undefined ? '' : user };
      }).filter(Boolean);
      var answered = results.filter(function (r) { return String(r.user).trim() !== ''; }).length;
      results.forEach(function (result) { if (String(result.user).trim() === '' && run.mode === 'exam') result.correct = false; });
      var attempt = {
        id: run.id, kind: run.kind, mode: run.mode, year: run.year, title: run.title,
        startedAt: run.startedAt, finishedAt: new Date().toISOString(),
        seconds: run.seconds || 0, answered: answered, results: results,
      };
      run.finished = true;
      var perTask = results.length ? (run.seconds || 0) / results.length : 0;
      results.forEach(function (result) {
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
    wrongResults: function (attempt) {
      return (attempt ? attempt.results : []).filter(function (r) { return !r.correct && C.taskById(r.taskId); });
    },
    wrongTasks: function (attempt) {
      return this.wrongResults(attempt).map(function (r) { return C.taskById(r.taskId); });
    },
    /** Analogous exercises for the concrete rules a learner got wrong. */
    analogousFor: function (results, limit) {
      var out = [], seen = {};
      results.forEach(function (result) {
        var task = C.taskById(result.taskId);
        C.rulesFor(task, result.user).forEach(function (rule) {
          var picked = 0;
          C.analogByRule(rule).forEach(function (candidate) {
            if (picked >= (limit || 2) || seen[candidate.id] || candidate.id === result.taskId) return;
            seen[candidate.id] = true;
            out.push(candidate);
            picked++;
          });
        });
      });
      return out;
    },
  };

  /* ------------------------------------------------------------------ *
   * 3. Общие куски интерфейса
   * ------------------------------------------------------------------ */
  var UI = {};
  var chromeBound = false;

  UI.bindChrome = function () {
    if (chromeBound) return;
    chromeBound = true;
    var brand = $('#brand');
    if (brand) brand.addEventListener('click', function () { go('#/home'); });
    var settings = $('#btn-settings');
    if (settings) settings.addEventListener('click', function () { go('#/settings'); });
    var language = $('#lang-toggle');
    if (language) language.addEventListener('click', function () { UI.changeLanguage(I.lang === 'ru' ? 'en' : 'ru'); });
  };

  /** Switch RU/EN without losing an entered analogous answer, its check state or a search. */
  UI.changeLanguage = function (lang) {
    var search = $('#view input[type="search"]');
    var query = search ? search.value : null;
    var analogues = $$('.analogous-item', $('#view')).map(function (item) {
      return { id: item.getAttribute('data-task-id'), value: item.getAttribute('data-value') || '',
        status: item.getAttribute('data-status') || '', solution: item.getAttribute('data-solution') === '1' };
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
      if (!saved || (!saved.value && !saved.status && !saved.solution)) return;
      var index = parseInt(item.getAttribute('data-index'), 10) || 1;
      item.parentNode.replaceChild(UI.analogousItem(C.taskById(saved.id), index, saved), item);
    });
    if ($('#modal').classList.contains('open') && modalRefresh) modalRefresh(true);
  };

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
      } catch (error) { /* system theme unavailable */ }
    }
  };

  UI.chrome = function () {
    var langBtn = $('#lang-toggle');
    langBtn.textContent = I.lang === 'ru' ? 'EN' : 'RU';
    langBtn.title = t('language');
    $('#brand-name').textContent = t('app_name');
    doc.title = t('app_name');
    UI.applyAppearance();
  };

  var toastTimer = null;
  CT.toast = function (message) {
    var box = $('#toast');
    if (!box) return;
    box.textContent = message;
    box.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { box.classList.remove('show'); }, 2600);
  };
  CT.app = { toast: function (message) { CT.toast(message); } };

  // Nested dialogs keep the real DOM nodes of the parent (input values, scroll,
  // focus) and restore them on one-level Back.
  var modalStack = [], modalFocus = null, modalRefresh = null;

  UI.modal = function (title, node, options) {
    options = options || {};
    var overlay = $('#modal');
    var sheet = $('.sheet', overlay);
    if (options.push && overlay.classList.contains('open')) {
      modalStack.push({ nodes: Array.prototype.slice.call(sheet.childNodes), className: sheet.className,
        scrollTop: sheet.scrollTop, focus: doc.activeElement, lang: I.lang, refresh: modalRefresh });
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
    var controls = $$('button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), a[href], [tabindex="0"]', $('.sheet'));
    if (!controls.length) return;
    var first = controls[0], last = controls[controls.length - 1];
    if (event.shiftKey && (doc.activeElement === first || !$('.sheet').contains(doc.activeElement))) {
      event.preventDefault(); last.focus();
    } else if (!event.shiftKey && (doc.activeElement === last || !$('.sheet').contains(doc.activeElement))) {
      event.preventDefault(); first.focus();
    }
  });

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

  UI.bars = function (items) {
    var wrap = el('div', { class: 'bars' });
    var max = Math.max.apply(null, items.map(function (item) { return item.value; }).concat([1]));
    items.forEach(function (item) {
      var row = el(item.action ? 'button' : 'div', { class: 'bar-row' + (item.action ? ' clickable' : ''),
        type: item.action ? 'button' : null });
      row.appendChild(el('span', { class: 'bar-label', text: item.label }));
      var track = el('span', { class: 'bar-track' });
      var fill = el('span', { class: 'bar-fill' });
      fill.style.width = Math.round(item.value / max * 100) + '%';
      if (item.color) fill.style.background = item.color;
      track.appendChild(fill);
      row.appendChild(track);
      row.appendChild(el('span', { class: 'bar-value', text: item.text || String(item.value) }));
      if (item.action) row.addEventListener('click', item.action);
      wrap.appendChild(row);
    });
    if (!items.length) wrap.appendChild(el('p', { class: 'muted', text: t('no_data_yet') }));
    return wrap;
  };

  UI.ring = function (percent, label) {
    var size = 132, radius = 56, circumference = 2 * Math.PI * radius;
    var value = U.clamp(percent, 0, 100);
    var svg = '<svg viewBox="0 0 ' + size + ' ' + size + '" class="ring" role="img" aria-label="' + Math.round(value) + '%">' +
      '<circle cx="' + size / 2 + '" cy="' + size / 2 + '" r="' + radius + '" class="ring-track"/>' +
      '<circle cx="' + size / 2 + '" cy="' + size / 2 + '" r="' + radius + '" class="ring-fill" ' +
      'stroke-dasharray="' + circumference + '" stroke-dashoffset="' + (circumference * (1 - value / 100)).toFixed(1) + '"/>' +
      '<text x="' + size / 2 + '" y="' + (size / 2 + 6) + '" text-anchor="middle" class="ring-text">' + Math.round(value) + '%</text></svg>';
    var wrap = el('div', { class: 'ring-wrap' });
    wrap.appendChild(h(svg));
    if (label) wrap.appendChild(el('div', { class: 'muted small', text: label }));
    return wrap;
  };

  function rateColor(rate) { return rate < 0.5 ? '#e0555a' : (rate < 0.8 ? '#e0a84a' : '#4aa96c'); }
  function badge(task) {
    if (task.kind === 'variant') return (task.part === 'A' ? 'А' : 'В') + task.n;
    return t('exercise_short');
  }

  /* ---------------------------------------------- task material + answer */
  /** Russian material (text, numbered items) is rendered as is, marked lang="ru". */
  UI.material = function (task, options) {
    options = options || {};
    var box = el('div', { class: 'task-material' });
    if (task.text) {
      var text = ru(el('div', { class: 'task-original' }));
      String(task.text).split('\n').forEach(function (line, index) {
        if (index) text.appendChild(el('br'));
        text.appendChild(doc.createTextNode(line));
      });
      box.appendChild(text);
    }
    var spec = task.check;
    var inline = spec.type === 'multi' || spec.type === 'single';
    if (task.items && !inline && !options.hideItems) {
      var list = ru(el('ol', { class: 'task-items' }));
      task.items.forEach(function (item, index) {
        list.appendChild(el('li', { 'data-n': spec.type === 'match' ? 'АБВГДЕ'.charAt(index) : String(index + 1) }, [item]));
      });
      if (spec.type === 'match') list.classList.add('lettered');
      box.appendChild(list);
    }
    return box;
  };

  function digitsValue(values, max, ordered) {
    var list = ordered ? values : values.slice().sort(function (a, b) { return a - b; });
    return list.join(max <= 9 ? '' : ' ');
  }

  /**
   * Answer control for every check type. onChange(value) fires with the raw
   * answer string; the stored value can be re-rendered after a language switch.
   */
  UI.answerControl = function (task, value, onChange, options) {
    options = options || {};
    var spec = task.check;
    var wrap = el('div', { class: 'answer-control answer-' + spec.type });
    var current = value === undefined || value === null ? '' : String(value);
    var emit = function (next) { current = next; if (onChange) onChange(next); };
    var options_ = task.items || (task.choices ? I.pick(task.choices) : []);

    if (spec.type === 'multi' || spec.type === 'single') {
      var selected = A.parseNumbers(current, spec.options) || [];
      var list = el('div', { class: 'options', role: 'group', 'aria-label': t('answer_label') });
      options_.forEach(function (text, index) {
        var n = index + 1;
        var btn = el('button', { class: 'option' + (selected.indexOf(n) >= 0 ? ' selected' : ''), type: 'button',
          'aria-pressed': selected.indexOf(n) >= 0 ? 'true' : 'false', 'data-index': String(n) });
        btn.appendChild(el('span', { class: 'letter', text: n + ')' }));
        var label = el('span', { class: 'option-value', text: text });
        if (task.items) ru(label);
        btn.appendChild(label);
        btn.addEventListener('click', function () {
          if (spec.type === 'single') selected = selected.indexOf(n) >= 0 ? [] : [n];
          else if (selected.indexOf(n) >= 0) selected.splice(selected.indexOf(n), 1);
          else selected.push(n);
          $$('.option', list).forEach(function (node) {
            var on = selected.indexOf(parseInt(node.getAttribute('data-index'), 10)) >= 0;
            node.classList.toggle('selected', on);
            node.setAttribute('aria-pressed', on ? 'true' : 'false');
          });
          emit(digitsValue(selected, spec.options, false));
        });
        list.appendChild(btn);
      });
      wrap.appendChild(list);
      if (spec.type === 'multi') wrap.appendChild(el('p', { class: 'muted small', text: t('multi_hint') }));
      return { node: wrap, value: function () { return current; } };
    }

    if (spec.type === 'numbers') {
      var ordered = spec.order === 'ordered';
      var chosen = A.parseNumbers(current, spec.max) || [];
      var input = el('input', { class: 'answer-input', type: 'text', inputmode: 'numeric', value: current,
        autocomplete: 'off', placeholder: t('numbers_placeholder'), 'aria-label': t('answer_label') });
      var chips = el('div', { class: 'chips', role: 'group', 'aria-label': t(ordered ? 'sequence_label' : 'numbers_label') });
      var paint = function () {
        $$('.chip', chips).forEach(function (chip) {
          var n = parseInt(chip.getAttribute('data-n'), 10);
          var at = chosen.indexOf(n);
          chip.classList.toggle('selected', at >= 0);
          chip.setAttribute('aria-pressed', at >= 0 ? 'true' : 'false');
          var order = $('.chip-order', chip);
          order.textContent = ordered && at >= 0 ? String(at + 1) : '';
        });
      };
      for (var n = 1; n <= spec.max; n++) {
        (function (number) {
          var chip = el('button', { class: 'chip', type: 'button', 'data-n': String(number), 'aria-pressed': 'false' },
            [el('span', { text: String(number) }), el('span', { class: 'chip-order', 'aria-hidden': 'true' })]);
          chip.addEventListener('click', function () {
            var at = chosen.indexOf(number);
            if (at >= 0) chosen.splice(at, 1); else chosen.push(number);
            input.value = digitsValue(chosen, spec.max, ordered);
            paint();
            emit(input.value);
          });
          chips.appendChild(chip);
        })(n);
      }
      input.addEventListener('input', function () {
        chosen = A.parseNumbers(input.value, spec.max) || [];
        paint();
        emit(input.value);
      });
      paint();
      wrap.appendChild(chips);
      var row = el('div', { class: 'answer-row' });
      row.appendChild(input);
      if (ordered) {
        var reset = el('button', { class: 'btn ghost', type: 'button', text: t('reset_order') });
        reset.addEventListener('click', function () { chosen = []; input.value = ''; paint(); emit(''); });
        row.appendChild(reset);
      }
      wrap.appendChild(row);
      wrap.appendChild(el('p', { class: 'muted small', text: t(ordered ? 'sequence_hint' : 'numbers_hint') }));
      return { node: wrap, value: function () { return current; } };
    }

    if (spec.type === 'stress') {
      var word = spec.word;
      var letters = ru(el('div', { class: 'stress-letters', role: 'group', 'aria-label': t('stress_label') }));
      var stressInput = el('input', { class: 'answer-input', type: 'text', value: current, lang: 'ru', autocomplete: 'off',
        autocapitalize: 'none', autocorrect: 'off', spellcheck: 'false', placeholder: t('stress_placeholder'),
        'aria-label': t('answer_label') });
      var mark = function () {
        var at = A.parseStress(stressInput.value, word);
        $$('.stress-letter', letters).forEach(function (node) {
          var on = parseInt(node.getAttribute('data-i'), 10) === at;
          node.classList.toggle('selected', on);
          node.setAttribute('aria-pressed', on ? 'true' : 'false');
        });
      };
      word.split('').forEach(function (ch, index) {
        var vowel = A.VOWELS.indexOf(ch) >= 0;
        var node = el(vowel ? 'button' : 'span', { class: 'stress-letter' + (vowel ? ' vowel' : ''), type: vowel ? 'button' : null,
          'data-i': String(index), 'aria-pressed': vowel ? 'false' : null, text: ch });
        if (vowel) {
          node.setAttribute('aria-label', t('stress_vowel_fmt', ch, index + 1));
          node.addEventListener('click', function () {
            stressInput.value = word.slice(0, index + 1) + ACUTE + word.slice(index + 1);
            mark();
            emit(stressInput.value);
          });
        }
        letters.appendChild(node);
      });
      stressInput.addEventListener('input', function () { mark(); emit(stressInput.value); });
      wrap.appendChild(letters);
      wrap.appendChild(stressInput);
      wrap.appendChild(el('p', { class: 'muted small', text: t('stress_hint') }));
      mark();
      return { node: wrap, value: function () { return current; } };
    }

    if (spec.type === 'match') {
      var pairs = A.parseMatch(current, spec.labels, spec.right) || {};
      var partial = {};
      String(current).toUpperCase().replace(/([А-ЯЁ])([0-9]{1,2})/g, function (_, label, digits) { partial[label] = digits; return ''; });
      var right = ru(el('ol', { class: 'match-choices' }));
      (I.pick(task.choices) || []).forEach(function (choice) { right.appendChild(el('li', { text: choice })); });
      if (task.choices) right.removeAttribute('lang');
      wrap.appendChild(right);
      var grid = el('div', { class: 'match-grid' });
      var selects = {};
      spec.labels.forEach(function (label, index) {
        var field = el('label', { class: 'match-row' });
        field.appendChild(ru(el('span', { class: 'match-left', text: label + ') ' + (task.items || [])[index] })));
        var select = el('select', { class: 'match-select', 'aria-label': t('match_select_fmt', label) });
        select.appendChild(el('option', { value: '', text: '—' }));
        for (var k = 1; k <= spec.right; k++) select.appendChild(el('option', { value: String(k), text: String(k) }));
        select.value = pairs[label] ? String(pairs[label]) : (partial[label] || '');
        select.addEventListener('change', function () {
          emit(spec.labels.map(function (key) { return selects[key].value ? key + selects[key].value : ''; }).join(''));
        });
        selects[label] = select;
        field.appendChild(select);
        grid.appendChild(field);
      });
      wrap.appendChild(grid);
      wrap.appendChild(el('p', { class: 'muted small', text: t('match_hint') }));
      return { node: wrap, value: function () { return current; } };
    }

    // word / integer: a plain field. Autocorrect and auto-capitalisation are off:
    // the platform must never "fix" the spelling that is being checked.
    var field = el('input', { class: 'answer-input', type: 'text', value: current, autocomplete: 'off', autocapitalize: 'none',
      autocorrect: 'off', spellcheck: 'false', lang: 'ru', inputmode: spec.type === 'integer' ? 'numeric' : null,
      placeholder: t(spec.type === 'integer' ? 'integer_placeholder' : 'word_placeholder'), 'aria-label': t('answer_label') });
    field.addEventListener('input', function () { emit(field.value); });
    if (options.onEnter) field.addEventListener('keydown', function (event) { if (event.key === 'Enter') options.onEnter(); });
    wrap.appendChild(field);
    wrap.appendChild(el('p', { class: 'muted small', text: t(spec.type === 'integer' ? 'integer_hint' : 'word_hint') }));
    return { node: wrap, value: function () { return current; } };
  };

  UI.taskCard = function (task, run, options) {
    options = options || {};
    var card = el('div', { class: 'card task-card', 'data-task-id': task.id });
    var head = el('div', { class: 'task-head' });
    head.appendChild(el('span', { class: 'badge', text: badge(task) }));
    head.appendChild(el('span', { class: 'muted small', text: C.topicTitle(task.topic) }));
    if (task.level) head.appendChild(el('span', { class: 'muted small', text: t('level_fmt', ['I', 'II', 'III', 'IV', 'V'][task.level - 1]) }));
    if (run && run.marked.indexOf(task.id) >= 0) head.appendChild(el('span', { class: 'badge warn', text: t('marked') }));
    card.appendChild(head);
    card.appendChild(el('div', { class: 'task-text', text: I.pick(task.instruction) }));
    card.appendChild(UI.material(task));
    var stored = run ? run.answers[task.id] : undefined;
    var control = UI.answerControl(task, stored, function (value) { if (run) RUN.setAnswer(task.id, value); },
      { onEnter: options.onCheck });
    card.appendChild(control.node);
    if (options.onCheck) {
      var row = el('div', { class: 'answer-row' });
      var checkBtn = el('button', { class: 'btn primary', type: 'button', text: t('check_answer') });
      checkBtn.addEventListener('click', function () { if (run) RUN.setAnswer(task.id, control.value()); options.onCheck(); });
      row.appendChild(checkBtn);
      card.appendChild(row);
    }
    return card;
  };

  /* ------------------------------------------------------------- diagrams */
  var SVG_FIELDS = { line: ['x1', 'y1', 'x2', 'y2'], circle: ['cx', 'cy', 'r'], ellipse: ['cx', 'cy', 'rx', 'ry'],
    rect: ['x', 'y', 'width', 'height'], polyline: ['points'], polygon: ['points'], text: ['x', 'y', 'text', 'anchor'] };
  var SVG_ROLES = ['axis', 'grid', 'primary', 'secondary', 'helper', 'region', 'point', 'openpoint', 'text', 'accent'];
  function bilingual(value) {
    return value && ['ru', 'en'].every(function (lang) { return typeof value[lang] === 'string' && value[lang].trim(); });
  }
  function cellText(value) { return typeof value === 'string' ? value : I.pick(value); }

  /** Build an SVG only from finite coordinates and a fixed allowlist; one bad item rejects all. */
  UI.diagramSvg = function (figure) {
    var namespace = 'http://www.w3.org/2000/svg';
    if (!figure || figure.kind !== 'svg' || figure.width !== 420 || figure.height !== 280 || !Array.isArray(figure.drawing) ||
        !figure.drawing.length || figure.drawing.length > 250) return null;
    var numeric = function (key, value) {
      var bound = key.charAt(0) === 'y' || ['cy', 'ry', 'height'].indexOf(key) >= 0 ? 280 : 420;
      return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= bound &&
        (['r', 'rx', 'ry', 'width', 'height'].indexOf(key) < 0 || value > 0);
    };
    if (!bilingual(figure.title) || !bilingual(figure.caption)) return null;
    var valid = figure.drawing.every(function (item) {
      var allowed = item && typeof item.kind === 'string' && Object.prototype.hasOwnProperty.call(SVG_FIELDS, item.kind) ? SVG_FIELDS[item.kind] : null;
      if (!allowed || SVG_ROLES.indexOf(item.role) < 0 || typeof item.filled !== 'boolean' ||
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
      SVG_FIELDS[item.kind].forEach(function (key) {
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
      if (!item || SVG_ROLES.indexOf(item.role) < 0 || !bilingual(item.text)) return;
      var label = el('span', { class: 'diagram-legend-item' });
      label.appendChild(el('span', { class: 'diagram-key diagram-' + item.role, 'aria-hidden': 'true' }));
      label.appendChild(el('span', { text: I.pick(item.text) }));
      legend.appendChild(label);
    });
    return legend;
  };

  /** Large contrast tables are semantic HTML, never tiny SVG text. */
  UI.diagramTable = function (figure) {
    if (!figure || figure.kind !== 'table' || !Array.isArray(figure.columns) || !Array.isArray(figure.rows) ||
        !figure.columns.every(bilingual) || !figure.rows.every(function (row) {
          return Array.isArray(row) && row.length === figure.columns.length && row.every(function (cell) {
            return (typeof cell === 'string' && cell.trim()) || bilingual(cell);
          });
        })) return null;
    var scroller = el('div', { class: 'table-scroll', tabindex: '0', role: 'region', 'aria-label': I.pick(figure.title) });
    var tableNode = el('table', { class: 'rule-table', 'data-figure': figure.id });
    tableNode.appendChild(el('caption', { text: I.pick(figure.caption) }));
    var thead = el('thead');
    var headRow = el('tr');
    figure.columns.forEach(function (column) { headRow.appendChild(el('th', { scope: 'col', text: I.pick(column) })); });
    thead.appendChild(headRow);
    tableNode.appendChild(thead);
    var tbody = el('tbody');
    figure.rows.forEach(function (row) {
      var tr = el('tr');
      row.forEach(function (cell, index) {
        var td = el(index === 0 ? 'th' : 'td', { scope: index === 0 ? 'row' : null, text: cellText(cell) });
        if (typeof cell === 'string') ru(td);
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    tableNode.appendChild(tbody);
    scroller.appendChild(tableNode);
    return scroller;
  };

  function treeNode(entry, depth) {
    if (!entry || depth > 6) return null;
    if (entry.result) {
      if (!bilingual(entry.result) || !Array.isArray(entry.examples)) return null;
      var result = el('div', { class: 'tree-result' }, [el('strong', { text: I.pick(entry.result) })]);
      if (entry.examples.length) result.appendChild(ru(el('span', { class: 'tree-examples', text: ' ' + entry.examples.join('; ') })));
      return result;
    }
    if (!bilingual(entry.q)) return null;
    var yes = treeNode(entry.yes, depth + 1), no = treeNode(entry.no, depth + 1);
    if (!yes || !no) return null;
    var wrap = el('div', { class: 'tree-node' });
    wrap.appendChild(el('p', { class: 'tree-question', text: I.pick(entry.q) }));
    var list = el('ul', { class: 'tree-branches' });
    list.appendChild(el('li', { class: 'tree-yes' }, [el('span', { class: 'tree-label', text: t('tree_yes') }), yes]));
    list.appendChild(el('li', { class: 'tree-no' }, [el('span', { class: 'tree-label', text: t('tree_no') }), no]));
    wrap.appendChild(list);
    return wrap;
  }

  /** Decision trees are nested lists: a linear, screen-reader friendly description. */
  UI.diagramTree = function (figure) {
    if (!figure || figure.kind !== 'tree') return null;
    var body = treeNode(figure.root, 0);
    if (!body) return null;
    var wrap = el('div', { class: 'decision-tree', 'data-figure': figure.id, role: 'group', 'aria-label': I.pick(figure.title) });
    wrap.appendChild(body);
    return wrap;
  };

  /** Nested viewer: zoom, internal panning, the same one-level Back. */
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
      viewport.appendChild(svg || el('p', { text: t('theory_visual_unavailable') }));
      var update = function () {
        if (svg) svg.style.width = (state.scale * 100) + '%';
        status.textContent = t('theory_zoom_fmt', Math.round(state.scale * 100) + '%');
        smaller.disabled = state.scale <= 1;
        larger.disabled = state.scale >= 3;
      };
      smaller.addEventListener('click', function () { state.scale = Math.max(1, state.scale - .5); update(); });
      larger.addEventListener('click', function () { state.scale = Math.min(3, state.scale + .5); update(); });
      fit.addEventListener('click', function () { state.scale = 1; state.x = state.y = 0; viewport.scrollLeft = viewport.scrollTop = 0; update(); });
      viewport.addEventListener('scroll', function () { state.x = viewport.scrollLeft; state.y = viewport.scrollTop; });
      update();
      wrap.appendChild(controls); wrap.appendChild(viewport);
      wrap.appendChild(UI.diagramLegend(figure));
      wrap.appendChild(el('p', { class: 'diagram-caption', text: I.pick(figure.caption) }));
      wrap.appendChild(el('p', { class: 'muted small', text: t('theory_pan_hint') }));
      var footer = el('div', { class: 'theory-footer' });
      var back = el('button', { class: 'btn', type: 'button', text: t('prev') });
      back.addEventListener('click', UI.backModal); footer.appendChild(back);
      UI.modal(I.pick(figure.title), wrap, { tall: true, wide: true, push: !keepHistory, keepHistory: !!keepHistory,
        language: true, refresh: render, footer: footer });
      viewport.scrollLeft = state.x; viewport.scrollTop = state.y;
    };
    render(false);
  };

  UI.diagramCard = function (figure, lessonId) {
    var block = el('figure', { class: 'theory-figure figure-' + figure.kind, 'data-figure': figure.id });
    block.appendChild(el('h4', { text: I.pick(figure.title) }));
    var body = figure.kind === 'svg' ? UI.diagramSvg(figure) : (figure.kind === 'table' ? UI.diagramTable(figure) : UI.diagramTree(figure));
    block.appendChild(body || el('p', { text: t('theory_visual_unavailable') }));
    if (figure.kind === 'svg') block.appendChild(UI.diagramLegend(figure));
    if (figure.kind !== 'table') block.appendChild(el('figcaption', { class: 'diagram-caption', text: I.pick(figure.caption) }));
    if (body && figure.kind === 'svg') {
      var enlarge = el('button', { class: 'btn diagram-enlarge', type: 'button', text: t('theory_enlarge'),
        'aria-haspopup': 'dialog', 'data-focus-key': 'figure-' + lessonId + '-' + figure.id });
      enlarge.addEventListener('click', function () { enlarge.focus(); UI.openDiagram(figure); });
      block.appendChild(enlarge);
    }
    return block;
  };

  /* ----------------------------------------------------------- rule cards */
  function section(className, titleKey, children) {
    var block = el('section', { class: className });
    block.appendChild(el('h3', { text: t(titleKey) }));
    children.forEach(function (child) { block.appendChild(child); });
    return block;
  }
  function paragraphs(list, tag) {
    var wrap = el(tag || 'ul', {});
    (list || []).forEach(function (line) { wrap.appendChild(el(tag === 'div' ? 'p' : 'li', { text: line })); });
    return wrap;
  }

  /** Rule card: exact formulation, limits/exceptions, everyday explanation, examples, steps, visuals, sources. */
  UI.openRules = function (ids, options) {
    options = options || {};
    var lessons = ids.map(function (id) { return C.lessonById(id); }).filter(Boolean);
    if (!lessons.length) return;
    var render = function (keepHistory) {
      var savedScroll = keepHistory ? $('.sheet', $('#modal')).scrollTop : 0;
      var wrap = el('div', { class: 'theory-content' });
      lessons.forEach(function (lesson) {
        var article = el('article', { class: 'theory-lesson rule-card', 'data-lesson': lesson.id });
        if (lessons.length > 1) article.appendChild(el('h3', { text: I.pick(lesson.title) }));
        article.appendChild(section('theory-rules', 'rule_statement', [paragraphs(I.pick(lesson.rule), 'div')]));
        article.appendChild(section('theory-exceptions', 'rule_exceptions', [paragraphs(I.pick(lesson.exceptions))]));
        article.appendChild(section('theory-everyday', 'theory_everyday', [paragraphs(I.pick(lesson.everyday), 'div')]));
        var good = ru(el('ul', { class: 'examples-good' }));
        lesson.correct.forEach(function (example) { good.appendChild(el('li', { text: '✓ ' + example })); });
        var bad = el('ul', { class: 'examples-bad' });
        lesson.wrong.forEach(function (pair) {
          var li = ru(el('li', {}));
          li.appendChild(el('span', { class: 'wrong', text: '✗ ' + pair.wrong }));
          li.appendChild(doc.createTextNode(' → '));
          li.appendChild(el('span', { class: 'right', text: pair.right }));
          bad.appendChild(li);
        });
        article.appendChild(section('theory-example', 'rule_examples', [el('h4', { text: t('rule_correct') }), good,
          el('h4', { text: t('rule_wrong') }), bad]));
        var steps = el('ol', { class: 'steps' });
        (I.pick(lesson.steps) || []).forEach(function (step) { steps.appendChild(el('li', { text: step })); });
        article.appendChild(section('theory-steps', 'rule_steps', [steps]));
        var figures = (lesson.figures || []).map(function (id) { return C.figureById(id); }).filter(Boolean);
        if (figures.length) {
          var visuals = section('theory-visuals', 'theory_visuals', []);
          figures.forEach(function (figure) { visuals.appendChild(UI.diagramCard(figure, lesson.id)); });
          article.appendChild(visuals);
        }
        var sourceList = el('ul', { class: 'sources' });
        (lesson.sources || []).forEach(function (id) {
          var source = C.sources[id];
          if (source) sourceList.appendChild(ru(el('li', { text: source.title + (source.date ? ' (' + t('checked_on_fmt', source.date) + ')' : '') })));
        });
        article.appendChild(section('theory-sources', 'rule_sources', [sourceList]));
        var drill = el('button', { class: 'btn ghost rule-drill', type: 'button', text: t('rule_drill') });
        drill.addEventListener('click', function () { UI.closeModal(); RUN.startRule(lesson.id); go('#/run'); });
        article.appendChild(drill);
        wrap.appendChild(article);
      });
      var footer = el('div', { class: 'rowline theory-footer' });
      var back = el('button', { class: 'btn', type: 'button', text: t('prev') });
      back.addEventListener('click', UI.backModal);
      footer.appendChild(back);
      UI.modal(options.title ? I.pick(options.title) : I.pick(lessons[0].title), wrap, { tall: true,
        push: !keepHistory, keepHistory: !!keepHistory, language: true, refresh: render, footer: footer });
      if (keepHistory) $('.sheet', $('#modal')).scrollTop = savedScroll;
    };
    render(false);
  };
  UI.openTheory = UI.openRules;

  UI.ruleButton = function (label, ids, className) {
    var button = el('button', { class: 'theory-trigger ' + (className || ''), type: 'button', title: t('theory_open'),
      'aria-haspopup': 'dialog', 'data-lesson': ids.join(' '), 'data-focus-key': 'rule-' + ids.join('-') });
    button.appendChild(el('span', { text: label }));
    button.appendChild(el('span', { class: 'theory-arrow', text: '›', 'aria-hidden': 'true' }));
    button.addEventListener('click', function () { button.focus(); UI.openRules(ids); });
    return button;
  };

  UI.studyPoints = function (topic) {
    var study = C.studyFor(topic);
    var list = el('ul', { class: 'study-points' });
    (study ? I.pick(study) || [] : []).forEach(function (point, index) {
      var id = (study.lessons || [])[index];
      list.appendChild(el('li', {}, [C.lessonById(id) ? UI.ruleButton(point, [id], 'study-point-link') : doc.createTextNode(point)]));
    });
    return list;
  };

  /** Remediation block: the concrete rules of the error, their cards and drills. */
  UI.studyBlock = function (task, rules) {
    if (!task) return null;
    rules = (rules && rules.length ? rules : (task.rules || [task.rule])).filter(function (id) { return C.lessonById(id); });
    if (!rules.length) return null;
    var box = el('div', { class: 'study-topic', 'data-topic': task.topic });
    box.appendChild(el('h4', { text: t('study_rules_title') }));
    var list = el('ul', { class: 'study-points' });
    rules.forEach(function (id) { list.appendChild(el('li', {}, [UI.ruleButton(C.ruleTitle(id), [id], 'remedy-rule-link')])); });
    box.appendChild(list);
    var row = el('div', { class: 'rowline wrap' });
    var drill = el('button', { class: 'btn primary', type: 'button', text: t('rule_drill') });
    drill.addEventListener('click', function () { RUN.startRule(rules[0]); go('#/run'); });
    var open = el('button', { class: 'btn ghost', type: 'button', text: t('study_open') });
    open.addEventListener('click', function () { go('#/study/' + task.topic); });
    row.appendChild(drill); row.appendChild(open);
    box.appendChild(row);
    return box;
  };

  /** Analysis of one task: answers, diagnosis by rule, worked steps, rules, analogs. */
  UI.breakdown = function (task, userAnswer, options) {
    options = options || {};
    var box = el('div', { class: 'breakdown' });
    var correct = A.check(userAnswer, task);
    var answers = el('div', { class: 'answer-compare' });
    var shownUser = A.formatUser(userAnswer, task);
    answers.appendChild(el('div', { class: 'compare-box ' + (correct ? 'good' : 'bad') }, [
      el('span', { class: 'compare-label', text: t('your_answer') }),
      ru(el('span', { class: 'compare-value', text: shownUser || '—' }))]));
    answers.appendChild(el('div', { class: 'compare-box good' }, [
      el('span', { class: 'compare-label', text: t('correct_answer') }),
      ru(el('span', { class: 'compare-value', text: A.display(task.check) }))]));
    box.appendChild(answers);
    if (task.check.type === 'word' && (task.check.accept || []).length) {
      box.appendChild(el('p', { class: 'muted small', text: t('also_accepted_fmt', task.check.accept.join('; ')) }));
    }
    var wrongItems = correct ? [] : (A.misjudged(userAnswer, task) || []);
    if (wrongItems.length) box.appendChild(el('p', { class: 'banner bad', text: t('misjudged_fmt', wrongItems.join(', ')) }));
    var rules = correct ? (task.rules || [task.rule]) : C.rulesFor(task, userAnswer);
    var diagnoses = correct ? [] : C.diagnoses(rules);
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
      details.appendChild(paragraphs(hints));
      box.appendChild(details);
    }
    box.appendChild(el('div', { class: 'muted small', text: [C.topicTitle(task.topic), t('authored_task')].join(' · ') }));
    if (!correct) {
      var studyBlock = UI.studyBlock(task, rules);
      if (studyBlock) box.appendChild(studyBlock);
    }
    if (options.analogous !== false) {
      var analogous = options.analogous || RUN.analogousFor([{ taskId: task.id, user: userAnswer }], 2);
      if (analogous.length) {
        box.appendChild(el('h4', { text: t('analogous_title') }));
        box.appendChild(el('p', { class: 'muted small', text: t('analogous_hint') }));
        analogous.forEach(function (item, index) { box.appendChild(UI.analogousItem(item, index + 1)); });
      }
    }
    return box;
  };

  /** An analogous exercise with its own answer control, check, solution and rule. */
  UI.analogousItem = function (task, index, state) {
    state = state || {};
    var wrap = el('div', { class: 'analogous-item', 'data-task-id': task.id, 'data-index': String(index),
      'data-value': state.value || '', 'data-status': state.status || '', 'data-solution': state.solution ? '1' : '0' });
    wrap.appendChild(el('div', { class: 'analogous-head', text: t('analogous_task_fmt', index) + ' · ' + C.ruleTitle(task.rule) }));
    wrap.appendChild(el('div', { class: 'task-text', text: I.pick(task.instruction) }));
    wrap.appendChild(UI.material(task));
    var value = state.value || '';
    var control = UI.answerControl(task, value, function (next) { value = next; wrap.setAttribute('data-value', next); });
    wrap.appendChild(control.node);
    var check = el('button', { class: 'btn primary', type: 'button', text: t('check_answer') });
    var reveal = el('button', { class: 'btn ghost', type: 'button', text: t('show_solution') });
    var feedback = el('div', { class: 'feedback' + (state.status ? ' ' + state.status : '') });
    if (state.status) feedback.textContent = t(state.status === 'good' ? 'answer_correct' : 'answer_incorrect');
    var solution = el('div', { class: 'analogous-solution' + (state.solution ? '' : ' hidden') });
    solution.appendChild(el('p', {}, [el('strong', { text: t('correct_answer') + ': ' }), ru(el('span', { text: A.display(task.check) }))]));
    var steps = el('ol', { class: 'steps' });
    (I.pick(task.solution) || []).forEach(function (step) { steps.appendChild(el('li', { text: step })); });
    solution.appendChild(steps);
    var studyHolder = el('div', { class: 'analogous-study' + (state.status === 'bad' ? '' : ' hidden') });
    if (state.status === 'bad') { var restored = UI.studyBlock(task, C.rulesFor(task, value)); if (restored) studyHolder.appendChild(restored); }
    var row = el('div', { class: 'answer-row' });
    row.appendChild(check); row.appendChild(reveal);
    wrap.appendChild(row);
    wrap.appendChild(feedback);
    wrap.appendChild(solution);
    wrap.appendChild(studyHolder);
    check.addEventListener('click', function () {
      var ok = A.check(value, task);
      var status = ok ? 'good' : 'bad';
      wrap.setAttribute('data-status', status);
      feedback.className = 'feedback ' + status;
      feedback.textContent = ok ? t('answer_correct') : t('answer_incorrect');
      if (!ok) {
        solution.classList.remove('hidden');
        wrap.setAttribute('data-solution', '1');
        clear(studyHolder);
        var study = UI.studyBlock(task, C.rulesFor(task, value));
        if (study) studyHolder.appendChild(study);
        studyHolder.classList.remove('hidden');
        if (typeof studyHolder.scrollIntoView === 'function') studyHolder.scrollIntoView({ block: 'start' });
      } else {
        studyHolder.classList.add('hidden');
      }
      S.recordTask(task, ok, 0);
      B.vibrate(ok ? 12 : 30);
    });
    reveal.addEventListener('click', function () {
      solution.classList.toggle('hidden');
      wrap.setAttribute('data-solution', solution.classList.contains('hidden') ? '0' : '1');
    });
    return wrap;
  };

  /* ------------------------------------------------------------------ *
   * 4. Экраны
   * ------------------------------------------------------------------ */
  var SCREENS = {};

  function statCard(value, label) {
    return el('div', { class: 'card stat' }, [el('div', { class: 'stat-value', text: String(value) }),
      el('div', { class: 'muted', text: label })]);
  }

  SCREENS['#/home'] = function () {
    var totals = AN.totals(S.progress);
    var today = S.progress.daily[U.today()] || 0;
    var goal = S.settings.dailyGoal || 20;
    var root = el('section', { class: 'screen' });
    var hero = el('div', { class: 'hero' });
    hero.appendChild(el('h1', { text: t('app_name') }));
    hero.appendChild(el('p', { class: 'muted', text: t('app_tagline') }));
    var actions = el('div', { class: 'hero-actions' });
    [['#/tests', 'nav_tests', 'primary'], ['#/exam', 'nav_exam', ''], ['#/practice', 'nav_practice', ''], ['#/rules', 'nav_rules', '']]
      .forEach(function (entry) {
        var btn = el('button', { class: 'btn ' + entry[2], type: 'button', text: t(entry[1]) });
        btn.addEventListener('click', function () { go(entry[0]); });
        actions.appendChild(btn);
      });
    hero.appendChild(actions);
    root.appendChild(hero);
    var cards = el('div', { class: 'grid-4' });
    cards.appendChild(statCard(totals.tests, t('stat_tests')));
    cards.appendChild(statCard(totals.tasks, t('stat_tasks')));
    cards.appendChild(statCard(Math.round(totals.accuracy * 100) + '%', t('stat_accuracy')));
    cards.appendChild(statCard(S.progress.streak || 0, t('stat_streak')));
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
    var weak = AN.weakRules(S.progress, 3);
    if (weak.length) {
      var weakCard = el('div', { class: 'card' });
      weakCard.appendChild(el('h3', { text: t('weak_rules') }));
      weakCard.appendChild(UI.bars(weak.map(function (item) {
        return { label: C.ruleTitle(item.rule), value: Math.round(item.rate * 100), text: Math.round(item.rate * 100) + '% · ' + item.total,
          color: rateColor(item.rate), action: function () { RUN.startRule(item.rule); go('#/run'); } };
      })));
      root.appendChild(weakCard);
    }
    if (S.session && !S.session.finished) {
      var resume = el('div', { class: 'card accent' });
      resume.appendChild(el('h3', { text: t('resume_title') }));
      resume.appendChild(el('p', { class: 'muted', text: t('resume_text', S.session.title, S.session.index + 1, S.session.order.length) }));
      var resumeRow = el('div', { class: 'rowline' });
      var resumeBtn = el('button', { class: 'btn primary', type: 'button', text: t('resume') });
      resumeBtn.addEventListener('click', function () { go('#/run'); });
      var dropBtn = el('button', { class: 'btn ghost', type: 'button', text: t('discard') });
      dropBtn.addEventListener('click', function () {
        UI.confirm(t('discard_confirm'), function () { S.session = null; S.saveSession(true); UI.render(); });
      });
      resumeRow.appendChild(resumeBtn); resumeRow.appendChild(dropBtn);
      resume.appendChild(resumeRow);
      root.appendChild(resume);
    }
    root.appendChild(el('p', { class: 'muted small disclaimer', text: I.pick(C.disclaimer) }));
    return root;
  };

  function examInfo() {
    var spec = C.specification || {};
    return t('exam_structure_fmt', spec.tasks || 40, (spec.parts || {}).A || 18, (spec.parts || {}).B || 22, spec.minutes || 120);
  }

  SCREENS['#/tests'] = function () {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('nav_tests') }));
    root.appendChild(el('p', { class: 'muted', text: t('tests_intro') }));
    root.appendChild(el('p', { class: 'banner info', text: examInfo() }));
    var grid = el('div', { class: 'grid-2' });
    C.variants().forEach(function (variant) {
      var card = el('div', { class: 'card variant-card', 'data-year': String(variant.year) });
      card.appendChild(el('h3', { text: t('variant_title_fmt', variant.year) }));
      card.appendChild(el('p', { class: 'muted small', text: t('variant_parts_fmt', variant.partA, variant.partB) }));
      var row = el('div', { class: 'rowline' });
      var exam = el('button', { class: 'btn primary', type: 'button', text: t('start_exam') });
      exam.addEventListener('click', function () { RUN.startVariant(variant, 'exam'); B.keepScreenOn(S.settings.keepScreenOn); go('#/run'); });
      var train = el('button', { class: 'btn', type: 'button', text: t('start_train') });
      train.addEventListener('click', function () { RUN.startVariant(variant, 'train'); B.keepScreenOn(S.settings.keepScreenOn); go('#/run'); });
      row.appendChild(exam); row.appendChild(train);
      card.appendChild(row);
      grid.appendChild(card);
    });
    root.appendChild(grid);
    root.appendChild(el('p', { class: 'muted small disclaimer', text: I.pick(C.disclaimer) }));
    return root;
  };

  SCREENS['#/exam'] = function () {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('nav_exam') }));
    root.appendChild(el('div', { class: 'card' }, [el('p', { text: t('exam_rules_fmt', S.settings.examMinutes) }),
      el('p', { class: 'muted small', text: examInfo() })]));
    root.appendChild(el('p', { class: 'muted', text: t('choose_variant') }));
    var grid = el('div', { class: 'grid-3' });
    C.variants().forEach(function (variant) {
      var btn = el('button', { class: 'btn big', type: 'button', text: String(variant.year) });
      btn.addEventListener('click', function () { RUN.startVariant(variant, 'exam'); B.keepScreenOn(S.settings.keepScreenOn); go('#/run'); });
      grid.appendChild(btn);
    });
    root.appendChild(grid);
    var custom = el('button', { class: 'btn', type: 'button', text: t('mixed_exam') });
    custom.addEventListener('click', function () {
      RUN.startSet(C.mixedExam(), t('mixed_exam_title'), 'exam');
      B.keepScreenOn(S.settings.keepScreenOn);
      go('#/run');
    });
    root.appendChild(custom);
    return root;
  };

  SCREENS['#/run'] = function () {
    var run = S.session;
    if (!run) { go('#/tests'); return el('section', { class: 'screen' }); }
    if (run.finished) { go('#/result/' + run.id); return el('section', { class: 'screen' }); }
    var task = RUN.current();
    if (!task) { go('#/tests'); return el('section', { class: 'screen' }); }
    var root = el('section', { class: 'screen run-screen' });
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
    root.appendChild(UI.taskCard(task, run, run.mode === 'exam' ? {} : {
      onCheck: function () {
        var correct = RUN.checkCurrent();
        B.vibrate(correct ? 12 : 40);
        UI.render();
        if (!correct) {
          var studyNode = doc.querySelector('.study-topic');
          if (studyNode && typeof studyNode.scrollIntoView === 'function') studyNode.scrollIntoView({ block: 'start' });
        }
        if (correct && S.settings.autoAdvance) {
          setTimeout(function () {
            if (!S.settings.autoAdvance) return;
            if (RUN.current() && RUN.current().id === task.id) { RUN.step(1); UI.render(); }
          }, 700);
        }
      },
    }));
    var hints = I.pick(task.hints) || [];
    var toolsCard = el('div', { class: 'card tools-strip' });
    var toolsRow = el('div', { class: 'rowline wrap' });
    var hintBtn = el('button', { class: 'btn ghost', type: 'button', text: t('tool_hint') });
    hintBtn.disabled = !hints.length || run.mode === 'exam';
    hintBtn.addEventListener('click', function () {
      UI.modal(t('hints'), el('div', {}, hints.map(function (text, index) { return el('p', { class: 'banner info', text: (index + 1) + '. ' + text }); })));
    });
    toolsRow.appendChild(hintBtn);
    [['rules', t('tool_rules')], ['scratch', t('tool_scratch')], ['memos', t('tool_memos')]].forEach(function (pair) {
      var btn = el('button', { class: 'btn ghost', type: 'button', text: pair[1] });
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
          breakdown.appendChild(UI.breakdown(task, run.answers[task.id]));
          root.appendChild(breakdown);
        }
      }
    }
    var nav = el('div', { class: 'run-nav' });
    var prev = el('button', { class: 'btn', type: 'button', text: '← ' + t('prev') });
    prev.disabled = run.index === 0;
    prev.addEventListener('click', function () { RUN.step(-1); UI.render(); });
    var next = el('button', { class: 'btn', type: 'button', text: t('next') + ' →' });
    next.disabled = run.index >= run.order.length - 1;
    next.addEventListener('click', function () { RUN.step(1); UI.render(); });
    var mark = el('button', { class: 'btn ghost', type: 'button', text: t('mark') });
    mark.addEventListener('click', function () { RUN.mark(task.id); UI.render(); });
    var grid = el('button', { class: 'btn ghost', type: 'button', text: t('task_grid') });
    grid.addEventListener('click', function () { TOOLS.taskGrid(); });
    [prev, mark, grid, next].forEach(function (node) { nav.appendChild(node); });
    root.appendChild(nav);
    var finishRow = el('div', { class: 'rowline center' });
    var finish = el('button', { class: 'btn primary', type: 'button', text: t('finish_test') });
    finish.addEventListener('click', function () {
      var unanswered = run.order.filter(function (id) { return String(run.answers[id] === undefined ? '' : run.answers[id]).trim() === ''; }).length;
      UI.confirm(run.mode === 'exam' && unanswered ? t('unanswered_warning_fmt', unanswered) : t('finish_confirm'), function () {
        var attempt = RUN.finish();
        go('#/result/' + (attempt ? attempt.id : ''));
      }, t('finish_test'));
    });
    finishRow.appendChild(finish);
    root.appendChild(finishRow);
    if (run.mode === 'exam') startTimer(timer, run);
    else timer.textContent = U.duration(run.seconds, I.lang);
    return root;
  };

  var timerHandle = null;
  function startTimer(node, run) {
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

  function findAttempt(id) {
    var attempts = S.progress.attempts || [];
    if (!id) return attempts[attempts.length - 1] || null;
    var found = null;
    attempts.forEach(function (attempt) { if (attempt.id === id) found = attempt; });
    return found;
  }

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
    if (summary.byPart.A.total) details.appendChild(el('p', { text: t('part_a_fmt', summary.byPart.A.correct, summary.byPart.A.total) }));
    if (summary.byPart.B.total) details.appendChild(el('p', { text: t('part_b_fmt', summary.byPart.B.correct, summary.byPart.B.total) }));
    details.appendChild(el('p', { text: t('time_spent_fmt', U.duration(summary.seconds, I.lang)) }));
    details.appendChild(el('p', { class: 'muted small', text: t('score_note') }));
    top.appendChild(details);
    root.appendChild(top);
    var actions = el('div', { class: 'rowline wrap' });
    if (summary.mistakes.length) {
      var review = el('button', { class: 'btn primary', type: 'button', text: t('review_mistakes_fmt', summary.mistakes.length) });
      review.addEventListener('click', function () { go('#/mistakes/' + attempt.id); });
      actions.appendChild(review);
      var reinforce = el('button', { class: 'btn', type: 'button', text: t('reinforce') });
      reinforce.addEventListener('click', function () {
        var tasks = RUN.analogousFor(RUN.wrongResults(attempt), 2);
        if (!tasks.length) { CT.toast(t('no_analogous')); return; }
        RUN.startSet(tasks, t('reinforce_title'), 'train');
        go('#/run');
      });
      actions.appendChild(reinforce);
    }
    var exportBtn = el('button', { class: 'btn ghost', type: 'button', text: t('export_report') });
    exportBtn.addEventListener('click', function () { exportReport(attempt); });
    actions.appendChild(exportBtn);
    var again = el('button', { class: 'btn ghost', type: 'button', text: t('to_tests') });
    again.addEventListener('click', function () { go('#/tests'); });
    actions.appendChild(again);
    root.appendChild(actions);
    var topics = {};
    (attempt.results || []).forEach(function (result) {
      var entry = topics[result.topic] = topics[result.topic] || { correct: 0, total: 0 };
      entry.total++; if (result.correct) entry.correct++;
    });
    var items = Object.keys(topics).map(function (key) {
      var rate = topics[key].correct / topics[key].total;
      return { label: C.topicTitle(key), value: Math.round(rate * 100), text: topics[key].correct + '/' + topics[key].total, color: rateColor(rate) };
    }).sort(function (a, b) { return a.value - b.value; });
    if (items.length) {
      var card = el('div', { class: 'card' });
      card.appendChild(el('h3', { text: t('by_topic_attempt') }));
      card.appendChild(UI.bars(items));
      root.appendChild(card);
    }
    return root;
  };

  SCREENS['#/mistakes'] = function (extra) {
    var attempt = findAttempt(extra);
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('mistakes_title') }));
    if (!attempt) { root.appendChild(el('p', { class: 'muted', text: t('no_data_yet') })); return root; }
    var wrong = RUN.wrongResults(attempt);
    if (!wrong.length) { root.appendChild(el('div', { class: 'banner good', text: t('no_mistakes') })); return root; }
    root.appendChild(el('p', { class: 'muted', text: t('mistakes_intro_fmt', wrong.length) }));
    var reinforce = el('button', { class: 'btn primary', type: 'button', text: t('reinforce') });
    reinforce.addEventListener('click', function () {
      var tasks = RUN.analogousFor(wrong, 2);
      if (!tasks.length) { CT.toast(t('no_analogous')); return; }
      RUN.startSet(tasks, t('reinforce_title'), 'train');
      go('#/run');
    });
    root.appendChild(reinforce);
    var rulesSeen = {};
    wrong.forEach(function (result) {
      var task = C.taskById(result.taskId);
      C.rulesFor(task, result.user).forEach(function (rule) { rulesSeen[rule] = (rulesSeen[rule] || 0) + 1; });
      var card = el('div', { class: 'card' });
      var head = el('div', { class: 'task-head' });
      head.appendChild(el('span', { class: 'badge', text: badge(task) }));
      head.appendChild(el('span', { class: 'muted small', text: C.topicTitle(task.topic) }));
      if (task.year) head.appendChild(el('span', { class: 'muted small', text: String(task.year) }));
      card.appendChild(head);
      card.appendChild(el('div', { class: 'task-text', text: I.pick(task.instruction) }));
      card.appendChild(UI.material(task));
      if (task.check.type === 'multi' || task.check.type === 'single') {
        var opts = ru(el('ol', { class: 'task-items' }));
        (task.items || I.pick(task.choices) || []).forEach(function (item, index) { opts.appendChild(el('li', { 'data-n': String(index + 1) }, [item])); });
        if (!task.items) opts.removeAttribute('lang');
        card.appendChild(opts);
      }
      card.appendChild(UI.breakdown(task, result.user));
      root.appendChild(card);
    });
    var plan = el('div', { class: 'card accent' });
    plan.appendChild(el('h3', { text: t('repeat_rules') }));
    var ul = el('ul', { class: 'study-points' });
    Object.keys(rulesSeen).forEach(function (rule) {
      var li = el('li', {});
      li.appendChild(UI.ruleButton(C.ruleTitle(rule) + ' — ' + t('tasks_count_fmt', rulesSeen[rule]), [rule], 'plan-rule-link'));
      ul.appendChild(li);
    });
    plan.appendChild(ul);
    root.appendChild(plan);
    return root;
  };

  SCREENS['#/practice'] = function (extra) {
    var root = el('section', { class: 'screen' });
    if (extra && C.topics[extra]) { RUN.startPractice(extra); go('#/run'); return root; }
    root.appendChild(el('h1', { text: t('nav_practice') }));
    root.appendChild(el('p', { class: 'muted', text: t('practice_intro') }));
    var stats = AN.topicStats(S.progress);
    var grid = el('div', { class: 'grid-3' });
    C.order.forEach(function (topic) {
      var entry = stats[topic];
      var card = el('button', { class: 'btn topic-btn', type: 'button', 'data-topic': topic });
      card.appendChild(el('span', { class: 'topic-name', text: C.topicTitle(topic) }));
      card.appendChild(el('span', { class: 'muted small', text: entry ? t('topic_stats_fmt', Math.round(entry.rate * 100) + '%', entry.total)
        : t('tasks_count_fmt', C.tasksByTopic(topic).length + C.analogByTopic(topic).length) }));
      card.addEventListener('click', function () { RUN.startPractice(topic); B.keepScreenOn(S.settings.keepScreenOn); go('#/run'); });
      grid.appendChild(card);
    });
    root.appendChild(grid);
    return root;
  };

  SCREENS['#/study'] = function (extra) {
    var root = el('section', { class: 'screen' });
    var topic = extra && C.topics[extra] ? extra : null;
    if (!topic) {
      root.appendChild(el('h1', { text: t('nav_study') }));
      root.appendChild(el('p', { class: 'muted', text: t('study_index_intro') }));
      var grid = el('div', { class: 'grid-3' });
      C.order.forEach(function (key) {
        var card = el('button', { class: 'btn topic-btn', type: 'button', 'data-topic': key });
        card.appendChild(el('span', { class: 'topic-name', text: C.topicTitle(key) }));
        card.appendChild(el('span', { class: 'muted small', text: t('rules_count_fmt', C.rulesOfTopic(key).length) }));
        card.addEventListener('click', function () { go('#/study/' + key); });
        grid.appendChild(card);
      });
      root.appendChild(grid);
      return root;
    }
    root.appendChild(el('h1', { text: t('study_topic_fmt', C.topicTitle(topic)) }));
    root.appendChild(el('p', { class: 'muted', text: t('study_intro') }));
    if (S.session && !S.session.finished) {
      var returnBtn = el('button', { class: 'btn', type: 'button', text: t('return_to_task') });
      returnBtn.addEventListener('click', function () { go('#/run'); });
      root.appendChild(returnBtn);
    }
    var pointsCard = el('div', { class: 'card study-points-card' });
    pointsCard.appendChild(el('h3', { text: t('study_points') }));
    pointsCard.appendChild(UI.studyPoints(topic));
    root.appendChild(pointsCard);
    var examples = C.tasksByTopic(topic).slice(0, 2).concat(C.analogByTopic(topic).slice(0, 1));
    if (examples.length) {
      root.appendChild(el('h2', { text: t('study_examples') }));
      examples.forEach(function (example) {
        var card = el('div', { class: 'card study-example' });
        card.appendChild(el('div', { class: 'task-text', text: I.pick(example.instruction) }));
        card.appendChild(UI.material(example));
        if (example.check.type === 'multi' || example.check.type === 'single') {
          var opts = ru(el('ol', { class: 'task-items' }));
          (example.items || I.pick(example.choices) || []).forEach(function (item, index) { opts.appendChild(el('li', { 'data-n': String(index + 1) }, [item])); });
          card.appendChild(opts);
        }
        card.appendChild(el('p', {}, [el('strong', { text: t('correct_answer') + ': ' }), ru(el('span', { text: A.display(example.check) }))]));
        var details = el('details', { class: 'hints' });
        details.appendChild(el('summary', { text: t('show_solution') }));
        var steps = el('ol', { class: 'steps' });
        (I.pick(example.solution) || []).forEach(function (step) { steps.appendChild(el('li', { text: step })); });
        details.appendChild(steps);
        card.appendChild(details);
        root.appendChild(card);
      });
    }
    var practice = el('button', { class: 'btn primary', type: 'button', text: t('study_practice') });
    practice.addEventListener('click', function () { go('#/practice/' + topic); });
    root.appendChild(practice);
    return root;
  };

  SCREENS['#/stats'] = function () {
    var totals = AN.totals(S.progress);
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('nav_stats') }));
    var cards = el('div', { class: 'grid-4' });
    cards.appendChild(statCard(totals.tests, t('stat_tests')));
    cards.appendChild(statCard(totals.tasks, t('stat_tasks')));
    cards.appendChild(statCard(Math.round(totals.accuracy * 100) + '%', t('stat_accuracy')));
    cards.appendChild(statCard(totals.minutes, t('stat_minutes')));
    root.appendChild(cards);
    var topicStats = AN.topicStats(S.progress);
    var topicCard = el('div', { class: 'card' });
    topicCard.appendChild(el('h3', { text: t('by_topic') }));
    topicCard.appendChild(UI.bars(C.order.filter(function (topic) { return topicStats[topic]; }).map(function (topic) {
      var entry = topicStats[topic];
      return { label: C.topicTitle(topic), value: Math.round(entry.rate * 100), text: Math.round(entry.rate * 100) + '% · ' + entry.total,
        color: rateColor(entry.rate), action: function () { go('#/practice/' + topic); } };
    })));
    root.appendChild(topicCard);
    var weak = AN.weakRules(S.progress, 6);
    if (weak.length) {
      var ruleCard = el('div', { class: 'card' });
      ruleCard.appendChild(el('h3', { text: t('weak_rules') }));
      ruleCard.appendChild(UI.bars(weak.map(function (item) {
        return { label: C.ruleTitle(item.rule), value: Math.round(item.rate * 100), text: Math.round(item.rate * 100) + '% · ' + item.total,
          color: rateColor(item.rate), action: function () { RUN.startRule(item.rule); go('#/run'); } };
      })));
      root.appendChild(ruleCard);
    }
    var yearStats = AN.yearStats(S.progress);
    if (Object.keys(yearStats).length) {
      var yearCard = el('div', { class: 'card' });
      yearCard.appendChild(el('h3', { text: t('by_year') }));
      yearCard.appendChild(UI.bars(Object.keys(yearStats).sort().map(function (year) {
        return { label: year, value: Math.round(yearStats[year].rate * 100), text: Math.round(yearStats[year].rate * 100) + '%' };
      })));
      root.appendChild(yearCard);
    }
    var daily = S.progress.daily || {};
    var days = Object.keys(daily).sort().slice(-14);
    if (days.length) {
      var dailyCard = el('div', { class: 'card' });
      dailyCard.appendChild(el('h3', { text: t('daily_activity') }));
      dailyCard.appendChild(UI.bars(days.map(function (day) { return { label: day.slice(5), value: daily[day], text: String(daily[day]) }; })));
      root.appendChild(dailyCard);
    }
    var attempts = (S.progress.attempts || []).slice(-10).reverse();
    if (attempts.length) {
      var listCard = el('div', { class: 'card' });
      listCard.appendChild(el('h3', { text: t('last_attempts') }));
      var list = el('div', { class: 'attempt-list' });
      attempts.forEach(function (attempt) {
        var summary = AN.attemptSummary(attempt);
        var row = el('button', { class: 'attempt-row clickable', type: 'button' });
        row.appendChild(el('span', { class: 'attempt-title', text: attempt.title }));
        row.appendChild(el('span', { class: 'muted small', text: U.formatDate(attempt.finishedAt, I.lang) + ' · ' + U.duration(attempt.seconds, I.lang) }));
        row.appendChild(el('span', { class: 'attempt-score', text: summary.correct + '/' + summary.total }));
        row.addEventListener('click', function () { go('#/result/' + attempt.id); });
        list.appendChild(row);
      });
      listCard.appendChild(list);
      root.appendChild(listCard);
    }
    var actions = el('div', { class: 'rowline wrap' });
    var exportBtn = el('button', { class: 'btn', type: 'button', text: t('export_report') });
    exportBtn.addEventListener('click', function () { exportReport(null); });
    var reset = el('button', { class: 'btn ghost', type: 'button', text: t('reset_progress') });
    reset.addEventListener('click', function () {
      UI.confirm(t('reset_confirm'), function () { S.resetProgress(); CT.toast(t('progress_reset')); UI.render(); });
    });
    actions.appendChild(exportBtn); actions.appendChild(reset);
    root.appendChild(actions);
    return root;
  };

  function ruleMatches(item, group, needle) {
    if (!needle) return true;
    var hay = [item.name.ru, item.name.en, item.summary.ru, item.summary.en, group.ru, group.en].concat(item.examples || [])
      .join(' ').toLowerCase();
    return hay.indexOf(needle) >= 0;
  }

  UI.ruleRow = function (item) {
    var row = el('button', { class: 'rule-row theory-trigger rule-link', type: 'button', 'data-lesson': item.rule,
      'aria-haspopup': 'dialog', title: t('theory_open') });
    row.appendChild(el('span', { class: 'rule-name', text: I.pick(item.name) }));
    row.appendChild(el('span', { class: 'rule-summary', text: I.pick(item.summary) }));
    if ((item.examples || []).length) row.appendChild(ru(el('span', { class: 'rule-examples muted small', text: item.examples.join(' · ') })));
    row.appendChild(el('span', { class: 'theory-arrow', text: '›', 'aria-hidden': 'true' }));
    row.addEventListener('click', function () { row.focus(); UI.openRules([item.rule]); });
    return row;
  };

  /** «Правила»: the searchable reference of all rule cards. */
  SCREENS['#/rules'] = function () {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('nav_rules') }));
    root.appendChild(el('p', { class: 'muted', text: t('rules_intro') }));
    var search = el('input', { class: 'answer-input', type: 'search', placeholder: t('search_rule'), 'aria-label': t('search_rule'),
      autocomplete: 'off', spellcheck: 'false' });
    root.appendChild(search);
    var list = el('div', { class: 'rule-list' });
    var render = function (query) {
      clear(list);
      var needle = String(query || '').trim().toLowerCase();
      C.rules.forEach(function (group) {
        var items = group.items.filter(function (item) { return ruleMatches(item, group, needle); });
        if (!items.length) return;
        var card = el('div', { class: 'card rule-group', 'data-group': group.id });
        card.appendChild(el('h3', { class: 'rule-group-title', text: I.pick(group) }));
        items.forEach(function (item) { card.appendChild(UI.ruleRow(item)); });
        list.appendChild(card);
      });
      if (!list.firstChild) list.appendChild(el('p', { class: 'muted', text: t('nothing_found') }));
    };
    search.addEventListener('input', function () { render(search.value); });
    render('');
    root.appendChild(list);
    return root;
  };
  SCREENS['#/formulas'] = SCREENS['#/rules'];

  /** Инструменты: черновик, поиск правил, памятки, сетка заданий. */
  var TOOLS = {
    open: function (name, task) {
      if (name === 'scratch') TOOLS.scratchpad(task);
      else if (name === 'memos') TOOLS.memos();
      else TOOLS.rules('', {});
    },
    rules: function (query, options) {
      options = options || {};
      var wrap = el('div', {});
      var search = el('input', { class: 'answer-input', type: 'search', placeholder: t('search_rule'), value: query || '',
        'aria-label': t('search_rule'), autocomplete: 'off', spellcheck: 'false' });
      var list = el('div', { class: 'rule-list compact' });
      var render = function (value) {
        clear(list);
        var needle = String(value || '').trim().toLowerCase();
        C.rules.forEach(function (group) {
          group.items.filter(function (item) { return ruleMatches(item, group, needle); }).forEach(function (item) {
            list.appendChild(UI.ruleRow(item));
          });
        });
        if (!list.firstChild) list.appendChild(el('p', { class: 'muted', text: t('nothing_found') }));
      };
      search.addEventListener('input', function () { render(search.value); });
      wrap.appendChild(search);
      wrap.appendChild(list);
      render(search.value);
      UI.modal(t('tool_rules'), wrap, { tall: true, keepHistory: !!options.keepHistory, language: true,
        refresh: function () { TOOLS.rules(search.value, { keepHistory: true }); } });
    },
    memos: function () {
      var wrap = el('div', { class: 'memos' });
      C.memos.forEach(function (memo) {
        var card = el('div', { class: 'memo', 'data-memo': memo.id });
        card.appendChild(el('h4', { text: I.pick(memo.title) }));
        var list = ru(el('ul', { class: 'memo-list' }));
        memo.items.forEach(function (item) { list.appendChild(el('li', { text: item })); });
        card.appendChild(list);
        wrap.appendChild(card);
      });
      UI.modal(t('tool_memos'), wrap, { tall: true, language: true, refresh: function () { TOOLS.memos(); } });
    },
    scratchpad: function (task) {
      var wrap = el('div', {});
      var area = el('textarea', { class: 'scratch', rows: 12, lang: 'ru', spellcheck: 'false', placeholder: t('scratch_placeholder') });
      area.value = (S.progress.scratch && task && S.progress.scratch[task.id]) || '';
      var save = function () {
        S.progress.scratch = S.progress.scratch || {};
        S.progress.scratch[task && task.id || '_'] = area.value;
        S.saveProgress();
      };
      area.addEventListener('input', save);
      wrap.appendChild(area);
      var row = el('div', { class: 'rowline wrap' });
      ['ё', 'Ё', '«', '»', '—', ACUTE].forEach(function (symbol) {
        var btn = el('button', { class: 'btn small', type: 'button', text: symbol === ACUTE ? 'а́' : symbol,
          'aria-label': symbol === ACUTE ? t('insert_stress') : symbol });
        btn.addEventListener('click', function () {
          var start = area.selectionStart === undefined ? area.value.length : area.selectionStart;
          area.value = area.value.slice(0, start) + symbol + area.value.slice(start);
          area.selectionStart = area.selectionEnd = start + symbol.length;
          save();
          area.focus();
        });
        row.appendChild(btn);
      });
      var clearBtn = el('button', { class: 'btn ghost', type: 'button', text: t('clear') });
      clearBtn.addEventListener('click', function () { area.value = ''; save(); });
      row.appendChild(clearBtn);
      wrap.appendChild(row);
      UI.modal(t('tool_scratch'), wrap, { tall: true });
      area.focus();
    },
    taskGrid: function () {
      var run = S.session;
      if (!run) return;
      var wrap = el('div', {});
      wrap.appendChild(el('p', { class: 'muted small', text: t('task_grid_help') }));
      var grid = el('div', { class: 'task-grid' });
      run.order.forEach(function (id, index) {
        var task = C.taskById(id);
        var answered = String(run.answers[id] === undefined ? '' : run.answers[id]).trim() !== '';
        var state = answered ? (run.mode === 'exam' ? 'answered' : (run.checked[id] === undefined ? 'answered' : (run.checked[id] ? 'good' : 'bad'))) : '';
        var btn = el('button', { class: 'grid-cell ' + state + (index === run.index ? ' current' : '') +
          (run.marked.indexOf(id) >= 0 ? ' marked' : ''), type: 'button', text: task && task.kind === 'variant' ? badge(task) : String(index + 1) });
        btn.addEventListener('click', function () { RUN.jump(index); UI.closeModal(); UI.render(); });
        if (!task) btn.disabled = true;
        grid.appendChild(btn);
      });
      wrap.appendChild(grid);
      var row = el('div', { class: 'rowline' });
      var finish = el('button', { class: 'btn primary', type: 'button', text: t('finish_test') });
      finish.addEventListener('click', function () {
        UI.closeModal();
        UI.confirm(t('finish_confirm'), function () { var attempt = RUN.finish(); go('#/result/' + (attempt ? attempt.id : '')); }, t('finish_test'));
      });
      row.appendChild(finish);
      wrap.appendChild(row);
      UI.modal(t('task_grid'), wrap, { wide: true });
    },
  };
  CT.tools = TOOLS;

  /** A self-contained HTML report (saved into the app's own reports folder). */
  function exportReport(attempt) {
    var totals = AN.totals(S.progress);
    var stats = AN.topicStats(S.progress);
    var rows = C.order.filter(function (topic) { return stats[topic]; }).map(function (topic) {
      return '<tr><td>' + esc(C.topicTitle(topic)) + '</td><td>' + stats[topic].correct + ' / ' + stats[topic].total +
        '</td><td>' + Math.round(stats[topic].rate * 100) + '%</td></tr>';
    }).join('');
    var ruleRows = AN.weakRules(S.progress, 10).map(function (item) {
      return '<tr><td>' + esc(C.ruleTitle(item.rule)) + '</td><td>' + Math.round(item.rate * 100) + '%</td><td>' + item.total + '</td></tr>';
    }).join('');
    var attempts = (S.progress.attempts || []).map(function (item) {
      var summary = AN.attemptSummary(item);
      return '<tr><td>' + esc(item.title) + '</td><td>' + esc(U.formatDate(item.finishedAt, I.lang)) +
        '</td><td>' + summary.correct + ' / ' + summary.total + '</td><td>' + esc(U.duration(item.seconds, I.lang)) + '</td></tr>';
    }).join('');
    var mistakes = attempt ? RUN.wrongResults(attempt).map(function (result) {
      var task = C.taskById(result.taskId);
      return '<li><b>' + esc(badge(task)) + '. ' + esc(I.pick(task.instruction)) + '</b><br>' +
        esc(t('your_answer')) + ': ' + esc(A.formatUser(result.user, task) || '—') + ' · ' + esc(t('correct_answer')) + ': ' +
        '<span lang="ru">' + esc(A.display(task.check)) + '</span><br>' + esc(t('report_rules')) + ': ' +
        esc(C.rulesFor(task, result.user).map(function (rule) { return C.ruleTitle(rule); }).join('; ')) + '</li>';
    }).join('') : '';
    var html = '<!DOCTYPE html><html lang="' + I.lang + '"><head><meta charset="utf-8">' +
      '<title>' + esc(t('report_title')) + '</title><style>' +
      'body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:32px;color:#1c2330}' +
      'h1{font-size:22px}h2{font-size:17px;margin-top:26px}table{border-collapse:collapse;width:100%;margin-top:8px}' +
      'th,td{border:1px solid #ccd3de;padding:6px 8px;text-align:left;font-size:14px}' +
      'th{background:#eef2f8}.muted{color:#5b6472}.total{font-size:15px}li{margin:8px 0}</style></head><body>' +
      '<h1>' + esc(t('report_title')) + '</h1>' +
      '<p class="muted">' + esc(t('app_name')) + ' · ' + esc(U.formatDate(new Date().toISOString(), I.lang)) + '</p>' +
      '<p class="total"><b>' + esc(t('stat_tests')) + ':</b> ' + totals.tests + ' · <b>' + esc(t('stat_tasks')) + ':</b> ' + totals.tasks +
      ' · <b>' + esc(t('stat_accuracy')) + ':</b> ' + Math.round(totals.accuracy * 100) + '% · <b>' + esc(t('stat_time')) + ':</b> ' +
      totals.minutes + ' ' + esc(t('minutes_short')) + '</p>' +
      (rows ? '<h2>' + esc(t('by_topic')) + '</h2><table><tr><th>' + esc(t('topic')) + '</th><th>' + esc(t('correct_col')) + '</th><th>' +
        esc(t('percent_col')) + '</th></tr>' + rows + '</table>' : '') +
      (ruleRows ? '<h2>' + esc(t('weak_rules')) + '</h2><table><tr><th>' + esc(t('rule_col')) + '</th><th>' + esc(t('percent_col')) +
        '</th><th>' + esc(t('tasks_col')) + '</th></tr>' + ruleRows + '</table>' : '') +
      (attempts ? '<h2>' + esc(t('last_attempts')) + '</h2><table><tr><th>' + esc(t('variant_col')) + '</th><th>' + esc(t('date_col')) +
        '</th><th>' + esc(t('correct_col')) + '</th><th>' + esc(t('time_col')) + '</th></tr>' + attempts + '</table>' : '') +
      (mistakes ? '<h2>' + esc(t('mistakes_title')) + '</h2><ul>' + mistakes + '</ul>' : '') +
      '<p class="muted">' + esc(I.pick(C.disclaimer)) + '</p>' +
      '<p class="muted">' + esc(t('developer')) + ': ' + esc(t('developer_name')) + ' · ziv@csl.by · +3753371412</p></body></html>';
    B.saveReport('russian-progress', html).then(function (result) {
      CT.toast(result && result.path ? t('report_saved_fmt', result.path) : t('report_saved'));
    }).catch(function () { CT.toast(t('report_failed')); });
  }

  /* ------------------------------------------------------------------ *
   * 5. Настройки и «О программе»
   * ------------------------------------------------------------------ */
  function updateCheck(button, info) {
    button.disabled = true;
    info.textContent = t('checking_updates');
    return B.checkUpdates(S.settings.baseUrl, C.meta.contentVersion).then(function (result) {
      button.disabled = false;
      var ok = result && (result.status === 'updated' || result.status === 'ok');
      info.textContent = result && result.status === 'uptodate' ? t('update_uptodate')
        : (ok ? t('update_success_fmt', result.version) : t('update_failed'));
      var message = info.textContent;
      if (ok) return C.load().then(function () { UI.render(); CT.toast(message); });
      CT.toast(message);
      return null;
    }).catch(function () {
      button.disabled = false;
      info.textContent = t('update_failed');
      CT.toast(t('update_failed'));
    });
  }

  SCREENS['#/settings'] = function () {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('nav_settings') }));
    var languageCard = el('div', { class: 'card' });
    languageCard.appendChild(el('h3', { text: t('language') }));
    var row = el('div', { class: 'rowline wrap' });
    [['ru', 'Русский'], ['en', 'English']].forEach(function (pair) {
      var btn = el('button', { class: 'btn' + (S.settings.lang === pair[0] ? ' primary' : ''), type: 'button', text: pair[1] });
      btn.addEventListener('click', function () { UI.changeLanguage(pair[0]); });
      row.appendChild(btn);
    });
    languageCard.appendChild(row);
    languageCard.appendChild(el('p', { class: 'muted small', text: t('language_hint') }));
    root.appendChild(languageCard);
    var examCard = el('div', { class: 'card' });
    examCard.appendChild(el('h3', { text: t('exam_settings') }));
    var minutesLabel = el('label', { class: 'field' }, [el('span', { text: t('exam_minutes') })]);
    var minutes = el('input', { class: 'answer-input', type: 'number', min: 10, max: 300, value: S.settings.examMinutes });
    minutes.addEventListener('change', function () {
      S.settings.examMinutes = U.clamp(parseInt(minutes.value, 10) || 120, 10, 300);
      S.saveSettings(true);
    });
    minutesLabel.appendChild(minutes);
    examCard.appendChild(minutesLabel);
    var goalLabel = el('label', { class: 'field' }, [el('span', { text: t('daily_goal') })]);
    var goal = el('input', { class: 'answer-input', type: 'number', min: 5, max: 200, value: S.settings.dailyGoal });
    goal.addEventListener('change', function () {
      S.settings.dailyGoal = U.clamp(parseInt(goal.value, 10) || 20, 5, 200);
      S.saveSettings(true);
    });
    goalLabel.appendChild(goal);
    examCard.appendChild(goalLabel);
    root.appendChild(examCard);
    var lookCard = el('div', { class: 'card' });
    lookCard.appendChild(el('h3', { text: t('theme') }));
    var themeRow = el('div', { class: 'rowline wrap' });
    [['system', t('theme_system')], ['light', t('theme_light')], ['dark', t('theme_dark')]].forEach(function (pair) {
      var btn = el('button', { class: 'btn' + (S.settings.theme === pair[0] ? ' primary' : ''), type: 'button', text: pair[1] });
      btn.addEventListener('click', function () { S.settings.theme = pair[0]; S.saveSettings(true); UI.applyAppearance(); UI.render(); });
      themeRow.appendChild(btn);
    });
    lookCard.appendChild(themeRow);
    lookCard.appendChild(el('h3', { text: t('font_size') }));
    var fontRow = el('div', { class: 'rowline wrap' });
    [['font_small', 0.9], ['font_normal', 1], ['font_large', 1.15], ['font_huge', 1.3]].forEach(function (pair) {
      var btn = el('button', { class: 'btn' + (S.settings.fontScale === pair[1] ? ' primary' : ''), type: 'button', text: t(pair[0]) });
      btn.addEventListener('click', function () { S.settings.fontScale = pair[1]; S.saveSettings(true); UI.applyAppearance(); UI.render(); });
      fontRow.appendChild(btn);
    });
    lookCard.appendChild(fontRow);
    root.appendChild(lookCard);
    var switchCard = el('div', { class: 'card' });
    switchCard.appendChild(el('h3', { text: t('interface_settings') }));
    [['autoAdvance', t('auto_advance'), t('auto_advance_hint')], ['vibrate', t('vibration'), ''],
     ['keepScreenOn', t('keep_screen_on'), ''], ['autoUpdate', t('auto_update'), t('auto_update_hint')]].forEach(function (entry) {
      var label = el('label', { class: 'switch' });
      var input = el('input', { type: 'checkbox' });
      input.checked = !!S.settings[entry[0]];
      input.addEventListener('change', function () { S.settings[entry[0]] = input.checked; S.saveSettings(true); });
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
    var openData = el('button', { class: 'btn ghost', type: 'button', text: t('open_data_folder') });
    openData.addEventListener('click', function () {
      B.openFolder('data').then(function () { CT.toast(t('opened_folder')); }).catch(function () { CT.toast(t('open_folder_failed')); });
    });
    var exportBtn = el('button', { class: 'btn ghost', type: 'button', text: t('export_report') });
    exportBtn.addEventListener('click', function () { exportReport(null); });
    dataRow.appendChild(openData); dataRow.appendChild(exportBtn);
    dataCard.appendChild(dataRow);
    root.appendChild(dataCard);
    var updates = el('div', { class: 'card' });
    var update = el('button', { class: 'btn', type: 'button', text: t('check_updates') });
    var updateInfo = el('p', { class: 'muted small' });
    update.addEventListener('click', function () { updateCheck(update, updateInfo); });
    updates.appendChild(el('h3', { text: t('updates') }));
    updates.appendChild(el('p', { class: 'muted small', text: t('updates_channel') }));
    updates.appendChild(update);
    updates.appendChild(updateInfo);
    updates.appendChild(el('p', { class: 'muted small', text: t('content_version_fmt', C.meta.contentVersion || '—') }));
    root.appendChild(updates);
    return root;
  };

  SCREENS['#/about'] = function () {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('about_title') }));
    var card = el('div', { class: 'card' });
    card.appendChild(el('p', { text: t('about_text') }));
    var spec = C.specification || {};
    card.appendChild(el('p', { class: 'muted small', text: t('about_spec_fmt', I.pick(spec.title) || '', spec.checked || '') }));
    card.appendChild(el('p', { class: 'muted small', text: I.pick(C.disclaimer) }));
    card.appendChild(el('h3', { text: t('developer') }));
    var contacts = el('div', { class: 'contacts' });
    contacts.appendChild(el('p', { class: 'big', text: t('developer_name') }));
    var links = [el('a', { class: 'btn', href: 'mailto:ziv@csl.by?subject=' + encodeURIComponent(t('feedback_subject')), text: 'ziv@csl.by' }),
      el('a', { class: 'btn', href: 'tel:+3753371412', text: '+375 33 714 12' }),
      el('a', { class: 'btn ghost', href: 'https://wa.me/3753371412', text: 'WhatsApp' }),
      el('a', { class: 'btn ghost', href: C.meta.repo || 'https://github.com/zigorminsk-debug/mathematics', text: t('source_code') })];
    links.forEach(function (link) {
      link.addEventListener('click', function (event) { event.preventDefault(); B.openExternal(link.getAttribute('href')); });
      contacts.appendChild(link);
    });
    contacts.appendChild(el('p', { class: 'muted small', text: t('contacts_hint') }));
    card.appendChild(contacts);
    card.appendChild(el('p', { class: 'muted small', text: t('version_fmt', B.info.version || '—', C.meta.contentVersion || '—') }));
    root.appendChild(card);
    return root;
  };

  SCREENS['#/tools'] = function () {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('nav_tools') }));
    root.appendChild(el('p', { class: 'muted', text: t('tools_intro') }));
    var grid = el('div', { class: 'grid-3' });
    [['rules', t('tool_rules'), '📘'], ['memos', t('tool_memos'), '🗒️'], ['scratch', t('tool_scratch'), '📝']].forEach(function (entry) {
      var btn = el('button', { class: 'btn big tool-btn', type: 'button', 'data-tool': entry[0] });
      btn.appendChild(el('span', { class: 'tool-icon', text: entry[2], 'aria-hidden': 'true' }));
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
    ['#/home', 'nav_home', '🏠'], ['#/tests', 'nav_tests', '📚'], ['#/practice', 'nav_practice', '🔁'],
    ['#/study', 'nav_study', '📖'], ['#/rules', 'nav_rules', '📘'], ['#/stats', 'nav_stats', '📊'],
    ['#/tools', 'nav_tools', '🧰'], ['#/about', 'nav_about', 'ℹ️'],
  ];

  UI.renderNav = function () {
    var nav = $('#mainnav');
    if (!nav) return;
    clear(nav);
    var current = parseHash().name;
    NAV.forEach(function (entry) {
      var link = el('a', { href: entry[0], class: 'nav-link' + (entry[0] === current ? ' active' : ''),
        'aria-current': entry[0] === current ? 'page' : null });
      link.appendChild(el('span', { class: 'nav-icon', text: entry[2], 'aria-hidden': 'true' }));
      link.appendChild(el('span', { text: t(entry[1]) }));
      nav.appendChild(link);
    });
  };

  function parseHash() {
    var raw = String(global.location.hash || '#/home').replace(/^#\/?/, '');
    var parts = raw.split('/').filter(function (piece) { return piece !== ''; });
    if (!parts.length) return { name: '#/home', extra: null };
    return { name: '#/' + parts[0], extra: parts.slice(1).join('/') || null };
  }

  UI.render = function () {
    var route = parseHash();
    var screen = SCREENS[route.name] || SCREENS['#/home'];
    var view = $('#view');
    clear(view);
    if (!C.loaded) {
      view.appendChild(el('div', { class: 'card' }, [el('p', { class: 'banner bad', text: t('content_unavailable') })]));
      UI.renderNav();
      return;
    }
    try {
      view.appendChild(screen(route.extra));
    } catch (error) {
      if (global.console) global.console.error(error);
      view.appendChild(el('div', { class: 'card' }, [el('p', { class: 'banner bad', text: t('error_generic') }),
        el('pre', { class: 'small', text: String(error && error.message || error) })]));
    }
    view.scrollTop = 0;
    UI.renderNav();
    UI.chrome();
  };
  CT.render = UI.render;

  CT.onAndroidBack = function () {
    if ($('#modal').classList.contains('open')) { UI.backModal(); return null; }
    var route = parseHash();
    if (route.name === '#/home') return 'exit';
    if (route.name === '#/study' && route.extra) { go(S.session && !S.session.finished ? '#/run' : '#/study'); return null; }
    var parent = { '#/run': '#/tests', '#/result': '#/home', '#/mistakes': '#/home', '#/study': '#/home',
      '#/settings': '#/home', '#/about': '#/home', '#/rules': '#/home' }[route.name];
    go(parent || '#/home');
    return null;
  };

  var booted = false;
  CT.boot = function () {
    if (booted) return Promise.resolve(true);
    booted = true;
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
        var folder = $('#app-folder');
        if (folder) folder.textContent = B.info.dataDir || '';
      });
      UI.chrome();
      UI.render();
      if (S.settings.autoUpdate && C.loaded) {
        B.checkUpdates(S.settings.baseUrl, C.meta.contentVersion).then(function (result) {
          var updated = result && (result.status === 'updated' || result.status === 'ok');
          if (updated && result.version && result.version !== C.meta.contentVersion) {
            return C.load().then(function () {
              if (parseHash().name !== '#/run') UI.render();
              CT.toast(t('update_success_fmt', result.version));
            });
          }
          return null;
        }).catch(function () { /* offline: the embedded bank keeps working */ });
      }
      return true;
    });
  };

  global.addEventListener('hashchange', UI.render);
  doc.addEventListener('DOMContentLoaded', function () { CT.boot(); });
  if (doc.readyState !== 'loading') CT.boot();
})(typeof globalThis !== 'undefined' ? globalThis : this);

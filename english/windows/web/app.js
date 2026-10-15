/* app.js — экраны приложения «Репетитор ЦТ: Английский язык».
 *
 * Один и тот же код работает в Android WebView и в окне Windows: слой платформы
 * скрыт в CT.bridge (core.js). Здесь только интерфейс: главная, вариант ЦТ
 * (18 заданий части А + 22 части В, 120 минут), тренировка по темам, разбор
 * ошибок с правилом и уроком, справочник правил со схемами, статистика,
 * настройки и «О программе» с кликабельными контактами разработчика.
 *
 * Проверяемый английский текст не переводится вместе с интерфейсом: языковой
 * переключатель меняет подписи, инструкции и пояснения, но сами предложения,
 * варианты и ответы остаются английскими.
 *
 * Screens of the app; platform access always goes through CT.bridge.
 */
(function (global) {
  'use strict';

  var doc = global.document;
  var CT = global.CT;
  var U = CT.util, I = CT.i18n, B = CT.bridge, C = CT.content, A = CT.answer, AN = CT.analytics;

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
      if (child === null || child === undefined || child === false) return;
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
    lang: 'ru', theme: 'system', fontScale: 1, examMinutes: 120, dailyGoal: 20,
    autoAdvance: true, sound: true, vibrate: true, autoUpdate: true, baseUrl: '',
    keepScreenOn: true,
  };

  var S = CT.store = {
    settings: Object.assign({}, DEFAULT_SETTINGS),
    progress: AN.empty(),
    session: null,
    _timer: null,

    /** Загрузить настройки, прогресс и незаконченный вариант. */
    load: function () {
      var self = this;
      var read = function (key) {
        return B.loadBlob(key).catch(function () { return null; });
      };
      return Promise.all([read('settings'), read('progress'), read('session')]).then(function (data) {
        if (data[0]) self.settings = Object.assign({}, DEFAULT_SETTINGS, data[0]);
        if (data[1]) self.progress = Object.assign(AN.empty(), data[1]);
        self.settings.lang = I.setLang(self.settings.lang) === 'en' ? 'en' : 'ru';
        self.progress.streak = AN.computeStreak(self.progress);
        if (data[2] && data[2].tasks && data[2].tasks.length) self.session = data[2];
        return self;
      });
    },
    save: function (immediate) {
      var self = this;
      if (this._timer) global.clearTimeout(this._timer);
      var write = function () {
        B.saveBlob('settings', JSON.stringify(self.settings));
        B.saveBlob('progress', JSON.stringify(self.progress));
      };
      if (immediate) { write(); return Promise.resolve(); }
      return new Promise(function (resolve) {
        self._timer = global.setTimeout(function () { write(); resolve(); }, 400);
      });
    },
    saveSession: function (immediate) {
      var self = this;
      if (this.session === null) {
        return immediate ? B.saveBlob('session', 'null') : Promise.resolve();
      }
      var write = function () { B.saveBlob('session', JSON.stringify(self.session)); };
      if (immediate) { write(); return Promise.resolve(); }
      return new Promise(function (resolve) {
        self._sessionTimer = global.setTimeout(function () { write(); resolve(); }, 400);
      });
    },
    resetProgress: function () {
      this.progress = AN.empty();
      this.progress.goal = this.settings.dailyGoal;
      this.session = null;
      return this.save(true).then(function () { return S.saveSession(true); });
    },
  };

  /* ------------------------------------------------------------------ *
   * 2. Ход прогона / run model
   *
   * Прогон — это либо вариант целиком (18 А + 22 В, 120 минут), либо набор по
   * темам, либо работа над ошибками.  Модель одна, отличается только источник
   * заданий и наличие таймера.
   * ------------------------------------------------------------------ */
  var RUN = {};

  /** Задания варианта нужного года, по порядку частей и номеров. */
  RUN.variantTasks = function (year) {
    return C.bank.filter(function (task) { return task.year === Number(year); })
      .sort(function (a, b) {
        if (a.part !== b.part) return a.part === 'A' ? -1 : 1;
        return a.n - b.n;
      });
  };

  /** Набор по темам: задания банка + однотипные, вперемешку по темам. */
  RUN.topicTasks = function (topics, limit) {
    var picked = [];
    topics.forEach(function (topic) {
      picked = picked.concat(C.tasksByTopic(topic));
      C.analogByTopic(topic).forEach(function (task) {
        if (picked.length < (limit || 12)) picked.push(task);
      });
    });
    if (limit) picked = picked.slice(0, limit);
    return U.shuffle(picked);
  };

  /** Набор из уже решённых с ошибкой заданий: сами задания и их аналоги. */
  RUN.mistakeTasks = function (results) {
    var ids = (results || []).map(function (result) { return result.taskId; });
    var picked = ids.map(function (id) { return C.taskById(id); }).filter(Boolean);
    picked.forEach(function (task) {
      C.analogByTopic(task.topic).slice(0, 2).forEach(function (analogue) {
        if (picked.indexOf(analogue) < 0) picked.push(analogue);
      });
    });
    return picked;
  };

  RUN.start = function (options) {
    var tasks = options.tasks || [];
    if (!tasks.length) { B.notify(t('no_tasks')); return false; }
    S.session = {
      mode: options.mode || 'train',
      title: options.title || t('train'),
      year: options.year || null,
      topics: options.topics || [],
      order: tasks.map(function (task) { return task.id; }),
      index: 0,
      results: [],
      marked: [],
      startedAt: Date.now(),
      seconds: 0,
      limit: options.minutes ? options.minutes * 60 : 0,
      finished: false,
    };
    S.saveSession(true);
    // Экран не гасим только во время теста (настройка keepScreenOn).
    B.keepScreenOn(!!S.settings.keepScreenOn);
    go('#/run');
    return true;
  };

  RUN.task = function () {
    if (!S.session) return null;
    return C.taskById(S.session.order[S.session.index]);
  };

  RUN.answer = function (typed) {
    var session = S.session, task = RUN.task();
    if (!session || !task || session.finished) return null;
    var graded = A.check(task, typed);
    var previous = session.results[session.index];
    var seconds = session._taskStarted ? Math.round((Date.now() - session._taskStarted) / 1000) : 0;
    session.results[session.index] = {
      taskId: task.id, typed: String(typed === null || typed === undefined ? '' : typed),
      correct: graded.ok, reason: graded.reason, expected: graded.expected,
      topic: task.topic, part: task.part || null, seconds: seconds, checkedAt: Date.now(),
    };
    // Повторная попытка в тренировке не должна удваивать статистику.
    if (!previous) AN.record(S.progress, task, graded.ok, seconds);
    S.progress.goal = S.settings.dailyGoal;
    S.save();
    S.saveSession();
    if (graded.ok && S.settings.vibrate) B.vibrate(25);
    return graded;
  };

  RUN.mark = function (index) {
    var session = S.session;
    if (!session) return;
    var at = session.marked.indexOf(index);
    if (at < 0) session.marked.push(index); else session.marked.splice(at, 1);
    S.saveSession(true);
  };

  RUN.moveTo = function (index) {
    var session = S.session;
    if (!session) return;
    session.index = U.clamp(index, 0, session.order.length - 1);
    session._taskStarted = Date.now();
    S.saveSession(true);
    UI.render();
  };

  RUN.next = function (auto) {
    var session = S.session;
    if (!session) return;
    if (session.index >= session.order.length - 1) { RUN.finish(); return; }
    session.index += 1;
    session._taskStarted = Date.now();
    if (auto !== false) S.saveSession(true);
    UI.render();
  };

  RUN.secondsLeft = function () {
    var session = S.session;
    if (!session || !session.limit) return null;
    return Math.max(0, session.limit - Math.round((Date.now() - session.startedAt) / 1000));
  };

  RUN.finish = function () {
    var session = S.session;
    if (!session || session.finished) return;
    session.finished = true;
    session.seconds = Math.round((Date.now() - session.startedAt) / 1000);
    var attempt = {
      id: U.uid(), title: session.title, mode: session.mode, year: session.year,
      topics: session.topics, at: new Date().toISOString(), seconds: session.seconds,
      results: session.results.filter(Boolean),
    };
    S.progress.attempts = (S.progress.attempts || []).concat([attempt]).slice(-100);
    S.save(true);
    S.saveSession(true);
    B.keepScreenOn(false);
    go('#/result');
  };

  RUN.discard = function () {
    S.session = null;
    S.saveSession(true);
    B.keepScreenOn(false);
    go('#/home');
  };

  // Модель прогона доступна снаружи: её используют дымовые тесты и системная
  // кнопка «назад» на Android (возврат к незаконченному варианту).
  CT.run = RUN;

  var clock = null;
  function startClock() {
    if (clock) return;
    clock = global.setInterval(function () {
      if (!S.session || S.session.finished || !S.session.limit) return;
      var left = RUN.secondsLeft();
      var node = $('#run-clock');
      if (node) node.textContent = t('time_left_fmt', U.duration(left, I.lang));
      if (left <= 0) { global.clearInterval(clock); clock = null; B.notify(t('exam_finished')); RUN.finish(); }
    }, 1000);
  }
  function stopClock() { if (clock) { global.clearInterval(clock); clock = null; } }

  /* ------------------------------------------------------------------ *
   * 3. Общие куски интерфейса
   * ------------------------------------------------------------------ */
  var UI = {};
  CT.app = UI;

  /** Причина отказа → надпись интерфейса (литералы читает и сборка контента). */
  function reasonLabel(reason) {
    if (reason === 'ok') return t('reason_ok');
    if (reason === 'empty') return t('reason_empty');
    if (reason === 'article') return t('reason_article');
    if (reason === 'case') return t('reason_case');
    if (reason === 'apostrophe') return t('reason_apostrophe');
    if (reason === 'hyphen') return t('reason_hyphen');
    if (reason === 'space') return t('reason_space');
    if (reason === 'stress') return t('reason_stress');
    if (reason === 'near') return t('reason_near');
    return t('reason_exact');
  }

  UI.toast = function (message) {
    var node = $('#toast');
    if (!node) return;
    node.textContent = message;
    node.classList.add('open');
    global.setTimeout(function () { node.classList.remove('open'); }, 2600);
  };

  UI.bindChrome = function () {
    var lang = $('#lang-toggle');
    if (lang) lang.addEventListener('click', function () {
      UI.changeLanguage(I.lang === 'ru' ? 'en' : 'ru');
    });
    var settings = $('#btn-settings');
    if (settings) settings.addEventListener('click', function () { go('#/settings'); });
  };

  UI.changeLanguage = function (lang) {
    S.settings.lang = I.setLang(lang);
    S.save();
    UI.render();
  };

  UI.applyAppearance = function () {
    var root = doc.documentElement;
    var theme = S.settings.theme || 'system';
    if (theme === 'system') root.removeAttribute('data-theme');
    else root.setAttribute('data-theme', theme);
    root.style.setProperty('--font-scale', String(S.settings.fontScale || 1));
    if (S.settings.lang === 'en') root.setAttribute('lang', 'en');
  };

  UI.chrome = function () {
    var lang = $('#lang-toggle');
    if (lang) {
      lang.textContent = I.lang === 'ru' ? 'EN' : 'RU';
      lang.setAttribute('title', t('language'));
    }
    UI.applyAppearance();
  };

  UI.modal = function (title, node, options) {
    options = options || {};
    var modal = $('#modal');
    var sheet = $('.sheet', modal);
    clear(sheet);
    var head = el('div', { class: 'sheet-head' });
    head.appendChild(el('h2', { text: title }));
    var close = el('button', { class: 'icon-btn', type: 'button', text: '✕', 'aria-label': t('close') });
    close.addEventListener('click', UI.closeModal);
    head.appendChild(close);
    sheet.appendChild(head);
    sheet.appendChild(node);
    if (options.footer) sheet.appendChild(options.footer);
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
  };

  UI.closeModal = function () {
    var modal = $('#modal');
    if (!modal) return;
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
  };

  UI.backModal = function () { UI.closeModal(); };

  UI.confirm = function (message, onYes, yesLabel) {
    var body = el('div', { class: 'confirm' });
    body.appendChild(el('p', { text: message }));
    var row = el('div', { class: 'rowline' });
    var yes = el('button', { class: 'btn primary', type: 'button', text: yesLabel || t('check') });
    yes.addEventListener('click', function () { UI.closeModal(); onYes(); });
    var no = el('button', { class: 'btn ghost', type: 'button', text: t('close') });
    no.addEventListener('click', UI.closeModal);
    row.appendChild(yes); row.appendChild(no);
    body.appendChild(row);
    UI.modal(t('settings'), body);
  };

  /** Полоски с процентами (темы, годы). */
  UI.bars = function (items) {
    var wrap = el('div', { class: 'bars' });
    items.forEach(function (item) {
      var row = el('button', { class: 'bar-row', type: 'button' });
      row.appendChild(el('span', { class: 'bar-label', text: item.label }));
      var track = el('span', { class: 'bar-track' });
      var fill = el('span', { class: 'bar-fill' });
      fill.style.width = U.clamp(item.value, 0, 100) + '%';
      if (item.color) fill.style.background = item.color;
      track.appendChild(fill);
      row.appendChild(track);
      row.appendChild(el('span', { class: 'bar-value', text: item.text }));
      if (item.action) row.addEventListener('click', item.action);
      wrap.appendChild(row);
    });
    return wrap;
  };

  /* --- схемы: узлы и связи авторского формата --------------------------- */

  /** Схема из узлов и связей (типы tree | timeline | flow). */
  UI.diagramSvg = function (figure) {
    var NS = 'http://www.w3.org/2000/svg';
    if (!figure || !Array.isArray(figure.nodes) || figure.nodes.length < 2 ||
        !Array.isArray(figure.edges) || !figure.edges.length) return null;
    var byId = {};
    figure.nodes.forEach(function (node) { byId[node.id] = node; });
    var svg = doc.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + figure.width + ' ' + figure.height);
    svg.setAttribute('class', 'diagram-svg diagram-' + figure.kind);
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', I.pick(figure.title) + '. ' + I.pick(figure.caption));
    svg.setAttribute('data-figure', figure.id);
    var title = doc.createElementNS(NS, 'title');
    title.textContent = I.pick(figure.title);
    var desc = doc.createElementNS(NS, 'desc');
    desc.textContent = I.pick(figure.caption);
    svg.appendChild(title); svg.appendChild(desc);
    // связи рисуем первыми, чтобы узлы их перекрывали
    figure.edges.forEach(function (edge) {
      var from = byId[edge.from], to = byId[edge.to];
      if (!from || !to) return;
      var x1 = from.x + from.w / 2, y1 = from.y + from.h / 2;
      var x2 = to.x + to.w / 2, y2 = to.y + to.h / 2;
      var line = doc.createElementNS(NS, 'line');
      line.setAttribute('x1', x1); line.setAttribute('y1', y1);
      line.setAttribute('x2', x2); line.setAttribute('y2', y2);
      line.setAttribute('class', 'diagram-edge');
      line.setAttribute('marker-end', 'url(#diagram-arrow)');
      svg.appendChild(line);
      if (edge.label) {
        var label = doc.createElementNS(NS, 'text');
        label.setAttribute('x', (x1 + x2) / 2);
        label.setAttribute('y', (y1 + y2) / 2 - 4);
        label.setAttribute('class', 'diagram-edge-label');
        label.setAttribute('text-anchor', 'middle');
        label.textContent = I.pick(edge.label);
        svg.appendChild(label);
      }
    });
    var defs = doc.createElementNS(NS, 'defs');
    defs.innerHTML = '<marker id="diagram-arrow" viewBox="0 0 10 10" refX="9" refY="5" ' +
      'markerWidth="5" markerHeight="5" orient="auto-start-reverse">' +
      '<path d="M 0 0 L 10 5 L 0 10 z" class="diagram-arrow"/></marker>';
    svg.appendChild(defs);
    figure.nodes.forEach(function (node) {
      var rect = doc.createElementNS(NS, 'rect');
      rect.setAttribute('x', node.x); rect.setAttribute('y', node.y);
      rect.setAttribute('width', node.w); rect.setAttribute('height', node.h);
      rect.setAttribute('rx', 8);
      rect.setAttribute('class', 'diagram-node diagram-' + node.role);
      svg.appendChild(rect);
      var lines = I.pick(node.label).split('\n');
      var text = doc.createElementNS(NS, 'text');
      text.setAttribute('x', node.x + node.w / 2);
      text.setAttribute('y', node.y + node.h / 2 - (lines.length - 1) * 7 + 5);
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('class', 'diagram-label');
      lines.forEach(function (line, index) {
        var span = doc.createElementNS(NS, 'tspan');
        span.setAttribute('x', node.x + node.w / 2);
        span.setAttribute('dy', index === 0 ? 0 : 15);
        span.textContent = line;
        text.appendChild(span);
      });
      svg.appendChild(text);
    });
    return svg;
  };

  UI.diagramCard = function (figure) {
    var block = el('figure', { class: 'theory-figure', 'data-figure': figure.id });
    block.appendChild(el('h4', { text: I.pick(figure.title) }));
    var svg = UI.diagramSvg(figure);
    block.appendChild(svg || el('p', { class: 'muted', text: t('theory_visual_unavailable') }));
    block.appendChild(el('figcaption', { class: 'muted small', text: I.pick(figure.caption) }));
    if (svg) {
      var zoom = el('button', { class: 'icon-btn', type: 'button', text: '🔍', 'aria-label': t('figure_zoom') });
      zoom.addEventListener('click', function () {
        var wrap = el('div', { class: 'diagram-viewport' });
        wrap.appendChild(UI.diagramSvg(figure));
        var reset = el('button', { class: 'btn', type: 'button', text: t('figure_reset') });
        reset.addEventListener('click', function () { clear(wrap); wrap.appendChild(UI.diagramSvg(figure)); });
        UI.modal(I.pick(figure.title), el('div', {}, [wrap, reset]));
      });
      block.appendChild(zoom);
    }
    return block;
  };

  /** Карточка правила из справочника. */
  UI.ruleCard = function (item, group) {
    var card = el('div', { class: 'card rule-card', 'data-rule': item.id });
    card.appendChild(el('h3', { text: I.pick(item.title) }));
    if (group) card.appendChild(el('p', { class: 'muted small', text: I.pick(group.title) }));
    var rows = [
      ['rule_formulation', item.formulation],
      ['rule_conditions', item.conditions],
      ['rule_examples', item.examples],
      ['rule_everyday', item.everyday],
    ];
    rows.forEach(function (row) {
      if (!row[1]) return;
      var block = el('div', { class: 'rule-row' });
      block.appendChild(el('span', { class: 'rule-term', text: t(row[0]) }));
      if (Array.isArray(row[1])) {
        var list = el('ul', { class: 'rule-list' });
        row[1].forEach(function (line) { list.appendChild(el('li', { text: I.pick(line) })); });
        block.appendChild(list);
      } else {
        block.appendChild(el('span', { class: 'rule-text', text: I.pick(row[1]) }));
      }
      card.appendChild(block);
    });
    var lesson = Object.keys(C.lessons).map(function (id) { return C.lessons[id]; })
      .filter(function (entry) { return entry.rule === item.id; })[0];
    if (lesson) {
      var open = el('button', { class: 'btn', type: 'button', text: t('study_example') });
      open.addEventListener('click', function () { go('#/study/' + lesson.id); });
      card.appendChild(open);
    }
    return card;
  };

  /** Что проверить в этом задании: расшифровка политики проверки. */
  UI.policyNote = function (task) {
    var policy = A.policyFor(task);
    var box = el('div', { class: 'policy-note' });
    box.appendChild(el('span', { class: 'policy-title', text: t('policy_title') }));
    box.appendChild(el('span', { text: A.describePolicy(policy) }));
    ['case', 'article', 'apostrophe', 'hyphen', 'empty'].forEach(function (key) {
      var text = { case: 'policy_case_insensitive', article: 'policy_article_ignore',
        apostrophe: 'policy_apostrophe_ignore', hyphen: 'policy_hyphen_significant',
        empty: 'policy_empty_accept' }[key];
      var on = { case: policy.case === 'insensitive', article: policy.article === 'ignored',
        apostrophe: policy.apostrophe === 'ignore', hyphen: policy.hyphen === 'significant',
        empty: policy.empty === 'accept' }[key];
      if (!on || !I.strings[text]) return;
      box.appendChild(el('span', { class: 'policy-item', text: t(text) }));
    });
    return box;
  };

  /** Разбор ответа: вердикт, причина, исправление и правило. */
  UI.breakdown = function (task, typed, graded) {
    var wrap = el('div', { class: 'breakdown' });
    var banner = el('p', { class: graded.ok ? 'banner good' : 'banner bad' });
    banner.textContent = reasonLabel(graded.ok ? 'ok' : graded.reason);
    wrap.appendChild(banner);

    if (!graded.ok) {
      wrap.appendChild(el('p', { class: 'muted small', text: t('expected_fmt', graded.expected) }));
      if (graded.reason === 'case') wrap.appendChild(el('p', { class: 'muted small', text: t('case_hint') }));
      var correction = task.correction;
      if (correction) {
        wrap.appendChild(el('h4', { text: t('correction_title') }));
        wrap.appendChild(el('p', { text: I.pick(correction) }));
      }
      wrap.appendChild(el('h4', { text: t('wrong_answer_title') }));
      C.diagnoses(task).forEach(function (diagnosis) {
        var card = el('div', { class: 'card diagnosis' });
        card.appendChild(el('strong', { text: I.pick(diagnosis.title) }));
        card.appendChild(el('p', { text: I.pick(diagnosis.why) }));
        card.appendChild(el('p', { class: 'muted', text: I.pick(diagnosis.fix) }));
        var found = C.ruleItemFor(diagnosis.rule);
        if (found.item) card.appendChild(UI.ruleCard(found.item, found.group));
        var lessons = C.lessonsForTopic(task.topic);
        lessons.forEach(function (lesson) {
          var open = el('button', { class: 'btn', type: 'button', text: t('study') + ': ' + I.pick(lesson.title) });
          open.addEventListener('click', function () { go('#/study/' + lesson.id); });
          card.appendChild(open);
        });
        wrap.appendChild(card);
      });
    } else {
      var alternatives = A.alternativesFor(task);
      if (alternatives.length > 1) {
        wrap.appendChild(el('p', { class: 'muted small', text: t('accepted_forms_fmt', alternatives.join(', ')) }));
      }
      if (task.correction) {
        wrap.appendChild(el('h4', { text: t('correction_title') }));
        wrap.appendChild(el('p', { text: I.pick(task.correction) }));
      }
    }
    wrap.appendChild(UI.policyNote(task));
    return wrap;
  };

  /** Однотипное задание из набора «закрепить». */
  UI.analogousItem = function (task, index) {
    var card = el('div', { class: 'card analogous' });
    card.appendChild(el('p', { class: 'muted small', text: t('analogous') + ' ' + t('task_fmt', index + 1) }));
    card.appendChild(el('p', { class: 'task-text', text: task.text }));
    if (task.type === 'choice') {
      var list = el('ul', { class: 'options' });
      task.options.forEach(function (option) { list.appendChild(el('li', { text: option })); });
      card.appendChild(list);
    }
    var reveal = el('button', { class: 'btn', type: 'button', text: t('check') });
    var answer = el('p', { class: 'muted', text: '' });
    reveal.addEventListener('click', function () {
      var line = (A.alternativesFor(task).length ? A.alternativesFor(task) : [task.answer.value]);
      answer.textContent = t('expected_fmt', task.answer.value) +
        (line.length > 1 ? ' · ' + t('accepted_forms_fmt', line.join(', ')) : '');
    });
    card.appendChild(reveal);
    card.appendChild(answer);
    return card;
  };

  /** Экран задания: текст, варианты или поле ввода, подсказки, разбор. */
  UI.taskCard = function (task, options) {
    options = options || {};
    var card = el('div', { class: 'card task-card' });
    card.appendChild(el('p', { class: 'muted small', text: t('instruction_label') + ': ' + I.pick(C.instructionFor(task)) }));
    card.appendChild(el('p', { class: 'task-text', text: task.text }));
    var feedback = el('div', {});
    var state = { graded: options.result ? { ok: options.result.correct, reason: options.result.reason, expected: options.result.expected } : null };

    var showResult = function (graded, typed) {
      clear(feedback);
      if (options.reveal === false) {
        // Вариант целиком: правильность и разбор не показываются до завершения,
        // иначе теряется смысл экзамена.
        feedback.appendChild(el('p', { class: 'banner info', text: t('answer_saved') }));
        return;
      }
      feedback.appendChild(UI.breakdown(task, typed, graded));
      var analogues = options.analogous === false ? [] : C.analogByTopic(task.topic).slice(0, 2);
      if (!graded.ok && analogues.length) {
        var box = el('div', { class: 'analogous-box' });
        box.appendChild(el('h4', { text: t('analogous') }));
        box.appendChild(el('p', { class: 'muted small', text: t('analogous_hint') }));
        analogues.forEach(function (item, index) { box.appendChild(UI.analogousItem(item, index)); });
        feedback.appendChild(box);
      }
    };

    if (task.type === 'choice') {
      var list = el('div', { class: 'choices' });
      task.options.forEach(function (option) {
        var button = el('button', { class: 'choice', type: 'button' });
        button.appendChild(el('span', { class: 'choice-mark', text: '' }));
        button.appendChild(el('span', { text: option }));
        button.addEventListener('click', function () {
          if (state.graded) return;
          var graded = options.onAnswer ? options.onAnswer(option) : A.check(task, option);
          state.graded = graded;
          button.classList.add(graded.ok ? 'correct' : 'wrong');
          if (!graded.ok && options.reveal !== false) {
            $$('.choice', list).forEach(function (node) {
              if (node.textContent.indexOf(graded.expected) >= 0) node.classList.add('correct');
            });
          }
          showResult(graded, option);
          if (options.onGraded) options.onGraded(graded);
        });
        list.appendChild(button);
      });
      card.appendChild(list);
    } else {
      var form = el('div', { class: 'answer-row' });
      var input = el('input', { type: 'text', class: 'answer-input', autocomplete: 'off',
        autocapitalize: 'off', spellcheck: 'false', placeholder: t('answer_hint'),
        'aria-label': t('answer_hint'), value: (options.result && options.result.typed) || '' });
      var given = task.given || (task.answer && task.answer.given);
      if (given && I.strings.given_word) {
        form.appendChild(el('span', { class: 'given-word', text: t('given_word') + ': ' + I.pick(given) }));
      }
      form.appendChild(input);
      var check = el('button', { class: 'btn primary', type: 'button', text: t('check') });
      var submit = function () {
        if (state.graded) return;
        var typed = input.value;
        var graded = options.onAnswer ? options.onAnswer(typed) : A.check(task, typed);
        state.graded = graded;
        input.classList.add(graded.ok ? 'correct' : 'wrong');
        input.disabled = true;
        showResult(graded, typed);
        if (options.onGraded) options.onGraded(graded);
      };
      check.addEventListener('click', submit);
      input.addEventListener('keydown', function (event) { if (event.key === 'Enter') submit(); });
      form.appendChild(check);
      card.appendChild(form);
      card.appendChild(el('p', { class: 'muted small', text: t('answer_word_hint') }));
      card.appendChild(el('p', { class: 'muted small', text: t('autocheck_hint') }));
    }

    if (options.result) showResult(state.graded, options.result.typed);
    card.appendChild(feedback);
    return card;
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
      '<button class="btn primary" data-go="#/tests">' + esc(t('exam')) + '</button>' +
      '<button class="btn" data-go="#/practice">' + esc(t('train')) + '</button>' +
      '<button class="btn" data-go="#/study">' + esc(t('rules')) + '</button>' +
      '</div></div>'));

    var cards = el('div', { class: 'grid-4' });
    cards.appendChild(h('<div class="card stat"><div class="stat-value">' + totals.tasks + '</div><div class="muted">' + esc(t('stat_total_fmt', totals.tasks)) + '</div></div>'));
    cards.appendChild(h('<div class="card stat"><div class="stat-value">' + Math.round(totals.accuracy * 100) + '%</div><div class="muted">' + esc(t('stat_correct_fmt', Math.round(totals.accuracy * 100))) + '</div></div>'));
    cards.appendChild(h('<div class="card stat"><div class="stat-value">' + (S.progress.streak || 0) + '</div><div class="muted">' + esc(t('stat_streak_fmt', S.progress.streak || 0)) + '</div></div>'));
    cards.appendChild(h('<div class="card stat"><div class="stat-value">' + totals.minutes + '</div><div class="muted">' + esc(U.duration(totals.minutes * 60, I.lang)) + '</div></div>'));
    root.appendChild(cards);

    // день: сколько заданий сделано и сколько осталось до цели
    var goalCard = el('div', { class: 'card' });
    goalCard.appendChild(el('h3', { text: t('progress') }));
    var bar = el('div', { class: 'progress' });
    var fill = el('div', { class: 'progress-fill' });
    fill.style.width = U.clamp(today / goal * 100, 0, 100) + '%';
    bar.appendChild(fill);
    goalCard.appendChild(bar);
    goalCard.appendChild(el('p', { class: 'muted small', text: t('stat_total_fmt', today) + ' · ' + t('stat_streak_fmt', S.progress.streak || 0) }));
    root.appendChild(goalCard);

    if (S.session && !S.session.finished) {
      var resume = el('div', { class: 'card accent' });
      resume.appendChild(el('h3', { text: t('exam') }));
      resume.appendChild(el('p', { class: 'muted', text: t('task_fmt', S.session.index + 1) + ' · ' + S.session.title }));
      var row = el('div', { class: 'rowline' });
      var resumeBtn = el('button', { class: 'btn primary', type: 'button', text: t('next') });
      resumeBtn.addEventListener('click', function () { go('#/run'); });
      var drop = el('button', { class: 'btn ghost', type: 'button', text: t('back') });
      drop.addEventListener('click', function () { RUN.discard(); });
      row.appendChild(resumeBtn); row.appendChild(drop);
      resume.appendChild(row);
      root.appendChild(resume);
    }

    var weak = AN.weakTopics(S.progress, 3);
    if (weak.length) {
      var weakCard = el('div', { class: 'card' });
      weakCard.appendChild(el('h3', { text: t('stat_by_topic') }));
      weakCard.appendChild(UI.bars(weak.map(function (item) {
        return {
          label: C.topicTitle(item.topic),
          value: Math.round(item.rate * 100),
          text: Math.round(item.rate * 100) + '%',
          color: item.rate < 0.5 ? '#e0555a' : (item.rate < 0.8 ? '#e0a84a' : '#3DC9A6'),
          action: function () { RUN.start({ mode: 'train', topics: [item.topic], tasks: RUN.topicTasks([item.topic]), title: C.topicTitle(item.topic) }); },
        };
      })));
      root.appendChild(weakCard);
    }

    var mistakes = el('div', { class: 'card' });
    mistakes.appendChild(el('h3', { text: t('mistakes') }));
    mistakes.appendChild(el('p', { class: 'muted small', text: t('review_answers') }));
    var mistakesBtn = el('button', { class: 'btn', type: 'button', text: t('mistakes') });
    mistakesBtn.addEventListener('click', function () { go('#/mistakes'); });
    mistakes.appendChild(mistakesBtn);
    root.appendChild(mistakes);

    root.appendChild(el('p', { class: 'muted small', text: t('disclaimer') }));
    return root;
  };

  /** Список выпущенных авторских наборов по годам. */
  SCREENS['#/tests'] = function () {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('exam') }));
    var meta = C.meta || {};
    var parts = meta.parts || { A: 18, B: 22 };
    var minutes = meta.minutes || 120;
    root.appendChild(el('p', { class: 'muted', text: t('exam_rules_fmt', parts.A + parts.B, parts.A, parts.B, minutes) }));

    C.variants().forEach(function (variant) {
      var card = el('div', { class: 'card' });
      card.appendChild(el('h3', { text: String(variant.year) }));
      card.appendChild(el('p', { class: 'muted small', text: t('part_a') + ': ' + variant.partA + ' · ' + t('part_b') + ': ' + variant.partB }));
      card.appendChild(el('p', { class: 'muted small', text: t('variant_note') }));
      var row = el('div', { class: 'rowline' });
      var exam = el('button', { class: 'btn primary', type: 'button', text: t('exam') });
      exam.addEventListener('click', function () {
        RUN.start({ mode: 'exam', year: variant.year, tasks: variant.tasks, title: String(variant.year), minutes: minutes });
      });
      var train = el('button', { class: 'btn', type: 'button', text: t('train') });
      train.addEventListener('click', function () {
        RUN.start({ mode: 'train', year: variant.year, tasks: variant.tasks, title: String(variant.year) });
      });
      row.appendChild(exam); row.appendChild(train);
      card.appendChild(row);
      root.appendChild(card);
    });

    var planned = C.plannedYears();
    if (planned.length) {
      var note = el('div', { class: 'card' });
      note.appendChild(el('h3', { text: t('topics') }));
      note.appendChild(el('p', { class: 'muted', text: t('periods_note_fmt',
        C.variants().map(function (v) { return v.year; }).join(', ') || '—', planned.join(', ')) }));
      root.appendChild(note);
    }

    var mixed = el('div', { class: 'card' });
    mixed.appendChild(el('h3', { text: t('train') }));
    mixed.appendChild(el('p', { class: 'muted small', text: t('topics') }));
    var mixedBtn = el('button', { class: 'btn', type: 'button', text: t('train') });
    mixedBtn.addEventListener('click', function () {
      RUN.start({ mode: 'train', tasks: RUN.topicTasks(C.topicsWithTasks(), 20), title: t('train') });
    });
    mixed.appendChild(mixedBtn);
    root.appendChild(mixed);
    return root;
  };

  /** Тренировка по темам. */
  SCREENS['#/practice'] = function (extra) {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('train') }));
    root.appendChild(el('p', { class: 'muted', text: t('topics') }));
    var topics = extra ? [extra] : C.topicsWithTasks();
    topics.forEach(function (topic) {
      var tasks = C.tasksByTopic(topic);
      var card = el('div', { class: 'card topic-card' });
      card.appendChild(el('h3', { text: C.topicTitle(topic) }));
      card.appendChild(el('p', { class: 'muted small', text: t('stat_total_fmt', tasks.length) + ' · ' + t('analogous') + ': ' + C.analogByTopic(topic).length }));
      var row = el('div', { class: 'rowline' });
      var start = el('button', { class: 'btn primary', type: 'button', text: t('train') });
      start.addEventListener('click', function () {
        RUN.start({ mode: 'train', topics: [topic], tasks: RUN.topicTasks([topic]), title: C.topicTitle(topic) });
      });
      row.appendChild(start);
      var rule = C.ruleGroupsFor(topic)[0];
      if (rule) {
        var open = el('button', { class: 'btn', type: 'button', text: t('rules') });
        open.addEventListener('click', function () { go('#/study#group-' + rule.id); });
        row.appendChild(open);
      }
      card.appendChild(row);
      root.appendChild(card);
    });
    if (!topics.length) root.appendChild(el('p', { class: 'muted', text: t('no_tasks') }));
    return root;
  };

  /** Прохождение варианта или набора. */
  SCREENS['#/run'] = function () {
    var session = S.session;
    if (!session) { go('#/tests'); return el('section', { class: 'screen' }); }
    if (session._taskStarted === undefined) session._taskStarted = Date.now();
    var task = RUN.task();
    var root = el('section', { class: 'screen' });
    if (!task) { root.appendChild(el('p', { text: t('mistakes_empty') })); return root; }

    var head = el('div', { class: 'run-head' });
    head.appendChild(el('h1', { text: session.title }));
    head.appendChild(el('p', { class: 'muted small', text: t('task_fmt', session.index + 1) + ' / ' + session.order.length }));
    if (session.limit) head.appendChild(el('p', { class: 'clock', id: 'run-clock', text: t('time_left_fmt', U.duration(RUN.secondsLeft(), I.lang)) }));
    root.appendChild(head);

    if (task.part) {
      root.appendChild(el('p', { class: 'part-badge', text: task.part === 'A' ? t('part_a') : t('part_b') }));
      root.appendChild(el('p', { class: 'muted small', text: task.part === 'A' ? t('part_a_hint') : t('part_b_hint') }));
    }

    var result = session.results[session.index] || null;
    // Разбор доступен после ответа всегда, но в варианте — только в конце,
    // чтобы не подсказывать (требование формата тестирования).
    var showBreakdown = session.mode !== 'exam' || !!session.finished;
    var card = UI.taskCard(task, {
      result: result,
      analogous: showBreakdown,
      reveal: showBreakdown,
      onAnswer: function (typed) {
        var graded = RUN.answer(typed);
        if (session.mode === 'exam' && S.settings.autoAdvance && graded && graded.ok) {
          global.setTimeout(function () { RUN.next(); }, 250);
        }
        return graded;
      },
      onGraded: function () { S.saveSession(true); },
    });
    root.appendChild(card);

    if (result && session.mode !== 'exam') {
      // в тренировке показываем, где это правило разобрано
      var rule = C.ruleGroupFor(task);
      var teach = el('div', { class: 'card' });
      teach.appendChild(el('h4', { text: t('study_plan') }));
      var lessons = C.lessonsForTopic(task.topic);
      if (lessons.length) {
        var open = el('button', { class: 'btn', type: 'button', text: t('study_example') + ': ' + I.pick(lessons[0].title) });
        open.addEventListener('click', function () { go('#/study/' + lessons[0].id); });
        teach.appendChild(open);
      }
      (rule ? rule.items : []).forEach(function (item) { teach.appendChild(UI.ruleCard(item, rule)); });
      root.appendChild(teach);
    }

    // сетка заданий: отметки, переходы, завершение
    var grid = el('div', { class: 'task-grid' });
    session.order.forEach(function (id, index) {
      var done = session.results[index];
      var classes = ['grid-cell'];
      if (done) classes.push(done.correct ? 'ok' : 'bad');
      if (session.marked.indexOf(index) >= 0) classes.push('marked');
      if (index === session.index) classes.push('current');
      var cell = el('button', { class: classes.join(' '), type: 'button', text: String(index + 1) });
      cell.addEventListener('click', function () { RUN.moveTo(index); });
      grid.appendChild(cell);
    });
    root.appendChild(grid);

    var nav = el('div', { class: 'run-nav' });
    var prev = el('button', { class: 'btn', type: 'button', text: t('prev') });
    prev.disabled = session.index === 0;
    prev.addEventListener('click', function () { RUN.moveTo(session.index - 1); });
    var mark = el('button', { class: 'btn ghost', type: 'button', text: '★' });
    mark.addEventListener('click', function () { RUN.mark(session.index); UI.render(); });
    var next = el('button', { class: 'btn primary', type: 'button', text: session.index === session.order.length - 1 ? t('finish') : t('next') });
    next.addEventListener('click', function () {
      var remaining = session.order.length - session.results.filter(Boolean).length;
      if (session.index === session.order.length - 1 && remaining > 0) {
        UI.confirm(t('finish') + '? ' + t('stat_total_fmt', remaining), function () { RUN.finish(); }, t('finish'));
        return;
      }
      RUN.next(false);
    });
    nav.appendChild(prev); nav.appendChild(mark); nav.appendChild(next);
    root.appendChild(nav);

    var finish = el('button', { class: 'btn ghost wide', type: 'button', text: t('finish') });
    finish.addEventListener('click', function () { UI.confirm(t('finish') + '?', function () { RUN.finish(); }, t('finish')); });
    root.appendChild(finish);
    if (session.limit) startClock();
    return root;
  };

  /** Итоги варианта. */
  SCREENS['#/result'] = function () {
    var root = el('section', { class: 'screen' });
    var attempt = (S.progress.attempts || [])[S.progress.attempts.length - 1];
    if (!attempt) { root.appendChild(el('p', { class: 'muted', text: t('stat_empty') })); return root; }
    var summary = AN.attemptSummary(attempt);
    root.appendChild(el('h1', { text: t('exam_finished') }));
    root.appendChild(el('p', { class: 'score', text: t('score_fmt', summary.correct, summary.total) }));
    root.appendChild(el('p', { class: 'muted', text: t('score_parts_fmt',
      summary.byPart.A.correct, summary.byPart.A.total, summary.byPart.B.correct, summary.byPart.B.total) }));
    root.appendChild(el('p', { class: 'muted small', text: U.duration(summary.seconds, I.lang) }));

    if (summary.mistakes.length) {
      var card = el('div', { class: 'card' });
      card.appendChild(el('h3', { text: t('mistakes') }));
      summary.mistakes.forEach(function (result) {
        var task = C.taskById(result.taskId);
        if (!task) return;
        var row = el('button', { class: 'mistake-row', type: 'button' });
        row.appendChild(el('span', { class: 'mistake-text', text: task.text }));
        row.appendChild(el('span', { class: 'muted small', text: t('expected_fmt', result.expected) }));
        row.appendChild(el('span', { class: 'muted small', text: reasonLabel(result.reason) }));
        row.addEventListener('click', function () { go('#/mistakes/' + task.id); });
        card.appendChild(row);
      });
      root.appendChild(card);
      var again = el('button', { class: 'btn primary', type: 'button', text: t('retry') });
      again.addEventListener('click', function () {
        var tasks = RUN.mistakeTasks(summary.mistakes);
        RUN.start({ mode: 'train', tasks: tasks, title: t('mistakes') });
      });
      root.appendChild(again);
    } else {
      root.appendChild(el('p', { class: 'banner good', text: t('mistakes_empty') }));
    }

    var review = el('button', { class: 'btn', type: 'button', text: t('review_answers') });
    review.addEventListener('click', function () { go('#/mistakes'); });
    root.appendChild(review);
    return root;
  };

  /** Разбор ошибок: последние попытки, диагноз, правило, урок, аналоги. */
  SCREENS['#/mistakes'] = function (extra) {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('mistakes') }));
    var attempt = (S.progress.attempts || [])[S.progress.attempts.length - 1];
    var results = attempt ? AN.attemptSummary(attempt).mistakes : [];

    if (extra) {
      var task = C.taskById(extra);
      if (!task) { root.appendChild(el('p', { class: 'muted', text: t('no_tasks') })); return root; }
      var result = (attempt ? attempt.results : []).filter(function (item) { return item.taskId === extra; })[0] || null;
      var back = el('button', { class: 'btn ghost', type: 'button', text: t('back') });
      back.addEventListener('click', function () { go('#/mistakes'); });
      root.appendChild(back);
      root.appendChild(UI.taskCard(task, { result: result, onAnswer: function (typed) { return A.check(task, typed); } }));
      return root;
    }

    if (!results.length) {
      root.appendChild(el('p', { class: 'muted', text: t('mistakes_empty') }));
      var toTests = el('button', { class: 'btn primary', type: 'button', text: t('exam') });
      toTests.addEventListener('click', function () { go('#/tests'); });
      root.appendChild(toTests);
      return root;
    }

    root.appendChild(el('p', { class: 'muted', text: t('stat_total_fmt', results.length) }));
    results.forEach(function (result) {
      var task = C.taskById(result.taskId);
      if (!task) return;
      var card = el('div', { class: 'card mistake-card' });
      card.appendChild(el('p', { class: 'task-text', text: task.text }));
      card.appendChild(el('p', { class: 'muted small', text: t('your_answer_fmt', result.typed) }));
      card.appendChild(el('p', { class: 'muted small', text: t('expected_fmt', result.expected) }));
      var reason = el('p', { class: 'banner bad', text: reasonLabel(result.reason) });
      card.appendChild(reason);
      if (task.correction) card.appendChild(el('p', { text: I.pick(task.correction) }));
      C.diagnoses(task).forEach(function (diagnosis) {
        var box = el('div', { class: 'diagnosis' });
        box.appendChild(el('strong', { text: I.pick(diagnosis.title) }));
        box.appendChild(el('p', { text: I.pick(diagnosis.fix) }));
        card.appendChild(box);
      });
      var open = el('button', { class: 'btn', type: 'button', text: t('review_answers') });
      open.addEventListener('click', function () { go('#/mistakes/' + task.id); });
      card.appendChild(open);
      root.appendChild(card);
    });
    var again = el('button', { class: 'btn primary', type: 'button', text: t('retry') });
    again.addEventListener('click', function () {
      RUN.start({ mode: 'train', tasks: RUN.mistakeTasks(results), title: t('mistakes') });
    });
    root.appendChild(again);
    return root;
  };

  /** Справочник: разделы правил, уроки и схемы. */
  SCREENS['#/study'] = function (extra) {
    var root = el('section', { class: 'screen' });
    if (extra && C.lessonById(extra)) {
      var lesson = C.lessonById(extra);
      var back = el('button', { class: 'btn ghost', type: 'button', text: t('back') });
      back.addEventListener('click', function () { go('#/study'); });
      root.appendChild(back);
      root.appendChild(el('h1', { text: I.pick(lesson.title) }));
      root.appendChild(el('p', { class: 'muted', text: I.pick(lesson.summary) }));
      (lesson.sections || []).forEach(function (section) {
        if (section.kind === 'text') { root.appendChild(el('p', { text: I.pick(section) })); return; }
        var block = el('div', { class: 'card' });
        block.appendChild(el('h4', { text: I.pick(section.title) }));
        var list = el('ol', { class: 'steps' });
        (section[I.lang] || section.ru || []).forEach(function (line) { list.appendChild(el('li', { text: line })); });
        block.appendChild(list);
        root.appendChild(block);
      });
      if (lesson.everyday) {
        var everyday = el('div', { class: 'card' });
        everyday.appendChild(el('h4', { text: t('rule_everyday') }));
        everyday.appendChild(el('p', { text: I.pick(lesson.everyday) }));
        root.appendChild(everyday);
      }
      var figure = lesson.figure ? C.figureById(lesson.figure) : null;
      if (figure) root.appendChild(UI.diagramCard(figure));
      var practice = el('button', { class: 'btn primary', type: 'button', text: t('train') });
      practice.addEventListener('click', function () {
        RUN.start({ mode: 'train', topics: [lesson.topic], tasks: RUN.topicTasks([lesson.topic]), title: I.pick(lesson.title) });
      });
      root.appendChild(practice);
      return root;
    }

    root.appendChild(el('h1', { text: t('rules') }));
    root.appendChild(el('p', { class: 'muted', text: t('language_note') }));

    var search = el('input', { type: 'search', class: 'search', placeholder: t('rules'), 'aria-label': t('rules') });
    var list = el('div', {});
    var render = function () {
      var needle = (search.value || '').toLowerCase();
      clear(list);
      C.rules.forEach(function (group) {
        var items = (group.items || []).filter(function (item) {
          if (!needle) return true;
          return (I.pick(item.title) + ' ' + I.pick(item.formulation)).toLowerCase().indexOf(needle) >= 0;
        });
        if (!items.length) return;
        var card = el('div', { class: 'card rule-group', id: 'group-' + group.id });
        card.appendChild(el('h3', { text: I.pick(group.title) }));
        items.forEach(function (item) { card.appendChild(UI.ruleCard(item, group)); });
        list.appendChild(card);
      });
      var figures = Object.keys(C.figures).map(function (id) { return C.figures[id]; })
        .filter(function (figure) {
          if (!needle) return false;
          return (I.pick(figure.title) + ' ' + I.pick(figure.caption)).toLowerCase().indexOf(needle) >= 0;
        });
      figures.forEach(function (figure) { list.appendChild(UI.diagramCard(figure)); });
      if (!list.firstChild) list.appendChild(el('p', { class: 'muted', text: t('no_tasks') }));
    };
    search.addEventListener('input', render);
    root.appendChild(search);
    root.appendChild(list);
    render();

    var checklist = el('div', { class: 'card' });
    checklist.appendChild(el('h3', { text: t('checklist') }));
    var box = el('ul', { class: 'steps' });
    (C.checklist || []).forEach(function (line) { box.appendChild(el('li', { text: I.pick(line) })); });
    checklist.appendChild(box);
    root.appendChild(checklist);
    return root;
  };

  /** Статистика. */
  SCREENS['#/stats'] = function () {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('statistics') }));
    var totals = AN.totals(S.progress);
    root.appendChild(el('p', { class: 'score', text: t('stat_total_fmt', totals.tasks) }));
    root.appendChild(el('p', { class: 'muted', text: t('stat_correct_fmt', Math.round(totals.accuracy * 100)) + ' · ' + t('stat_streak_fmt', S.progress.streak || 0) }));

    var topicStats = AN.topicStats(S.progress);
    var topicItems = Object.keys(topicStats).map(function (topic) {
      return {
        label: C.topicTitle(topic), value: Math.round(topicStats[topic].rate * 100),
        text: t('stat_correct_fmt', Math.round(topicStats[topic].rate * 100)) + ' (' + topicStats[topic].total + ')',
        color: topicStats[topic].rate < 0.5 ? '#e0555a' : (topicStats[topic].rate < 0.8 ? '#e0a84a' : '#3DC9A6'),
      };
    }).sort(function (a, b) { return a.value - b.value; });
    if (topicItems.length) {
      var byTopic = el('div', { class: 'card' });
      byTopic.appendChild(el('h3', { text: t('stat_by_topic') }));
      byTopic.appendChild(UI.bars(topicItems));
      root.appendChild(byTopic);
    } else {
      root.appendChild(el('p', { class: 'muted', text: t('stat_empty') }));
    }

    var yearStats = AN.yearStats(S.progress);
    var yearKeys = Object.keys(yearStats);
    if (yearKeys.length) {
      var byYear = el('div', { class: 'card' });
      byYear.appendChild(el('h3', { text: t('exam') }));
      byYear.appendChild(UI.bars(yearKeys.sort().map(function (year) {
        return {
          label: year, value: Math.round(yearStats[year].rate * 100),
          text: t('stat_correct_fmt', Math.round(yearStats[year].rate * 100)),
        };
      })));
      root.appendChild(byYear);
    }

    var days = Object.keys(S.progress.daily || {}).sort().slice(-14);
    if (days.length) {
      var daily = el('div', { class: 'card' });
      daily.appendChild(el('h3', { text: t('progress') }));
      daily.appendChild(UI.bars(days.map(function (day) {
        return { label: day.slice(5), value: Math.min(100, (S.progress.daily[day] / (S.settings.dailyGoal || 20)) * 100), text: String(S.progress.daily[day]) };
      })));
      root.appendChild(daily);
    }

    var attempts = (S.progress.attempts || []).slice(-10).reverse();
    if (attempts.length) {
      var list = el('div', { class: 'card' });
      list.appendChild(el('h3', { text: t('exam') }));
      attempts.forEach(function (attempt) {
        var summary = AN.attemptSummary(attempt);
        list.appendChild(el('p', { class: 'muted small', text: U.formatDate(attempt.at, I.lang) + ' · ' + t('score_fmt', summary.correct, summary.total) + ' · ' + U.duration(summary.seconds, I.lang) }));
      });
      root.appendChild(list);
    }

    var report = el('button', { class: 'btn', type: 'button', text: t('export_report') });
    report.addEventListener('click', function () {
      var html = '<h1>' + esc(t('app_name')) + '</h1><p>' + esc(t('stat_total_fmt', totals.tasks)) + '</p>' +
        UI.bars(topicItems).outerHTML;
      B.saveReport('progress', html).then(function () { UI.toast(t('report_saved')); })
        .catch(function () { B.notify(t('error_generic')); });
    });
    root.appendChild(report);
    return root;
  };

  /** Настройки. */
  SCREENS['#/settings'] = function () {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('settings') }));

    var language = el('div', { class: 'card' });
    language.appendChild(el('h3', { text: t('language') }));
    var langRow = el('div', { class: 'rowline' });
    [['ru', 'Русский'], ['en', 'English']].forEach(function (pair) {
      var button = el('button', { class: 'btn' + (S.settings.lang === pair[0] ? ' primary' : ''), type: 'button', text: pair[1] });
      button.addEventListener('click', function () { UI.changeLanguage(pair[0]); });
      langRow.appendChild(button);
    });
    language.appendChild(langRow);
    language.appendChild(el('p', { class: 'muted small', text: t('language_note') }));
    root.appendChild(language);

    var appearance = el('div', { class: 'card' });
    appearance.appendChild(el('h3', { text: t('theme') }));
    var themeRow = el('div', { class: 'rowline' });
    [['system', 'theme_auto'], ['light', 'theme_light'], ['dark', 'theme_dark']].forEach(function (pair) {
      var button = el('button', { class: 'btn' + (S.settings.theme === pair[0] ? ' primary' : ''), type: 'button', text: t(pair[1]) });
      button.addEventListener('click', function () {
        S.settings.theme = pair[0]; S.save(true); UI.applyAppearance(); UI.render();
      });
      themeRow.appendChild(button);
    });
    appearance.appendChild(themeRow);
    var fontRow = el('div', { class: 'rowline' });
    [[0.9, 'A'], [1, 'A'], [1.15, 'A']].forEach(function (pair, index) {
      var button = el('button', { class: 'btn' + (S.settings.fontScale === pair[0] ? ' primary' : ''), type: 'button', text: pair[1] });
      button.style.fontSize = (0.9 + index * 0.15) + 'em';
      button.addEventListener('click', function () {
        S.settings.fontScale = pair[0]; S.save(true); UI.applyAppearance(); UI.render();
      });
      fontRow.appendChild(button);
    });
    appearance.appendChild(fontRow);
    appearance.appendChild(el('p', { class: 'muted small', text: t('large_text') }));
    root.appendChild(appearance);

    var exam = el('div', { class: 'card' });
    exam.appendChild(el('h3', { text: t('exam') }));
    var minutes = el('input', { type: 'number', min: '10', max: '240', step: '5', class: 'answer-input',
      value: String(S.settings.examMinutes || 120), 'aria-label': t('exam') });
    minutes.addEventListener('change', function () {
      S.settings.examMinutes = U.clamp(parseInt(minutes.value, 10) || 120, 10, 240); S.save(true);
    });
    exam.appendChild(minutes);
    var goal = el('input', { type: 'number', min: '5', max: '200', step: '5', class: 'answer-input',
      value: String(S.settings.dailyGoal || 20), 'aria-label': t('progress') });
    goal.addEventListener('change', function () {
      S.settings.dailyGoal = U.clamp(parseInt(goal.value, 10) || 20, 5, 200); S.progress.goal = S.settings.dailyGoal; S.save(true);
    });
    exam.appendChild(goal);
    var autoAdvance = el('input', { type: 'checkbox' });
    autoAdvance.checked = !!S.settings.autoAdvance;
    autoAdvance.addEventListener('change', function () { S.settings.autoAdvance = autoAdvance.checked; S.save(true); });
    var autoLabel = el('label', { class: 'check-row' });
    autoLabel.appendChild(autoAdvance);
    autoLabel.appendChild(el('span', { text: t('next') }));
    exam.appendChild(autoLabel);
    var keepOn = el('input', { type: 'checkbox' });
    keepOn.checked = !!S.settings.keepScreenOn;
    keepOn.addEventListener('change', function () { S.settings.keepScreenOn = keepOn.checked; S.save(true); });
    var keepLabel = el('label', { class: 'check-row' });
    keepLabel.appendChild(keepOn);
    keepLabel.appendChild(el('span', { text: t('keep_screen_on') }));
    exam.appendChild(keepLabel);
    root.appendChild(exam);

    var updates = el('div', { class: 'card' });
    updates.appendChild(el('h3', { text: t('updates_check') }));
    var autoUpdate = el('input', { type: 'checkbox' });
    autoUpdate.checked = !!S.settings.autoUpdate;
    autoUpdate.addEventListener('change', function () { S.settings.autoUpdate = autoUpdate.checked; S.save(true); });
    var updateLabel = el('label', { class: 'check-row' });
    updateLabel.appendChild(autoUpdate);
    updateLabel.appendChild(el('span', { text: t('updates_check') }));
    updates.appendChild(updateLabel);
    var base = el('input', { type: 'url', class: 'answer-input', placeholder: 'https://github.com/…/releases',
      value: S.settings.baseUrl || '', 'aria-label': t('updates_check') });
    base.addEventListener('change', function () { S.settings.baseUrl = base.value.trim(); S.save(true); });
    updates.appendChild(base);
    var checkNow = el('button', { class: 'btn', type: 'button', text: t('updates_check') });
    checkNow.addEventListener('click', function () {
      B.checkUpdates(S.settings.baseUrl, (C.meta || {}).contentVersion).then(function (result) {
        var version = result && result.version;
        if (version && version !== (C.meta || {}).contentVersion) {
          return C.load().then(function () { UI.toast(t('updates_found_fmt', version)); UI.render(); });
        }
        UI.toast(t('updates_none'));
      }).catch(function () { B.notify(t('error_generic')); });
    });
    updates.appendChild(checkNow);
    root.appendChild(updates);

    var data = el('div', { class: 'card' });
    data.appendChild(el('h3', { text: t('settings') }));
    var folder = el('button', { class: 'btn', type: 'button', text: t('offline_note') });
    folder.addEventListener('click', function () { B.openFolder('data').catch(function () { B.notify(t('error_generic')); }); });
    data.appendChild(folder);
    var reset = el('button', { class: 'btn ghost', type: 'button', text: t('mistakes_empty') });
    reset.addEventListener('click', function () {
      UI.confirm(t('progress'), function () { S.resetProgress().then(function () { UI.toast(t('progress')); UI.render(); }); });
    });
    data.appendChild(reset);
    root.appendChild(data);
    return root;
  };

  /** О программе. */
  SCREENS['#/about'] = function () {
    var root = el('section', { class: 'screen' });
    root.appendChild(el('h1', { text: t('app_name') }));
    root.appendChild(el('p', { text: t('about_text') }));
    root.appendChild(el('p', { class: 'muted small', text: t('disclaimer') }));
    var meta = C.meta || {};
    var info = el('div', { class: 'card' });
    info.appendChild(el('p', { class: 'muted small', text: t('periods_note_fmt',
      C.variants().map(function (variant) { return variant.year; }).join(', ') || '—',
      C.plannedYears().join(', ') || '—') }));
    info.appendChild(el('p', { class: 'muted small', text: t('offline_note') }));
    info.appendChild(el('p', { class: 'muted small', text: 'content ' + (meta.contentVersion || '—') + ' · ' + (B.info.version || '') }));
    if (B.info.dataDir) info.appendChild(el('p', { class: 'muted small', text: B.info.dataDir }));
    root.appendChild(info);

    var contacts = el('div', { class: 'card' });
    contacts.appendChild(el('h3', { text: t('feedback_subject') }));
    [['Захаревич Игорь · Zakharevich Igor', null],
      ['ziv@csl.by', 'mailto:ziv@csl.by'],
      ['+375 33 714 12', 'tel:+3753371412'],
      ['WhatsApp', 'https://wa.me/3753371412'],
      ['GitHub', 'https://github.com/zigorminsk-debug/mathematics']].forEach(function (pair) {
      var node = pair[1] ? el('a', { class: 'link', href: pair[1], text: pair[0], rel: 'noopener' })
        : el('p', { class: 'muted small', text: pair[0] });
      if (pair[1] && pair[1].indexOf('http') === 0) {
        node.addEventListener('click', function (event) { event.preventDefault(); B.openExternal(pair[1]); });
      }
      contacts.appendChild(node);
    });
    root.appendChild(contacts);
    return root;
  };

  /* ------------------------------------------------------------------ *
   * 5. Роутер и запуск
   * ------------------------------------------------------------------ */
  var NAV = [
    ['#/home', 'home', '🏠'],
    ['#/tests', 'exam', '📝'],
    ['#/practice', 'train', '🔁'],
    ['#/study', 'rules', '📖'],
    ['#/stats', 'statistics', '📊'],
    ['#/mistakes', 'mistakes', '🧐'],
    ['#/about', 'study', 'ℹ️'],
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

  /** Разбор адреса: «#/study/lesson-tenses» → {name:'#/study', extra:'lesson-tenses'} */
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
    try {
      view.appendChild(screen(route.extra));
    } catch (error) {
      if (global.console) global.console.error(error);
      view.appendChild(h('<div class="card"><p class="banner bad">' + esc(t('reason_exact')) + '</p>' +
        '<pre class="small">' + esc(String(error && error.message || error)) + '</pre></div>'));
    }
    view.scrollTop = 0;
    UI.renderNav();
    UI.chrome();
    if (route.name !== '#/run') { stopClock(); B.keepScreenOn(false); }
  };
  CT.render = UI.render;

  /** Системная кнопка «назад» на Android: «exit» — выйти из приложения. */
  CT.onAndroidBack = function () {
    if ($('#modal') && $('#modal').classList.contains('open')) { UI.backModal(); return null; }
    var route = parseHash();
    if (route.name === '#/home') return 'exit';
    if (route.name === '#/study' && route.extra) { go('#/study'); return null; }
    if (route.name === '#/mistakes' && route.extra) { go('#/mistakes'); return null; }
    if (route.name === '#/run') { go(S.session ? '#/home' : '#/tests'); return null; }
    var parent = { '#/result': '#/home', '#/mistakes': '#/home', '#/study': '#/home', '#/settings': '#/home' }[route.name];
    go(parent || '#/home');
    return null;
  };

  var booted = false;

  CT.boot = function () {
    if (booted) return Promise.resolve(true);
    booted = true;
    var brand = $('#brand');
    if (brand) brand.addEventListener('click', function () { go('#/home'); });
    UI.bindChrome();
    I.setLang('ru');
    return S.load().catch(function () { return S; }).then(function () {
      I.setLang(S.settings.lang);
      return C.load().catch(function (error) {
        if (global.console) global.console.error(error);
        return null;
      });
    }).then(function () {
      UI.applyAppearance();
      B.ready().then(function (info) {
        B.info = info || {};
        B.platform = B.info.platform || (B.native ? 'android' : 'windows');
        var folder = $('#app-folder');
        if (folder) folder.textContent = B.info.dataDir || '';
        UI.render();
      });
      UI.render();
      // Автообновление банка: тихо, по настройке; ошибка сети просто пропускается.
      if (S.settings.autoUpdate) {
        B.checkUpdates(S.settings.baseUrl, (C.meta || {}).contentVersion).then(function (result) {
          var version = result && result.version;
          if (version && version !== (C.meta || {}).contentVersion) {
            return C.load().then(function () {
              if (parseHash().name !== '#/run') UI.render();
              UI.toast(t('updates_found_fmt', version));
            });
          }
          return null;
        }).catch(function () { /* офлайн: работаем на встроенном банке */ });
      }
      return true;
    });
  };

  global.addEventListener('hashchange', UI.render);
  doc.addEventListener('DOMContentLoaded', function () { CT.boot(); });
  if (doc.readyState !== 'loading') CT.boot();
})(typeof globalThis !== 'undefined' ? globalThis : this);

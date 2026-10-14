/* core.js — ядро интерфейса английского тренажёра (Android WebView и Windows Go).
 *
 * Здесь всё, что не зависит от платформы: загрузка авторского банка, алгоритм
 * проверки ответа (точно такой же, как в content_src/policy.py и в
 * android/app/src/main/java/by/ziv/ctenglish/AnswerChecker.kt), аналитика
 * прогресса и хранилище с автосохранением.
 *
 * Английские ответы проверяются не «как числа»: в упражнениях пробел, дефис,
 * апостроф, артикль и регистр часто и есть ответ, поэтому задание само объявляет
 * политику проверки (policy), а этот код её исполняет.
 *
 * Shared engine of the UI: content loading, the portable answer checker that
 * mirrors policy.py, analytics and storage. Platform differences live behind
 * CT.bridge (window.CTNative on Android, fetch() to the local HTTP API on
 * Windows). None of the checked English text is translated here.
 */
(function (global) {
  'use strict';

  var CT = {};

  /* --------------------------------------------------------------------- *
   * 0. Мелочи / small helpers
   * --------------------------------------------------------------------- */
  var U = CT.util = {
    today: function (date) {
      var d = date ? new Date(date) : new Date();
      return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
    },
    daysBetween: function (a, b) {
      return Math.round((new Date(b + 'T00:00:00') - new Date(a + 'T00:00:00')) / 86400000);
    },
    clamp: function (v, lo, hi) { return Math.max(lo, Math.min(hi, v)); },
    round: function (v, digits) {
      var p = Math.pow(10, digits === undefined ? 1 : digits);
      return Math.round(v * p) / p;
    },
    /** «12 мин 30 с» / "12 min 30 s" */
    duration: function (seconds, lang) {
      seconds = Math.max(0, Math.round(seconds || 0));
      var m = Math.floor(seconds / 60), s = seconds % 60;
      if (lang === 'en') return m ? m + ' min ' + s + ' s' : s + ' s';
      return m ? m + ' мин ' + s + ' с' : s + ' с';
    },
    formatDate: function (iso, lang) {
      var d = new Date(iso);
      var p = function (n) { return ('0' + n).slice(-2); };
      return lang === 'en'
        ? p(d.getDate()) + '/' + p(d.getMonth() + 1) + '/' + d.getFullYear() + ' ' + p(d.getHours()) + ':' + p(d.getMinutes())
        : p(d.getDate()) + '.' + p(d.getMonth() + 1) + '.' + d.getFullYear() + ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
    },
    uid: function () {
      return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
    },
    /** Простое перемешивание (детерминированное для одного seed). */
    shuffle: function (list, rnd) {
      var out = list.slice(), i, j, tmp;
      rnd = rnd || Math.random;
      for (i = out.length - 1; i > 0; i--) {
        j = Math.floor(rnd() * (i + 1));
        tmp = out[i]; out[i] = out[j]; out[j] = tmp;
      }
      return out;
    },
    sum: function (list) { return list.reduce(function (a, b) { return a + b; }, 0); },
    /** Латиница и цифры: «don't» → «dont» (сравнение «почти совпало»). */
    letters: function (value) {
      return String(value || '').toLowerCase().replace(/[^a-z0-9]/g, '');
    },
  };

  /* --------------------------------------------------------------------- *
   * 1. Язык / language
   * --------------------------------------------------------------------- */
  var I = CT.i18n = {
    lang: 'ru',
    strings: {},
    setLang: function (lang) {
      this.lang = lang === 'en' ? 'en' : 'ru';
      try { global.document && global.document.documentElement.setAttribute('lang', this.lang); } catch (e) {}
      return this.lang;
    },
    /** Значение из двуязычного объекта {ru, en}. */
    pick: function (value) {
      if (value === null || value === undefined) return '';
      if (typeof value === 'string') return value;
      if (Array.isArray(value)) return value.map(function (item) { return I.pick(item); }).join(' ');
      return value[this.lang] || value.ru || value.en || '';
    },
    /** Строка интерфейса с подстановкой %s. */
    t: function (key) {
      var entry = this.strings[key];
      var text = entry ? (entry[this.lang] || entry.ru || entry.en || key) : key;
      for (var i = 1; i < arguments.length; i++) text = text.replace('%s', arguments[i]);
      return text;
    },
  };

  /* --------------------------------------------------------------------- *
   * 2. Мост к платформе / platform bridge
   * --------------------------------------------------------------------- */
  var SUBJECT = 'english';
  var APP_NAME = 'CTEnglishTutor';

  var B = CT.bridge = {
    native: typeof global.CTNative !== 'undefined' ? global.CTNative : null,
    platform: 'web',
    info: {},
    /** Состояние платформы: {app:{...}, content:{...}, blobs:[...]} → плоский вид. */
    ready: function () {
      var self = this;
      if (!this._ready) {
        this._ready = this.getState().then(function (state) {
          self.state = state || {};
          var app = (state && state.app) || {};
          self.info = Object.assign({}, app, {
            contentVersion: (state && state.content && state.content.version) || '',
            overlay: !!(state && state.content && state.content.overlay),
          });
          self.platform = app.platform || (self.native ? 'android' : 'windows');
          return self.info;
        }).catch(function (error) {
          if (global.console) global.console.warn('platform state unavailable', error);
          self.info = self.info || {};
          self.platform = self.native ? 'android' : 'windows';
          return self.info;
        });
      }
      return this._ready;
    },
    getState: function () {
      var self = this;
      if (this.native && this.native.getState) {
        return Promise.resolve().then(function () { return JSON.parse(self.native.getState()); });
      }
      return fetch('api/state').then(function (r) { return r.json(); });
    },
    loadBlob: function (key) {
      var self = this;
      if (this.native && this.native.loadBlob) {
        return Promise.resolve().then(function () {
          var raw = self.native.loadBlob(key);
          if (raw === null || raw === undefined || raw === '') return null;
          return typeof raw === 'string' ? JSON.parse(raw) : raw;
        });
      }
      return fetch('api/blob?key=' + encodeURIComponent(key)).then(function (r) {
        return r.text().then(function (text) { return text ? JSON.parse(text) : null; });
      });
    },
    saveBlob: function (key, json) {
      if (this.native && this.native.saveBlob) {
        this.native.saveBlob(key, json);
        return Promise.resolve();
      }
      return fetch('api/blob?key=' + encodeURIComponent(key), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: json,
      }).then(function (r) { return r.json(); });
    },
    getContent: function (name) {
      var self = this;
      if (this.native && this.native.getContent) {
        return Promise.resolve().then(function () { return JSON.parse(self.native.getContent(name)); });
      }
      return fetch('content/' + name + '.json').then(function (r) {
        if (!r.ok) throw new Error('content/' + name + ' → HTTP ' + r.status);
        return r.json();
      });
    },
    checkUpdates: function (baseUrl, current) {
      var self = this;
      if (this.native && this.native.checkUpdatesAsync) {
        // Сеть — на отдельном потоке, не в потоке WebView.
        return new Promise(function (resolve, reject) {
          var id = 'update-' + U.uid();
          self._updates = self._updates || {};
          self._updates[id] = { resolve: resolve, reject: reject };
          try { self.native.checkUpdatesAsync(baseUrl || '', current || '', id); }
          catch (error) { delete self._updates[id]; reject(error); }
        });
      }
      if (this.native && this.native.checkUpdates) {
        return Promise.resolve().then(function () { return JSON.parse(self.native.checkUpdates(baseUrl || '', current || '')); });
      }
      return fetch('api/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ baseUrl: baseUrl || '', current: current || '' }),
      }).then(function (r) { return r.json(); });
    },
    onUpdateResult: function (id, response) {
      var pending = (this._updates || {})[id];
      if (!pending) return;
      delete this._updates[id];
      try { pending.resolve(typeof response === 'string' ? JSON.parse(response) : response); }
      catch (error) { pending.reject(error); }
    },
    notify: function (message) {
      if (this.native && this.native.toast) { this.native.toast(message); return; }
      if (CT.app && CT.app.toast) { CT.app.toast(message); return; }
      if (global.console) global.console.log(message);
    },
    saveReport: function (kind, html) {
      var self = this;
      if (this.native && this.native.saveReport) {
        return Promise.resolve().then(function () { return JSON.parse(self.native.saveReport(kind, html)); });
      }
      return fetch('api/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ kind: kind || 'progress', html: html }),
      }).then(function (r) { return r.json(); });
    },
    openExternal: function (url) {
      if (this.native && this.native.openExternal) { this.native.openExternal(url); return; }
      if (typeof global.open === 'function') { global.open(url, '_blank'); return; }
      if (global.location) global.location.href = url;
    },
    openFolder: function (which) {
      var self = this;
      if (this.native && this.native.openFolder) {
        return Promise.resolve().then(function () { return self.native.openFolder(which || 'data'); });
      }
      return fetch('api/open-folder?which=' + encodeURIComponent(which || 'data'), { method: 'POST' })
        .then(function (r) { return r.json(); });
    },
    quit: function () {
      if (this.native && this.native.quit) { this.native.quit(); return Promise.resolve(); }
      return fetch('api/quit', { method: 'POST' }).then(function () { return { ok: true }; });
    },
    keepScreenOn: function (on) {
      if (this.native && this.native.setKeepScreenOn) this.native.setKeepScreenOn(!!on);
    },
    vibrate: function (ms) {
      if (this.native && this.native.vibrate) { this.native.vibrate(ms || 20); return; }
      if (global.navigator && global.navigator.vibrate) { try { global.navigator.vibrate(ms || 20); } catch (e) {} }
    },
    isNative: function () { return !!this.native; },
  };

  /* --------------------------------------------------------------------- *
   * 3. Проверка ответа / English answer checker
   *
   * Тот же контракт, что в english/content_src/policy.py и в
   * english/android/app/src/main/java/by/ziv/ctenglish/AnswerChecker.kt.
   * Совпадение трёх реализаций проверяется векторами
   * content/answer_vectors.json (English answer vectors, RU/EN notes).
   * --------------------------------------------------------------------- */
  var A = CT.answer = {};

  //: значения политики по умолчанию — как в policy.py
  A.DEFAULT_POLICY = {
    case: 'insensitive',
    article: 'checked',
    apostrophe: 'ignore',
    hyphen: 'significant',
    space: 'significant',
    stress: 'significant',
    empty: 'reject',
  };

  //: порядок ключей одинаков во всех трёх реализациях
  A.POLICY_KEYS = ['case', 'article', 'apostrophe', 'hyphen', 'space', 'stress', 'empty'];

  A.ALLOWED = {
    case: ['insensitive', 'sensitive'],
    article: ['checked', 'ignored'],
    apostrophe: ['ignore', 'required'],
    hyphen: ['significant', 'ignore'],
    space: ['significant', 'collapse'],
    stress: ['significant', 'ignore'],
    empty: ['reject', 'accept'],
  };

  //: «пропуск должен остаться пустым» — так в банке записан ответ «—»
  A.NOTHING = '—';

  var APOSTROPHES = /[\u2019\u02bc\u2018'`]/g;
  var DASHES = /[\u2010\u2011\u2012\u2013\u2014\u2212]/g;
  var ARTICLES = ['a', 'an', 'the'];

  /** Политика задания с подставленными значениями по умолчанию. */
  A.policyFor = function (task) {
    var merged = Object.assign({}, A.DEFAULT_POLICY, (task && task.policy) || {});
    A.POLICY_KEYS.forEach(function (key) {
      var value = merged[key];
      if (!value || A.ALLOWED[key].indexOf(value) < 0) {
        throw new Error('политика ' + key + '=' + value + ' недопустима для задания ' + ((task && task.id) || '?'));
      }
    });
    return merged;
  };

  /** Привести ответ к сравнимому виду только по разрешённым правилам. */
  A.normalize = function (text, policy) {
    var value = text === null || text === undefined ? '' : String(text);
    value = value.replace(/\u00a0/g, ' ');
    value = value.replace(DASHES, policy.hyphen === 'significant' ? '-' : '');
    if (policy.hyphen !== 'significant') value = value.replace(/-/g, '');
    value = value.replace(APOSTROPHES, policy.apostrophe === 'required' ? "'" : '');
    if (policy.stress === 'ignore') value = A._withoutDiacritics(value);
    if (policy.space === 'collapse') value = value.replace(/\s+/g, ' ');
    value = value.replace(/^\s+|\s+$/g, '');
    if (policy.case === 'insensitive') value = value.toLowerCase();  // до артиклей: «The» → артикль
    if (policy.article === 'ignored') {
      value = A._dropArticles(value).replace(/\s+/g, ' ').replace(/^\s+|\s+$/g, '');
    }
    return value;
  };

  /**
   * Сравнить ввод с допустимыми ответами задания.
   *
   * Порядок причин отказа — часть контракта (его повторяют Python и Kotlin):
   * empty → case → apostrophe → hyphen → space → article → stress → near → exact.
   */
  A.check = function (task, typed) {
    var policy = A.policyFor(task);
    var accepted = [((task && task.answer) || {}).value || ''];
    (task && task.accepted || []).forEach(function (item) { accepted.push(item); });
    accepted = accepted.filter(function (item) { return item !== ''; });
    if (!accepted.length) throw new Error('у задания ' + ((task && task.id) || '?') + ' нет допустимого ответа');

    var gotRaw = typed === null || typed === undefined ? '' : String(typed).replace(/^\s+|\s+$/g, '');
    var got = A.normalize(gotRaw, policy);
    if (got === '') {
      // «ничего не нужно» — законный ответ задания, объявившего empty: accept
      if (policy.empty === 'accept') return { ok: true, reason: 'ok', expected: '', got: gotRaw };
      return { ok: false, reason: 'empty', expected: accepted[0], got: gotRaw };
    }
    // задание, где пропуск должен остаться пустым: любое слово — уже ошибка
    if (accepted.length === 1 && accepted[0] === A.NOTHING) {
      var tokens = A._tokens(got);
      var reason = A._withoutArticles(tokens).join(' ') !== tokens.join(' ') ? 'article' : 'exact';
      return { ok: false, reason: reason, expected: '', got: gotRaw };
    }

    var norms = accepted.map(function (item) { return A.normalize(item, policy); });
    if (norms.indexOf(got) >= 0) return { ok: true, reason: 'ok', expected: accepted[0], got: gotRaw };

    for (var i = 0; i < accepted.length; i++) {
      var expected = accepted[i], norm = norms[i];
      if (A._differsOnlyByCase(got, norm, policy)) return { ok: false, reason: 'case', expected: expected, got: gotRaw };
      if (policy.apostrophe === 'required' && A._stripApostrophes(got) === A._stripApostrophes(norm)) {
        return { ok: false, reason: 'apostrophe', expected: expected, got: gotRaw };
      }
      if (policy.hyphen === 'significant' && (norm.replace(/-/g, ' ') === got || norm.replace(/-/g, '') === got)) {
        return { ok: false, reason: 'hyphen', expected: expected, got: gotRaw };
      }
      if (policy.space === 'significant' && A._collapse(got) === A._collapse(norm)) {
        return { ok: false, reason: 'space', expected: expected, got: gotRaw };
      }
      if (A._withoutArticles(A._tokens(norm)).join(' ') === A._withoutArticles(A._tokens(got)).join(' ') && got !== norm) {
        return { ok: false, reason: 'article', expected: expected, got: gotRaw };
      }
      if (policy.stress === 'significant' && A._withoutDiacritics(got) === A._withoutDiacritics(norm)) {
        return { ok: false, reason: 'stress', expected: expected, got: gotRaw };
      }
      if (A._near(got, norm)) return { ok: false, reason: 'near', expected: expected, got: gotRaw };
    }
    return { ok: false, reason: 'exact', expected: accepted[0], got: gotRaw };
  };

  /** Короткая человеческая расшифровка политики (для интерфейса). */
  A.describePolicy = function (policy) {
    var parts = [];
    if (policy.case === 'sensitive') parts.push('регистр букв важен');
    if (policy.article === 'ignored') parts.push('артикль не проверяется');
    if (policy.apostrophe === 'required') parts.push('апостроф обязателен');
    if (policy.hyphen === 'ignore') parts.push('дефис не проверяется');
    if (policy.space === 'collapse') parts.push('пробелы можно схлопывать');
    if (policy.stress === 'ignore') parts.push('диакритика не проверяется');
    if (policy.empty === 'accept') parts.push('если ничего не нужно, поле остаётся пустым');
    return parts.length ? parts.join('; ') : 'точное совпадение';
  };

  /** Допустимые варианты, которые стоит показать после верного ответа. */
  A.alternativesFor = function (task) {
    var out = [];
    ((task && task.accepted) || []).forEach(function (item) {
      var value = typeof item === 'string' ? item : (item && item.value) || '';
      if (value && value !== A.NOTHING && out.indexOf(value) < 0) out.push(value);
    });
    return out;
  };

  A._tokens = function (value) {
    return String(value || '').split(/[ \t]+/).filter(function (token) { return token !== ''; });
  };
  A._withoutArticles = function (tokens) {
    return tokens.filter(function (token) { return ARTICLES.indexOf(token) < 0; });
  };
  A._dropArticles = function (value) {
    return String(value || '').replace(/(^|\s)(?:a|an|the)(?=\s|$)/g, '$1').replace(/\s+/g, ' ').replace(/^\s+|\s+$/g, '');
  };
  A._collapse = function (value) { return String(value || '').replace(/[ \t]/g, ''); };
  A._stripApostrophes = function (value) { return String(value || '').replace(/'/g, ''); };
  A._withoutDiacritics = function (value) {
    if (typeof value.normalize !== 'function') return value;
    return value.normalize('NFD').replace(/[\u0300-\u036f\u00b4\u02ca\u02c7\u02d8]/g, '');
  };
  A._differsOnlyByCase = function (got, expected, policy) {
    return policy.case === 'sensitive' && got !== expected && got.toLowerCase() === expected.toLowerCase();
  };
  /** «Почти совпало»: другая форма слова или лишний/пропущенный знак. */
  A._near = function (got, expected) {
    var a = U.letters(got), b = U.letters(expected);
    if (!a || !b) return false;
    if (a.indexOf(b) >= 0 || b.indexOf(a) >= 0) return true;
    var common = 0;
    for (var i = 0; i < Math.min(a.length, b.length); i++) {
      if (a.charAt(i) !== b.charAt(i)) break;
      common++;
    }
    return common >= 3 && Math.abs(a.length - b.length) <= 2;
  };

  /* --------------------------------------------------------------------- *
   * 4. Загрузка контента / content
   * --------------------------------------------------------------------- */
  var C = CT.content = {
    bank: [], analogous: [], topics: {}, order: [], tools: {}, types: {}, instructions: {},
    counts: {}, byYear: {}, periods: {}, lessons: {}, figures: {}, rules: [], checklist: [],
    mistakes: { errors: {}, checklist: [] }, meta: {}, vectors: [], loaded: false, subject: SUBJECT,

    load: function () {
      var self = this;
      return Promise.all([
        B.getContent('bank'), B.getContent('analogous'), B.getContent('topics'),
        B.getContent('ui_strings'), B.getContent('mistakes'),
      ]).then(function (data) {
        var bank = data[0], analog = data[1], topics = data[2];
        self.bank = bank.tasks || [];
        self.analogous = analog.tasks || [];
        self.topics = topics.topics || {};
        self.order = topics.order || Object.keys(self.topics);
        self.tools = topics.tools || {};
        self.types = topics.types || {};
        self.instructions = topics.instructions || {};
        self.counts = topics.counts || {};
        self.byYear = topics.byYear || {};
        self.periods = topics.periods || {};
        self.lessons = topics.lessons || {};
        self.figures = topics.figures || {};
        self.rules = (topics.rules && topics.rules.groups) || [];
        self.checklist = topics.checklist || [];
        I.strings = (data[3] && data[3].strings) || {};
        self.mistakes = data[4] || { errors: {}, checklist: [] };
        self.meta = bank.meta || {};
        self.loaded = true;
        return data;
      });
    },

    taskById: function (id) {
      for (var i = 0; i < this.bank.length; i++) if (this.bank[i].id === id) return this.bank[i];
      for (var j = 0; j < this.analogous.length; j++) if (this.analogous[j].id === id) return this.analogous[j];
      return null;
    },
    /** Выпущенные варианты: 2026 — готовый, прежние годы помечены как «в работе». */
    variants: function () {
      var self = this, years = {};
      this.bank.forEach(function (task) {
        if (!task.year) return;
        (years[task.year] = years[task.year] || []).push(task);
      });
      return Object.keys(years).sort().map(function (year) {
        var list = years[year].slice().sort(function (a, b) {
          if (a.part !== b.part) return a.part === 'A' ? -1 : 1;
          return a.n - b.n;
        });
        return {
          year: Number(year), key: 'year-' + year, tasks: list,
          partA: list.filter(function (t) { return t.part === 'A'; }).length,
          partB: list.filter(function (t) { return t.part === 'B'; }).length,
        };
      }).reverse();
    },
    /** Годы, которые ещё не выпущены (показываются как план, не как вариант). */
    plannedYears: function () { return (this.periods.planned || []).slice().sort(); },
    topicTitle: function (key) { return I.pick(this.topics[key]) || key; },
    topicsWithTasks: function () {
      var self = this;
      return this.order.filter(function (topic) { return self.tasksByTopic(topic).length > 0; });
    },
    tasksByTopic: function (topic) { return this.bank.filter(function (t) { return t.topic === topic; }); },
    analogByTopic: function (topic) { return this.analogous.filter(function (t) { return t.topic === topic; }); },
    lessonById: function (id) { return this.lessons[id] || null; },
    figureById: function (id) { return this.figures[id] || null; },

    /** Карточки справочника, относящиеся к теме задания. */
    ruleGroupsFor: function (topic) {
      var entry = this.topics[topic];
      var wanted = entry && entry.rule;
      return this.rules.filter(function (group) {
        if (!wanted) return false;
        return group.rule === wanted || group.id === wanted ||
          (group.items || []).some(function (item) { return item.id === wanted; });
      });
    },
    /** Уроки, относящиеся к теме (открываются при неверном ответе). */
    lessonsForTopic: function (topic) {
      var self = this;
      return Object.keys(this.lessons)
        .map(function (id) { return self.lessons[id]; })
        .filter(function (lesson) { return lesson.topic === topic; });
    },
    /** Диагноз типичной ошибки по тегам задания. */
    diagnoses: function (task) {
      var out = [], errors = this.mistakes.errors || {};
      ((task && task.tags) || []).forEach(function (tag) {
        if (errors[tag] && out.indexOf(errors[tag]) < 0) out.push(errors[tag]);
      });
      if (!out.length && errors.__default) out.push(errors.__default);
      return out;
    },
    /** Раздел справочника, к которому относится тема задания. */
    ruleGroupFor: function (task) {
      var wanted = (task && task.rule) || ((this.topics[task && task.topic] || {}).rule);
      if (!wanted) return null;
      for (var i = 0; i < this.rules.length; i++) {
        var group = this.rules[i];
        if (group.rule === wanted || group.id === wanted) return group;
      }
      // ключ может указывать прямо на карточку внутри раздела
      return this.ruleItemFor(wanted).group;
    },
    /** Карточка справочника по её ключу: {group, item} (используется разбором ошибки). */
    ruleItemFor: function (ruleId) {
      for (var i = 0; i < this.rules.length; i++) {
        var group = this.rules[i];
        var items = group.items || [];
        for (var j = 0; j < items.length; j++) {
          if (items[j].id === ruleId) return { group: group, item: items[j] };
        }
      }
      return { group: null, item: null };
    },
    /** Почему задание попало в эту тему: тип упражнения словами. */
    typeTitle: function (type) { return I.pick(this.types[type]) || type; },
    instructionFor: function (task) {
      if (task && task.instruction) return task.instruction;
      return this.instructions[(task && task.type) || 'choice'] || { ru: '', en: '' };
    },
  };

  /* --------------------------------------------------------------------- *
   * 5. Аналитика / analytics
   * --------------------------------------------------------------------- */
  var AN = CT.analytics = {};

  /** Пустая запись прогресса (одна структура на обе платформы). */
  AN.empty = function () {
    return {
      attempts: [],      // завершённые прогоны (варианты, экзамены, наборы)
      tasksDone: 0,      // решённых заданий всего (включая тренировку)
      correct: 0,
      seconds: 0,
      byTopic: {},       // topic → { correct, total }
      byYear: {},        // year  → { correct, total }
      daily: {},         // «ГГГГ-ММ-ДД» → число заданий
      streak: 0,
      best: 0,
      goal: 20,
      scratch: {},       // черновики по заданиям
    };
  };

  /** Сводка по всему прогрессу (то, что видно на главной и в статистике). */
  AN.totals = function (progress) {
    progress = progress || AN.empty();
    var tasks = progress.tasksDone || 0;
    var correct = progress.correct || 0;
    var seconds = progress.seconds || 0;
    var attempts = progress.attempts || [];
    if (!tasks && attempts.length) {
      attempts.forEach(function (attempt) {
        (attempt.results || []).forEach(function (result) {
          tasks++;
          if (result.correct) correct++;
        });
        seconds += attempt.seconds || 0;
      });
    }
    return {
      tests: attempts.length,
      tasks: tasks,
      correct: correct,
      accuracy: tasks ? correct / tasks : 0,
      minutes: Math.round(seconds / 60),
      avgSeconds: tasks ? seconds / tasks : 0,
      byTopic: progress.byTopic || {},
      byYear: progress.byYear || {},
    };
  };

  /** Статистика по темам: topic → { correct, total, rate }. */
  AN.topicStats = function (progress) {
    var source = (progress || {}).byTopic || {};
    var stats = {};
    Object.keys(source).forEach(function (topic) {
      var entry = source[topic] || {};
      var total = entry.total || 0;
      var correct = entry.correct || 0;
      stats[topic] = { correct: correct, total: total, rate: total ? correct / total : 0 };
    });
    return stats;
  };

  /** Статистика по годам вариантов: year → { correct, total, rate, tests }. */
  AN.yearStats = function (progress) {
    var stats = {};
    var source = (progress || {}).byYear || {};
    Object.keys(source).forEach(function (year) {
      var entry = source[year] || {};
      var total = entry.total || 0;
      var correct = entry.correct || 0;
      stats[year] = { correct: correct, total: total, rate: total ? correct / total : 0, tests: entry.tests || 0 };
    });
    return stats;
  };

  /** Слабые темы (не меньше трёх заданий), начиная с самой слабой. */
  AN.weakTopics = function (progress, limit) {
    var stats = AN.topicStats(progress);
    return Object.keys(stats)
      .map(function (topic) { return { topic: topic, rate: stats[topic].rate, total: stats[topic].total }; })
      .filter(function (item) { return item.total >= 3; })
      .sort(function (a, b) { return a.rate - b.rate || b.total - a.total; })
      .slice(0, limit || 3);
  };

  /** Дни подряд с занятиями (сегодня или вчера — начало серии). */
  AN.computeStreak = function (progress) {
    var days = Object.keys((progress || {}).daily || {}).filter(function (day) {
      return (progress.daily[day] || 0) > 0;
    }).sort();
    if (!days.length) return 0;
    var today = U.today();
    var last = days[days.length - 1];
    if (U.daysBetween(last, today) > 1) return 0;
    var streak = 1;
    for (var i = days.length - 1; i > 0; i--) {
      if (U.daysBetween(days[i - 1], days[i]) === 1) streak++;
      else break;
    }
    return streak;
  };

  /**
   * Записать одно решённое задание: общие счётчики, разбивка по темам и годам,
   * календарь занятий и серия дней.  Вызывается и в тренировке, и при
   * завершении экзамена — так статистика не теряет ни одного задания.
   */
  AN.record = function (progress, task, correct, seconds) {
    progress.tasksDone = (progress.tasksDone || 0) + 1;
    if (correct) progress.correct = (progress.correct || 0) + 1;
    progress.seconds = (progress.seconds || 0) + (seconds || 0);

    var today = U.today();
    progress.daily = progress.daily || {};
    progress.daily[today] = (progress.daily[today] || 0) + 1;
    if (progress.daily[today] > (progress.best || 0)) progress.best = progress.daily[today];

    var topic = (task && task.topic) || 'other';
    progress.byTopic = progress.byTopic || {};
    var topicEntry = progress.byTopic[topic] = progress.byTopic[topic] || { correct: 0, total: 0 };
    topicEntry.total++;
    if (correct) topicEntry.correct++;

    var year = task && task.year ? task.year : 0;
    if (year) {
      progress.byYear = progress.byYear || {};
      var yearEntry = progress.byYear[year] = progress.byYear[year] || { correct: 0, total: 0 };
      yearEntry.total++;
      if (correct) yearEntry.correct++;
    }
    progress.streak = AN.computeStreak(progress);
    return progress;
  };

  /** Итоги одной попытки: проценты, разбивка по частям, список ошибок. */
  AN.attemptSummary = function (attempt) {
    var results = (attempt && attempt.results) || [];
    var correct = results.filter(function (result) { return result.correct; }).length;
    var byPart = { A: { correct: 0, total: 0 }, B: { correct: 0, total: 0 } };
    results.forEach(function (result) {
      var bucket = byPart[result.part] || (byPart[result.part] = { correct: 0, total: 0 });
      bucket.total++;
      if (result.correct) bucket.correct++;
    });
    var percent = results.length ? correct / results.length : 0;
    return {
      correct: correct,
      total: results.length,
      wrong: results.length - correct,
      percent: percent,
      grade: Math.round(percent * 100),
      byPart: byPart,
      seconds: (attempt && attempt.seconds) || 0,
      mistakes: results.filter(function (result) { return !result.correct; }),
    };
  };

  global.CT = CT;
})(typeof globalThis !== 'undefined' ? globalThis : this);

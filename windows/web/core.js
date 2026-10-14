/* core.js — общее ядро интерфейса «Репетитор ЦТ: Русский язык»
 * (Android WebView и Windows Go).
 *
 * Здесь всё, что не зависит от платформы: загрузка банка (только своего
 * предмета — чужой банк отвергается), предметная проверка ответов (тот же
 * контракт, что content_src/checker.py и AnswerChecker.kt), аналитика
 * прогресса и хранилище с автосохранением.
 *
 * Shared engine: subject-checked content loading, the language answer checker
 * (no math normalisation), analytics and storage. Platform differences live
 * behind CT.bridge (window.CTNative on Android, the loopback HTTP API on
 * Windows).
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
  var B = CT.bridge = {
    native: typeof global.CTNative !== 'undefined' ? global.CTNative : null,
    platform: 'web',
    info: {},
    /**
     * Состояние платформы.  Обе платформы отвечают одной структурой
     * {app:{...}, content:{...}, blobs:[...]} — приводим её к плоскому виду,
     * которым пользуется интерфейс (platform, dataDir, version, …).
     */
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
        // Native network IO runs on an executor, never on the WebView thread.
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
   * 3. Проверка ответов / subject answer checker
   *
   * Port of content_src/checker.py (same contract, same vectors). Nothing is
   * removed implicitly: spaces, hyphens, ё, case and stress marks are part of
   * the answer unless the task's explicit policy says otherwise.
   * --------------------------------------------------------------------- */
  var A = CT.answer = {};
  A.WHITESPACE = '\t\n\u000b\u000c\r \u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008' +
    '\u2009\u200a\u2028\u2029\u202f\u205f\u3000';
  A.VOWELS = 'аеёиоуыэюя';
  var ACUTE = '\u0301', GRAVE = '\u0300';

  A.nfc = function (text) { return String(text).normalize('NFC'); };

  /** Trim the ends; a run of whitespace becomes ONE space (never deleted). */
  A.squeeze = function (text) {
    var out = '', pending = false;
    for (var i = 0; i < text.length; i++) {
      var ch = text.charAt(i);
      if (A.WHITESPACE.indexOf(ch) >= 0) { pending = true; continue; }
      if (pending && out) out += ' ';
      pending = false;
      out += ch;
    }
    return out;
  };

  function number(token) {
    if (!/^[0-9]+$/.test(token) || (token.length > 1 && token.charAt(0) === '0')) return null;
    return parseInt(token, 10);
  }

  /** Numbers 1..max in input order or null (duplicates are invalid). */
  A.parseNumbers = function (raw, max) {
    var text = A.squeeze(A.nfc(raw));
    if (!text) return null;
    var tokens = text.split(/[ ,;]+/).filter(function (token) { return token !== ''; });
    if (!tokens.length) return null;
    if (tokens.length === 1 && max <= 9 && tokens[0].length > 1) {
      if (!/^[0-9]+$/.test(tokens[0])) return null;
      tokens = tokens[0].split('');
    }
    var values = [];
    for (var i = 0; i < tokens.length; i++) {
      if (max <= 9 && tokens[i].length !== 1) return null;
      var value = number(tokens[i]);
      if (value === null || value < 1 || value > max || values.indexOf(value) >= 0) return null;
      values.push(value);
    }
    return values;
  };

  A.foldWord = function (text, spec) {
    text = A.nfc(text);
    if (spec.hyphen === 'typographic') text = text.replace(/[\u2010\u2011]/g, '-');
    text = A.squeeze(text);
    if (spec.case === 'insensitive') text = text.toLowerCase();
    if (spec.yo === 'e-equals-yo') text = text.replace(/ё/g, 'е').replace(/Ё/g, 'Е');
    return text;
  };

  A.parseStress = function (raw, word) {
    var text = A.squeeze(A.nfc(raw));
    if (!text || text.indexOf(' ') >= 0 || text.indexOf(GRAVE) >= 0) return null;
    var marks = text.split(ACUTE).length - 1;
    if (marks > 1) return null;
    var position, base;
    if (marks === 1) {
      position = text.indexOf(ACUTE) - 1;
      base = text.replace(ACUTE, '');
      if (position < 0 || base.toLowerCase() !== word || A.VOWELS.indexOf(base.charAt(position).toLowerCase()) < 0) return null;
      return position;
    }
    var capitals = [];
    for (var i = 0; i < text.length; i++) if (text.charAt(i) !== text.charAt(i).toLowerCase()) capitals.push(i);
    if (capitals.length !== 1) return null;
    position = capitals[0];
    if (text.toLowerCase() !== word || A.VOWELS.indexOf(text.charAt(position).toLowerCase()) < 0) return null;
    return position;
  };

  A.parseMatch = function (raw, labels, right) {
    var text = A.squeeze(A.nfc(raw)).toUpperCase().replace(/[ ,;:\-]/g, '');
    if (!text || !/^(?:[А-ЯЁ][0-9]{1,2})+$/.test(text)) return null;
    var pairs = {}, re = /([А-ЯЁ])([0-9]{1,2})/g, found;
    while ((found = re.exec(text))) {
      var value = number(found[2]);
      if (labels.indexOf(found[1]) < 0 || pairs[found[1]] !== undefined || value === null || value < 1 || value > right) return null;
      pairs[found[1]] = value;
    }
    return Object.keys(pairs).length === labels.length ? pairs : null;
  };

  function sameList(a, b) {
    if (!a || !b || a.length !== b.length) return false;
    for (var i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
    return true;
  }
  function sorted(list) { return list.slice().sort(function (x, y) { return x - y; }); }

  /** Grade one answer against a check spec; never throws, unknown types fail. */
  A.checkSpec = function (user, spec) {
    var raw = user === null || user === undefined ? '' : String(user);
    if (!spec) return false;
    var values, normalized;
    switch (spec.type) {
      case 'multi':
        values = A.parseNumbers(raw, spec.options);
        return values !== null && sameList(sorted(values), spec.answer);
      case 'single':
        values = A.parseNumbers(raw, spec.options);
        return values !== null && values.length === 1 && values[0] === spec.answer;
      case 'numbers':
        values = A.parseNumbers(raw, spec.max);
        if (values === null) return false;
        return spec.order === 'ordered' ? sameList(values, spec.answer) : sameList(sorted(values), spec.answer);
      case 'word':
        normalized = A.nfc(raw);
        if (normalized.indexOf(ACUTE) >= 0 || normalized.indexOf(GRAVE) >= 0) return false;
        var got = A.foldWord(raw, spec);
        if (!got) return false;
        return [spec.answer].concat(spec.accept || []).some(function (candidate) { return A.foldWord(candidate, spec) === got; });
      case 'stress':
        return A.parseStress(raw, spec.word) === spec.answer;
      case 'match':
        var pairs = A.parseMatch(raw, spec.labels, spec.right);
        return pairs !== null && spec.labels.every(function (label) { return pairs[label] === spec.answer[label]; });
      case 'integer':
        var value = number(A.squeeze(A.nfc(raw)));
        return value !== null && value === spec.answer;
      default:
        return false;
    }
  };

  A.check = function (user, task) { return !!task && A.checkSpec(user, task.check); };

  /** The canonical answer in a readable form. */
  A.display = function (spec) {
    if (!spec) return '';
    if (spec.type === 'multi' || spec.type === 'numbers') return spec.answer.join(', ');
    if (spec.type === 'single' || spec.type === 'integer') return String(spec.answer);
    if (spec.type === 'word') return spec.answer;
    if (spec.type === 'stress') return spec.display;
    if (spec.type === 'match') return spec.labels.map(function (label) { return label + spec.answer[label]; }).join(' ');
    return '';
  };

  /** The learner's answer in a readable form (numbers normalised when valid). */
  A.formatUser = function (user, task) {
    var raw = user === null || user === undefined ? '' : String(user);
    if (!raw.trim() || !task) return '';
    var spec = task.check, values;
    if (spec.type === 'multi' || spec.type === 'single') values = A.parseNumbers(raw, spec.options);
    if (spec.type === 'numbers') values = A.parseNumbers(raw, spec.max);
    if (values) return (spec.type === 'numbers' && spec.order === 'ordered' ? values : sorted(values)).join(', ');
    return raw;
  };

  /** Items judged wrongly in a set answer (extra or missing choices), 1-based. */
  A.misjudged = function (user, task) {
    if (!task || !Array.isArray(task.itemRules)) return null;
    var spec = task.check;
    if (!(spec.type === 'multi' || (spec.type === 'numbers' && spec.order === 'unordered'))) return null;
    var values = A.parseNumbers(user === undefined || user === null ? '' : String(user), spec.options || spec.max) || [];
    var out = [];
    for (var i = 1; i <= task.itemRules.length; i++) {
      if ((values.indexOf(i) >= 0) !== (spec.answer.indexOf(i) >= 0)) out.push(i);
    }
    return out;
  };

  /* --------------------------------------------------------------------- *
   * 4. Загрузка контента / content (subject-checked)
   * --------------------------------------------------------------------- */
  CT.SUBJECT = 'russian';
  CT.PACKAGE = 'by.ziv.ctrussian';
  var C = CT.content = {
    bank: [], analogous: [], rules: [], mistakes: { errors: {}, checklist: [] },
    topics: {}, order: [], sections: {}, blueprint: [], lessons: {}, figures: {}, study: {}, sources: {},
    memos: [], meta: {}, periods: [], specification: {}, disclaimer: {}, ruleMeta: {},
    loaded: false,

    /** A content pack belongs to this tutor only if subject and package match. */
    subjectOk: function (meta) {
      return !!meta && meta.subject === CT.SUBJECT && (!meta.package || meta.package === CT.PACKAGE);
    },

    load: function () {
      var self = this;
      return Promise.all([
        B.getContent('bank'), B.getContent('analogous'), B.getContent('topics'),
        B.getContent('rules'), B.getContent('ui_strings'), B.getContent('mistakes'),
      ]).then(function (data) {
        var bank = data[0] || {}, analog = data[1] || {}, topics = data[2] || {};
        if (!self.subjectOk(bank.meta) || !self.subjectOk(analog.meta) || topics.subject !== CT.SUBJECT) {
          throw new Error('foreign content pack rejected: subject must be ' + CT.SUBJECT);
        }
        self.bank = bank.tasks || [];
        self.analogous = analog.tasks || [];
        self.topics = topics.topics || {};
        self.order = topics.order || Object.keys(self.topics);
        self.sections = topics.sections || {};
        self.blueprint = topics.blueprint || [];
        self.study = topics.study || {};
        self.lessons = topics.lessons || {};
        self.figures = topics.figures || {};
        self.sources = topics.sources || {};
        self.memos = topics.memos || [];
        self.ruleMeta = topics.rules || {};
        self.periods = topics.periods || [];
        self.specification = topics.specification || {};
        self.disclaimer = topics.disclaimer || {};
        self.rules = (data[3] && data[3].groups) || [];
        I.strings = (data[4] && data[4].strings) || {};
        self.mistakes = data[5] || { errors: {}, checklist: [] };
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
    variants: function () {
      var years = {};
      this.bank.forEach(function (task) { (years[task.year] = years[task.year] || []).push(task); });
      return Object.keys(years).sort().map(function (year) {
        var list = years[year].slice().sort(function (a, b) {
          if (a.part !== b.part) return a.part === 'A' ? -1 : 1;
          return a.n - b.n;
        });
        return { year: Number(year), key: 'year-' + year, tasks: list,
          partA: list.filter(function (t) { return t.part === 'A'; }).length,
          partB: list.filter(function (t) { return t.part === 'B'; }).length };
      }).reverse();
    },
    /** A mixed exam: one task per blueprint slot from random variants. */
    mixedExam: function () {
      var bySlot = {};
      this.bank.forEach(function (task) { var slot = task.part + task.n; (bySlot[slot] = bySlot[slot] || []).push(task); });
      return this.blueprint.map(function (entry) {
        var pool = bySlot[entry.slot] || [];
        return pool[Math.floor(Math.random() * pool.length)];
      }).filter(Boolean);
    },
    topicTitle: function (key) { return I.pick(this.topics[key]) || key; },
    ruleTitle: function (id) { return I.pick((this.ruleMeta[id] || {}).title) || id; },
    tasksByTopic: function (topic) { return this.bank.filter(function (t) { return t.topic === topic; }); },
    analogByTopic: function (topic) { return this.analogous.filter(function (t) { return t.topic === topic; }); },
    analogByRule: function (rule) { return this.analogous.filter(function (t) { return t.rule === rule; }); },
    tasksByRule: function (rule) {
      return this.bank.concat(this.analogous).filter(function (t) { return (t.rules || [t.rule]).indexOf(rule) >= 0; });
    },
    rulesOfTopic: function (topic) { return (this.study[topic] || {}).lessons || []; },
    studyFor: function (topic) { return this.study[topic] || null; },
    lessonById: function (id) { return this.lessons[id] || null; },
    figureById: function (id) { return this.figures[id] || null; },

    /** Rules to remediate: those of misjudged items when known, else all rules of the task. */
    rulesFor: function (task, user) {
      if (!task) return [];
      var wrong = A.misjudged(user, task);
      if (wrong && wrong.length) {
        var out = [];
        wrong.forEach(function (index) {
          var rule = task.itemRules[index - 1];
          if (rule && out.indexOf(rule) < 0) out.push(rule);
        });
        if (out.length) return out;
      }
      return (task.rules || [task.rule]).slice();
    },

    /** Typical-error diagnoses for the given rules. */
    diagnoses: function (rules) {
      var errors = this.mistakes.errors || {}, out = [];
      (rules || []).forEach(function (rule) { if (errors[rule] && out.indexOf(errors[rule]) < 0) out.push(errors[rule]); });
      return out;
    },
  };

  /* --------------------------------------------------------------------- *
   * 6. Аналитика / analytics
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
      byRule: {},        // rule  → { correct, total } — remediation by concrete rule
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
      // страховка для данных, записанных до появления счётчиков
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

  /** Статистика по правилам: rule → { correct, total, rate }. */
  AN.ruleStats = function (progress) {
    var source = (progress || {}).byRule || {}, stats = {};
    Object.keys(source).forEach(function (rule) {
      var entry = source[rule] || {}, total = entry.total || 0, correct = entry.correct || 0;
      stats[rule] = { correct: correct, total: total, rate: total ? correct / total : 0 };
    });
    return stats;
  };

  /** Самые слабые правила (не меньше двух попыток). */
  AN.weakRules = function (progress, limit) {
    var stats = AN.ruleStats(progress);
    return Object.keys(stats).map(function (rule) { return { rule: rule, rate: stats[rule].rate, total: stats[rule].total }; })
      .filter(function (item) { return item.total >= 2 && item.rate < 1; })
      .sort(function (a, b) { return a.rate - b.rate || b.total - a.total; })
      .slice(0, limit || 5);
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
    var gap = U.daysBetween(last, today);
    if (gap > 1) return 0;
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

    var rule = (task && task.rule) || '';
    if (rule) {
      progress.byRule = progress.byRule || {};
      var ruleEntry = progress.byRule[rule] = progress.byRule[rule] || { correct: 0, total: 0 };
      ruleEntry.total++;
      if (correct) ruleEntry.correct++;
    }

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

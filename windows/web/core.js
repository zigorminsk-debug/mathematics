/* core.js — общее ядро интерфейса (Android WebView и Windows Go).
 *
 * Здесь всё, что не зависит от платформы: загрузка банка заданий, алгоритм
 * проверки ответов (он же продублирован на Kotlin для нативных тестов),
 * безопасный калькулятор без eval, построение графиков, аналитика прогресса
 * и хранилище с автосохранением.
 *
 * Shared engine of the UI: content loading, the portable answer checker,
 * a safe expression calculator (no eval), plotting, analytics and storage.
 * Platform differences live behind CT.bridge (window.CTNative on Android,
 * fetch() to the local HTTP API on Windows).
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
   * 3. Проверка ответов / answer checker
   * --------------------------------------------------------------------- */
  var A = CT.answer = {};

  /** Нормализация: пробелы, юникодные минусы, запятая↔точка, префиксы, ×·. */
  A.normalize = function (value) {
    if (value === null || value === undefined) return '';
    var s = String(value).trim().toLowerCase();
    s = s.replace(/\u00a0/g, ' ');
    s = s.replace(/[\u2212\u2013\u2014\u2015]/g, '-');   // − – — ―
    s = s.replace(/\u00d7/g, '*');                        // ×
    s = s.replace(/\u00b7/g, '*');                        // ·
    s = s.replace(/\u2219/g, '*');                        // ∙
    s = s.replace(/\u0445/g, 'x');                        // русская х
    s = s.replace(/\u0443/g, 'y');                        // русская у
    s = s.replace(/\u03c0/g, 'pi');                       // π
    s = s.replace(/\u221a/g, 'sqrt');                     // √
    s = s.replace(/^\s*(ответ|answer)\s*[:=]?\s*/i, '');
    s = s.replace(/^\s*[a-zа-я]{1,2}\s*[:=]\s*/i, '');    // "x = 12", "y:12"
    s = s.replace(/\s+/g, '');
    s = s.replace(/^\((.*)\)$/, '$1');                    // (12) → 12
    s = s.replace(/,/g, '.');
    if (s.endsWith('.')) s = s.slice(0, -1);              // «12.» — это «12»
    return s;
  };

  /** Значение — целое число (для строгого сравнения целых ответов). */
  A.isInteger = function (value) {
    return typeof value === 'number' && isFinite(value) && Math.abs(value % 1) < 1e-12;
  };

  /** Строка → рациональное число или null. Понимает «3», «0.75», «3/4», «-2,5». */
  A.parseNumber = function (value) {
    if (value === null || value === undefined) return null;
    if (typeof value === 'number') return isFinite(value) ? value : null;
    var s = A.normalize(value);
    if (!/^[-+]?(\d+(\.\d+)?|\.\d+)([-+*\/]\d+(\.\d+)?)*$/.test(s)) return null;
    try {
      var frac = A.evalFraction(s);
      return frac === null || !isFinite(frac) ? null : frac;
    } catch (e) { return null; }
  };

  /** Точная арифметика по мере возможности (дроби), с запасным float. */
  A.evalFraction = function (s) {
    var parts = [];
    var sign = 1;
    var tokens = s.match(/[-+*/]|[^-+*/]+/g) || [];
    if (!tokens.length) return null;
    for (var i = 0; i < tokens.length; i++) {
      var tok = tokens[i];
      if (tok === '+' || tok === '-') parts.push(['op', tok]);
      else if (tok === '*' || tok === '/') parts.push(['op', tok]);
      else parts.push(['num', parseFloat(tok)]);
    }
    // сначала * и /
    var out = [];
    for (var j = 0; j < parts.length; j++) {
      var part = parts[j];
      if (part[0] === 'op' && (part[1] === '*' || part[1] === '/')) {
        var prev = out.pop();
        var next = parts[++j];
        if (!prev || !next || prev[0] !== 'num' || next[0] !== 'num') return null;
        out.push(['num', part[1] === '*' ? prev[1] * next[1] : prev[1] / next[1]]);
      } else {
        if (part[0] === 'num' && j === 0) out.push(part);
        else out.push(part);
      }
    }
    // затем + и -
    var acc = null, op = '+';
    for (var k = 0; k < out.length; k++) {
      var item = out[k];
      if (item[0] === 'op') { op = item[1]; continue; }
      if (acc === null) { acc = op === '-' ? -item[1] : item[1]; op = '+'; continue; }
      acc = op === '+' ? acc + item[1] : acc - item[1];
      op = '+';
    }
    return acc;
  };

  /** Значения из задания: правильный ответ и «принимаемые» записи. */
  A.candidates = function (task) {
    var list = [];
    if (!task) return list;
    var push = function (value) { if (value !== null && value !== undefined && String(value) !== '') list.push(String(value)); };
    if (typeof task.answer === 'string') push(task.answer);
    else if (task.answer && typeof task.answer === 'object') { push(A.pick(task.answer)); }
    if (Array.isArray(task.accept)) task.accept.forEach(function (v) { push(A.pick(v)); });
    return list;
  };

  /** Двуязычное значение из задания. */
  A.pick = function (value) {
    if (value === null || value === undefined) return '';
    return typeof value === 'string' ? value : I.pick(value);
  };

  /** Совпадает ли ответ пользователя с «эталонным» ответом задания. */
  A.check = function (userAnswer, task) {
    if (!task) return false;
    var got = String(userAnswer === null || userAnswer === undefined ? '' : userAnswer);
    var normalizedUser = A.normalize(got);
    if (task.answerType === 'choice') {
      // Вариант сравнивается ровно (без численных допусков): «8/2» — не ответ «4».
      var variants = A.candidates(task);
      for (var c = 0; c < variants.length; c++) {
        if (A.normalize(variants[c]) === normalizedUser) return true;
      }
      return false;
    }
    var user = normalizedUser;
    if (!user) return false;
    var candidates = A.candidates(task);
    var i, cn;
    for (i = 0; i < candidates.length; i++) {
      if (A.normalize(candidates[i]) === user) return true;
    }
    var userNum = A.parseNumber(userAnswer);
    if (userNum !== null) {
      for (i = 0; i < candidates.length; i++) {
        cn = A.parseNumber(candidates[i]);
        if (cn === null) continue;
        var diff = Math.abs(userNum - cn);
        if (diff <= 1e-9) return true;
        if (A.isInteger(cn)) continue;                                // целое — только точно
        if (diff <= 5e-4 * Math.max(1, Math.abs(cn))) return true;    // «0,833» для 5/6
      }
    }
    // Третий рубеж: ответы-выражения («√2/2», «2π») и написанные от руки
    // десятичные приближения. Для обычных чисел он не включается — иначе
    // «1000,5» подошло бы к ответу «1000».
    var userVal = CT.math.value(userAnswer);
    if (userVal === null) return false;
    var userIsExpression = A.isExpression(userAnswer);
    for (i = 0; i < candidates.length; i++) {
      if (!userIsExpression && !A.isExpression(candidates[i])) continue;
      var candidateVal = CT.math.value(candidates[i]);
      if (candidateVal === null) continue;
      if (Math.abs(userVal - candidateVal) <= 1e-3 * Math.max(1, Math.abs(candidateVal))) return true;
    }
    return false;
  };

  /** Ответ записан как выражение (корень, π, дробная степень), а не как число. */
  A.isExpression = function (value) {
    if (value === null || value === undefined) return false;
    return /sqrt|pi|\^|\(/.test(A.normalize(value)) && A.parseNumber(value) === null;
  };

  /* --------------------------------------------------------------------- *
   * 4. Безопасная математика / calculator & plotting (no eval)
   * --------------------------------------------------------------------- */
  var M = CT.math = {};

  var FUNCTIONS = {
    sin: function (x) { return Math.sin(x); },
    cos: function (x) { return Math.cos(x); },
    tan: function (x) { return Math.tan(x); },
    tg: function (x) { return Math.tan(x); },
    cot: function (x) { return 1 / Math.tan(x); },
    ctg: function (x) { return 1 / Math.tan(x); },
    asin: Math.asin, acos: Math.acos, atan: Math.atan,
    arcsin: Math.asin, arccos: Math.acos, arctg: Math.atan, arctan: Math.atan,
    sqrt: Math.sqrt, abs: Math.abs, ln: Math.log, lg: function (x) { return Math.log(x) / Math.LN10; },
    log: function (x) { return Math.log(x) / Math.LN10; },
    exp: Math.exp, round: function (x) { return Math.round(x); },
    floor: Math.floor, ceil: Math.ceil, sign: function (x) { return x > 0 ? 1 : (x < 0 ? -1 : 0); },
  };
  var CONSTANTS = { pi: Math.PI, 'π': Math.PI, e: Math.E, tau: 2 * Math.PI };

  /** Разбор выражения в массив чисел/операторов/функций. */
  function tokenize(src) {
    var s = String(src);
    s = s.replace(/\u2212/g, '-').replace(/\u00b7|\u00d7|\u2219/g, '*').replace(/,/g, '.').replace(/\u221a/g, 'sqrt');
    s = s.replace(/\u03c0/g, 'pi').replace(/\u00b2/g, '^2').replace(/\u00b3/g, '^3');
    s = s.replace(/\[/g, '(').replace(/\]/g, ')').replace(/\{/g, '(').replace(/\}/g, ')');
    var tokens = [], i = 0, ch, rest;
    while (i < s.length) {
      ch = s[i];
      if (/\s/.test(ch)) { i++; continue; }
      if (/[0-9.]/.test(ch)) {
        rest = /^\d*\.?\d*(e[-+]?\d+)?/i.exec(s.slice(i))[0];
        if (!rest || rest === '.') throw new Error('bad number');
        tokens.push({ type: 'num', value: parseFloat(rest) });
        i += rest.length;
        continue;
      }
      rest = /^[a-zA-Zа-яА-Я_]+/.exec(s.slice(i));
      if (rest) {
        var name = rest[0].toLowerCase();
        tokens.push({ type: 'name', value: name });
        i += name.length;
        continue;
      }
      if ('+-*/^%()!'.indexOf(ch) >= 0) { tokens.push({ type: 'op', value: ch }); i++; continue; }
      throw new Error('bad symbol ' + ch);
    }
    return tokens;
  }

  /** Рекурсивный разбор (без eval): сложение и вычитание, умножение и деление,
   *  возведение в степень (правоассоциативно) и унарный минус. */
  function parseTokens(tokens) {
    var pos = 0;
    function peek() { return tokens[pos]; }
    function next() { return tokens[pos++]; }

    function parseExpression() {
      var node = parseTerm();
      while (peek() && peek().type === 'op' && (peek().value === '+' || peek().value === '-')) {
        var op = next().value;
        var right = parseTerm();
        node = { op: op, a: node, b: right };
      }
      return node;
    }
    function parseTerm() {
      var node = parseUnary();
      for (;;) {
        var tok = peek();
        if (tok && tok.type === 'op' && (tok.value === '*' || tok.value === '/' || tok.value === '%')) {
          var op = next().value;
          node = { op: op, a: node, b: parseUnary() };
          continue;
        }
        // неявное умножение: «6√2» → 6·√2, «2π» → 2·π, «3(4+1)»
        if (startsAtom(tok)) { node = { op: '*', a: node, b: parseUnary() }; continue; }
        return node;
      }
    }

    function startsAtom(tok) {
      if (!tok) return false;
      if (tok.type === 'num' || tok.type === 'name') return true;
      return tok.type === 'op' && tok.value === '(';
    }
    function parseUnary() {
      var tok = peek();
      if (tok && tok.type === 'op' && (tok.value === '-' || tok.value === '+')) {
        next();
        var operand = parseUnary();
        return tok.value === '-' ? { op: 'neg', a: operand } : operand;
      }
      return parsePower();
    }
    function parsePower() {
      var base = parseAtom();
      var tok = peek();
      if (tok && tok.type === 'op' && tok.value === '^') {
        next();
        return { op: '^', a: base, b: parseUnary() };
      }
      return base;
    }
    function parseAtom() {
      var tok = next();
      if (!tok) throw new Error('unexpected end');
      if (tok.type === 'num') return { num: tok.value };
      if (tok.type === 'name') {
        if (CONSTANTS[tok.value] !== undefined && !(peek() && peek().type === 'op' && peek().value === '(')) {
          return { num: CONSTANTS[tok.value] };
        }
        if (CONSTANTS[tok.value] !== undefined) {
          next();
          parseExpression();
          expect(')');
          return { num: CONSTANTS[tok.value] };
        }
        if (!FUNCTIONS[tok.value]) throw new Error('unknown name ' + tok.value);
        if (!(peek() && peek().type === 'op' && peek().value === '(')) {
          // функция без скобок: «√2» — это sqrt(2), «2π» и «6√2» — умножение
          return { fn: tok.value, a: parsePower() };
        }
        next();
        var arg = parseExpression();
        expect(')');
        return { fn: tok.value, a: arg };
      }
      if (tok.type === 'op' && tok.value === '(') {
        var inner = parseExpression();
        expect(')');
        return inner;
      }
      throw new Error('unexpected token');
    }
    function expect(value) {
      var tok = next();
      if (!tok || tok.value !== value) throw new Error('expected ' + value);
    }

    var tree = parseExpression();
    if (pos < tokens.length) throw new Error('trailing input');
    return tree;
  }

  function evalNode(node, x) {
    if (node.num !== undefined) return node.num;
    if (node.fn) return FUNCTIONS[node.fn](evalNode(node.a, x));
    switch (node.op) {
      case '+': return evalNode(node.a, x) + evalNode(node.b, x);
      case '-': return evalNode(node.a, x) - evalNode(node.b, x);
      case '*': return evalNode(node.a, x) * evalNode(node.b, x);
      case '/': return evalNode(node.a, x) / evalNode(node.b, x);
      case '%': return evalNode(node.a, x) % evalNode(node.b, x);
      case '^': return Math.pow(evalNode(node.a, x), evalNode(node.b, x));
      case 'neg': return -evalNode(node.a, x);
      default: throw new Error('bad node');
    }
  }

  /** Разобрать выражение один раз (для графиков). */
  M.parse = function (source) {
    var tree = parseTokens(tokenize(source));
    return {
      value: function (x) { return evalNode(tree, x); },
      source: String(source),
    };
  };

  /** Значение выражения; null при ошибке. */
  M.value = function (source) {
    try {
      var parsed = M.parse(source);
      var v = parsed.value(0);
      return isFinite(v) ? v : null;
    } catch (e) { return null; }
  };

  /** Число или строка «= 2.5» / «ошибка». */
  M.eval = function (source) {
    var v = M.value(source);
    if (v === null) return null;
    return U.round(v, 10);
  };

  /** Точки для графика y = f(x) на [xmin; xmax]. */
  M.sample = function (source, xmin, xmax, steps) {
    var parsed, points = [], i, x, y, step;
    try { parsed = M.parse(source); } catch (e) { return points; }
    xmin = typeof xmin === 'number' ? xmin : -10;
    xmax = typeof xmax === 'number' ? xmax : 10;
    steps = steps || 240;
    step = (xmax - xmin) / steps;
    for (i = 0; i <= steps; i++) {
      x = xmin + i * step;
      try { y = parsed.value(x); } catch (e) { y = NaN; }
      if (!isFinite(y)) { points.push(null); continue; }
      if (Math.abs(y) > 1e4) { points.push(null); continue; }
      points.push({ x: U.round(x, 6), y: U.round(y, 6) });
    }
    return points;
  };

  M.CONSTANTS = CONSTANTS;
  M.FUNCTIONS = FUNCTIONS;

  /* --------------------------------------------------------------------- *
   * 5. Загрузка контента / content
   * --------------------------------------------------------------------- */
  var C = CT.content = {
    bank: [], analogous: [], formulas: [], mistakes: { errors: {}, checklist: [] },
    topics: {}, order: [], counts: {}, byYear: {}, tools: {}, meta: {}, vectors: [],
    study: {}, lessons: {},
    loaded: false,

    load: function () {
      var self = this;
      return Promise.all([
        B.getContent('bank'), B.getContent('analogous'), B.getContent('topics'),
        B.getContent('formulas'), B.getContent('ui_strings'), B.getContent('mistakes'),
      ]).then(function (data) {
        var bank = data[0], analog = data[1], topics = data[2];
        self.bank = bank.tasks || [];
        self.analogous = analog.tasks || [];
        self.topics = topics.topics || {};
        self.order = topics.order || Object.keys(self.topics);
        self.tools = topics.tools || {};
        self.byYear = topics.byYear || {};
        self.study = topics.study || {};
        self.lessons = topics.lessons || {};
        self.formulas = (data[3] && data[3].groups) || [];
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
        return {
          year: Number(year), key: 'year-' + year, tasks: list,
          partA: list.filter(function (t) { return t.part === 'A'; }).length,
          partB: list.filter(function (t) { return t.part === 'B'; }).length,
        };
      }).reverse();
    },
    topicTitle: function (key) { return I.pick(this.topics[key]) || key; },
    toolTitle: function (key) { return I.pick(this.tools[key]) || key; },
    tasksByTopic: function (topic) { return this.bank.filter(function (t) { return t.topic === topic; }); },
    analogByTopic: function (topic) { return this.analogous.filter(function (t) { return t.topic === topic; }); },

    /** Конспект темы («что изучить»), который открывается при неверном ответе. */
    studyFor: function (topic) { return this.study[topic] || null; },
    lessonById: function (id) { return this.lessons[id] || null; },

    /** Detailed explanations for a formula section, in its authoring order. */
    lessonsForGroup: function (group) {
      var self = this, seen = {};
      return (group.lessons || []).map(function (id) {
        if (seen[id]) return null;
        seen[id] = true;
        return self.lessonById(id);
      }).filter(Boolean);
    },

    /** Разделы сборника формул, относящиеся к теме задания. */
    formulaGroupsFor: function (topic) {
      var entry = this.studyFor(topic);
      if (!entry || !entry.formulas) return [];
      var byId = {};
      this.formulas.forEach(function (group) { byId[group.id] = group; });
      return entry.formulas.map(function (id) { return byId[id]; }).filter(Boolean);
    },

    /** Диагноз типичной ошибки по тегам задания. */
    diagnoses: function (task) {
      var out = [], errors = this.mistakes.errors || {};
      (task && task.tags || []).forEach(function (tag) {
        if (errors[tag] && out.indexOf(errors[tag]) < 0) out.push(errors[tag]);
      });
      if (!out.length && errors.__default) out.push(errors.__default);
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

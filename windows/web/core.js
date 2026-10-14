/* core.js — shared engine of the CT maths tutor (Android WebView + Windows/HTML).
 *
 * It deliberately uses plain ES2019 with no modules and no CDN so it works from
 * file://, from the Android asset domain and from the Go server alike, fully
 * offline.  Everything the two platforms share lives here: the storage bridge,
 * the bilingual string catalogue, the portable answer checker (the same algorithm
 * is implemented in Python for authoring and in Kotlin/Go for native use) and
 * the statistics engine.
 */
(function (global) {
  'use strict';

  const CT = global.CT || {};
  global.CT = CT;

  /* ------------------------------------------------------------------ util */
  CT.util = {
    $(sel, root) { return (root || document).querySelector(sel); },
    $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); },
    escape(s) {
      return String(s === null || s === undefined ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    },
    fmtDuration(ms) {
      const total = Math.max(0, Math.round(ms / 1000));
      const h = Math.floor(total / 3600);
      const m = Math.floor((total % 3600) / 60);
      const s = total % 60;
      const pad = (v) => String(v).padStart(2, '0');
      return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}`;
    },
    fmtDate(iso) {
      const d = new Date(iso);
      if (isNaN(d.getTime())) return '';
      const pad = (v) => String(v).padStart(2, '0');
      return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    },
    today() { return new Date().toISOString().slice(0, 10); },
    debounce(fn, wait) {
      let handle = null;
      return function () {
        const args = arguments, self = this;
        clearTimeout(handle);
        handle = setTimeout(() => fn.apply(self, args), wait || 400);
      };
    },
    shuffle(arr, seed) {
      const a = arr.slice();
      let s = seed || 1;
      const rnd = () => { s = (s * 1103515245 + 12345) & 0x7fffffff; return s / 0x7fffffff; };
      for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(rnd() * (i + 1));
        const t = a[i]; a[i] = a[j]; a[j] = t;
      }
      return a;
    },
  };

  /* ------------------------------------------------------------- i18n ---- */
  CT.i18n = {
    lang: 'ru',
    strings: {},
    setStrings(catalogue) { this.strings = catalogue || {}; },
    setLang(lang) { this.lang = lang === 'en' ? 'en' : 'ru'; },
    /** t('task_counter_fmt', 1, 30) → "Задание 1 из 30" */
    t(key, ...args) {
      const entry = this.strings[key];
      let template;
      if (entry && typeof entry === 'object') template = entry[this.lang] || entry.en || entry.ru;
      if (!template) template = key;
      let i = 0;
      return template.replace(/%s/g, () => (i < args.length ? String(args[i++]) : '%s'));
    },
    /** Pick the localised branch of an object coming from the content bank. */
    pick(node) {
      if (node === null || node === undefined) return '';
      if (typeof node === 'string') return node;
      return node[this.lang] || node.ru || node.en || '';
    },
    pickList(node) {
      if (!node) return [];
      if (Array.isArray(node)) return node;
      return node[this.lang] || node.ru || node.en || [];
    },
  };

  /* ------------------------------------------------------- storage bridge */
  /* Two backends share one interface:
   *   Android : window.CTNative (Kotlin @JavascriptInterface)
   *   Windows : the local Go server under /api/...                                        */
  const native = () => global.CTNative || null;

  CT.bridge = {
    isAndroid() { return !!native(); },
    async getState() {
      if (native()) {
        try { return JSON.parse(native().getState() || '{}'); } catch (e) { return {}; }
      }
      try {
        const res = await fetch('api/state', { cache: 'no-store' });
        return await res.json();
      } catch (e) { return {}; }
    },
    async loadBlob(key) {
      if (native()) {
        try { const raw = native().loadBlob(key); return raw ? JSON.parse(raw) : null; }
        catch (e) { return null; }
      }
      try {
        const res = await fetch('api/blob?k=' + encodeURIComponent(key), { cache: 'no-store' });
        if (res.status === 204) return null;
        return await res.json();
      } catch (e) { return null; }
    },
    async saveBlob(key, value) {
      const payload = JSON.stringify(value);
      if (native()) { try { native().saveBlob(key, payload); } catch (e) { /* ignore */ } return; }
      try {
        await fetch('api/blob?k=' + encodeURIComponent(key), {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: payload,
        });
      } catch (e) { /* offline: the in-memory state still works */ }
    },
    async checkUpdates(baseUrl, currentVersion) {
      if (native()) {
        try { return JSON.parse(native().checkUpdates(baseUrl || '', currentVersion || '') || '{}'); }
        catch (e) { return { status: 'error', message: String(e) }; }
      }
      try {
        const res = await fetch('api/update', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ baseUrl: baseUrl || '', currentVersion: currentVersion || '' }),
        });
        return await res.json();
      } catch (e) { return { status: 'offline', message: String(e) }; }
    },
    async saveReport(name, html) {
      if (native()) {
        try { return JSON.parse(native().saveReport(name, html) || '{}'); }
        catch (e) { return { path: '' }; }
      }
      try {
        const res = await fetch('api/report', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, html }),
        });
        return await res.json();
      } catch (e) { return { path: '' }; }
    },
    /** Keep the screen awake while a test is in progress (Android only). */
    keepScreenOn(enabled) {
      if (native() && native().setKeepScreenOn) {
        try { native().setKeepScreenOn(!!enabled); } catch (e) { /* not supported */ }
      }
    },
    openExternal(url) {
      if (native()) { try { native().openExternal(url); return; } catch (e) { /* fall through */ } }
      global.open(url, '_blank', 'noopener');
    },
    /** A short user-visible notification (Android toast, otherwise in-page). */
    notify(message) {
      if (native()) { try { native().toast(message); return; } catch (e) { /* ignore */ } }
      const host = global.document && document.getElementById('toast');
      if (!host) return;
      host.textContent = message;
      host.classList.add('visible');
      clearTimeout(this._timer);
      this._timer = setTimeout(() => host.classList.remove('visible'), 3200);
    },
    async quit() {
      if (native()) { try { native().quit(); } catch (e) { /* ignore */ } return; }
      try { await fetch('api/quit', { method: 'POST' }); } catch (e) { /* ignore */ }
    },
    async openFolder(which) {
      if (native()) { return; }
      try { await fetch('api/open-folder?which=' + encodeURIComponent(which || 'data'), { method: 'POST' }); }
      catch (e) { /* ignore */ }
    },
  };

  /* ------------------------------------------------------------ content -- */
  CT.content = {
    bank: [], analogous: [], topics: {}, formulas: [], mistakes: {}, ui: {},
    meta: {},
    async loadFile(name) {
      if (native()) {
        try {
          const raw = native().getContent(name);
          if (raw) return JSON.parse(raw);
        } catch (e) { /* fall through to fetch */ }
      }
      const res = await fetch('content/' + name + '.json', { cache: 'no-store' });
      if (!res.ok) throw new Error('cannot load ' + name);
      return await res.json();
    },
    async load() {
      const bank = await this.loadFile('bank');
      this.bank = bank.tasks || [];
      this.meta = bank.meta || {};
      try { this.analogous = (await this.loadFile('analogous')).tasks || []; }
      catch (e) { this.analogous = []; }
      try { this.topics = await this.loadFile('topics'); } catch (e) { this.topics = {}; }
      try { this.formulas = (await this.loadFile('formulas')).groups || []; } catch (e) { this.formulas = []; }
      try { this.mistakes = await this.loadFile('mistakes'); } catch (e) { this.mistakes = {}; }
      let uiStrings = null;
      try { uiStrings = (await this.loadFile('ui_strings')).strings || {}; }
      catch (e) { uiStrings = null; }
      if (uiStrings) CT.i18n.setStrings(uiStrings);
      const version = await this.loadFile('version').catch(() => null);
      if (version) this.meta.version = version.contentVersion || this.meta.contentVersion;
      return this;
    },
    taskById(id) {
      for (const list of [this.bank, this.analogous]) {
        for (const t of list) if (t.id === id) return t;
      }
      return null;
    },
    years() {
      const set = [];
      this.bank.forEach((t) => { if (t.year && set.indexOf(t.year) < 0) set.push(t.year); });
      return set.sort((a, b) => b - a);
    },
    byYear(year) { return this.bank.filter((t) => t.year === year); },
    /** Analogous tasks for a failed item: same topic first, then shared tags. */
    analogousFor(task, limit) {
      if (!task) return [];
      const wanted = task.tags || [];
      const scored = this.analogous.map((t) => {
        let score = t.topic === task.topic ? 3 : 0;
        (t.tags || []).forEach((tag) => { if (wanted.indexOf(tag) >= 0) score += 2; });
        if (t.part === task.part) score += 0.5;
        return { t, score };
      }).filter((x) => x.score > 0)
        .sort((a, b) => b.score - a.score || a.t.id.localeCompare(b.t.id));
      return scored.slice(0, limit || 2).map((x) => x.t);
    },
    topicsByAccuracy(accuracy) {
      const list = Object.keys(accuracy || {});
      return list.sort((a, b) => accuracy[a].rate - accuracy[b].rate);
    },
    topicTitle(key) {
      const entry = (this.topics && this.topics.topics && this.topics.topics[key]) || null;
      return entry ? CT.i18n.pick(entry) : key;
    },
  };

  /* --------------------------------------------------- answer checking --- */
  /* Mirrors tools/... kit.normalize_answer/check_answer.  The build also emits
   * answer_vectors.json, and tests/answer_parity.js fails the CI run if the JS
   * implementation ever diverges from the Python reference.               */
  const MINUS_RE = /[−–—‒\u2212]/g;
  const SPACE_RE = /[\s\u00a0\u2009\u202f\t]/g;

  CT.answer = {
    normalize(value) {
      if (value === null || value === undefined) return '';
      let s = String(value).replace(MINUS_RE, '-').replace(SPACE_RE, '').toLowerCase();
      s = s.replace(/^(ответ|answer)[:=]/, '');
      s = s.replace(/^[a-zа-я]=/, '');
      if (s.endsWith('.')) s = s.slice(0, -1);
      s = s.replace(/\*/g, '·').replace(/pi/g, 'π');
      return s;
    },
    /** Parse an exact-or-decimal number, fractions included. */
    toNumber(value) {
      const s = this.normalize(value);
      if (!s) return null;
      if (s.indexOf('/') >= 0) {
        const parts = s.split('/');
        if (parts.length !== 2) return null;
        const a = this.toNumber(parts[0]), b = this.toNumber(parts[1]);
        if (a === null || b === null || b === 0) return null;
        return a / b;
      }
      if (!/^[-+]?(\d+([.,]\d*)?|[.,]\d+)$/.test(s)) return null;
      const n = parseFloat(s.replace(',', '.'));
      return isNaN(n) ? null : n;
    },
    accepted(task) {
      const list = (task && task.accept) ? task.accept.slice() : [];
      if (task && task.answer) {
        if (typeof task.answer === 'string') list.push(task.answer);
        else { list.push(task.answer.ru, task.answer.en); }
      }
      return list.filter(Boolean).map((v) => this.normalize(v)).filter(Boolean);
    },
    check(user, task) {
      const u = this.normalize(user);
      if (!u) return false;
      const accepted = this.accepted(task);
      if (accepted.indexOf(u) >= 0) return true;
      if (!task || task.answerType === 'choice') return false;
      const fu = this.toNumber(u);
      if (fu === null) return false;
      for (const variant of accepted) {
        const fv = this.toNumber(variant);
        if (fv === null) continue;
        if (Math.abs(fu - fv) < 1e-9) return true;
      }
      for (const variant of accepted) {
        const fv = this.toNumber(variant);
        if (fv === null) continue;
        if (Math.abs(fu - fv) < 5e-4) return true;  // hand-written decimals
      }
      return false;
    },
  };

  /* --------------------------------------------------------------- math -- */
  /* A tiny safe expression evaluator: no eval(), no Function() — the parser is
   * used by the calculator tool and by the function plotter.               */
  CT.math = {
    preprocess(src) {
      let s = String(src || '');
      s = s.replace(/[−–—]/g, '-').replace(/,/g, '.').replace(/π/g, 'pi');
      s = s.replace(/²/g, '^2').replace(/³/g, '^3');
      s = s.replace(/√/g, 'sqrt');
      s = s.replace(/\btg\b/g, 'tan').replace(/\bctg\b/g, 'cot');
      s = s.replace(/\blg\b/g, 'log10');
      s = s.replace(/\*/g, '*').replace(/·/g, '*').replace(/×/g, '*');
      s = s.replace(/÷/g, '/').replace(/:/g, '/');
      return s;
    },
    tokenize(src) {
      const s = this.preprocess(src);
      const tokens = [];
      let i = 0;
      const isDigit = (c) => c >= '0' && c <= '9';
      const isAlpha = (c) => /[a-zA-Z_]/.test(c);
      while (i < s.length) {
        const c = s[i];
        if (c === ' ') { i++; continue; }
        if (isDigit(c) || c === '.') {
          let j = i;
          while (j < s.length && (isDigit(s[j]) || s[j] === '.')) j++;
          tokens.push({ type: 'num', value: parseFloat(s.slice(i, j)) });
          i = j; continue;
        }
        if (isAlpha(c)) {
          let j = i;
          while (j < s.length && isAlpha(s[j])) j++;
          tokens.push({ type: 'name', value: s.slice(i, j) });
          i = j; continue;
        }
        if ('+-*/^()'.indexOf(c) >= 0) { tokens.push({ type: 'op', value: c }); i++; continue; }
        throw new Error('unexpected symbol: ' + c);
      }
      return this.withImplicitMultiplication(tokens);
    },
    /** 2x → 2*x, 3(x+1) → 3*(x+1), 2pi → 2*pi, xsin(x) is not supported. */
    withImplicitMultiplication(tokens) {
      const out = [];
      for (let i = 0; i < tokens.length; i++) {
        const prev = out[out.length - 1];
        const cur = tokens[i];
        const needMultiply = prev && (
          (prev.type === 'num' && (cur.type === 'name' || (cur.type === 'op' && cur.value === '('))) ||
          (prev.type === 'op' && prev.value === ')' && (cur.type === 'num' || cur.type === 'name' || (cur.type === 'op' && cur.value === '('))) ||
          (prev.type === 'name' && cur.type === 'num' && (cur.value % 1 === 0))
        );
        if (needMultiply) out.push({ type: 'op', value: '*' });
        out.push(cur);
      }
      return out;
    },
    parse(src) {
      const tokens = this.tokenize(src);
      let pos = 0;
      const peek = () => tokens[pos];
      const eat = (value) => {
        const t = tokens[pos];
        if (t && t.type === 'op' && t.value === value) { pos++; return true; }
        return false;
      };
      const FUNCS = {
        sin: Math.sin, cos: Math.cos, tan: Math.tan, sqrt: Math.sqrt,
        abs: Math.abs, exp: Math.exp, ln: Math.log, log10: Math.log10,
        cot: (x) => 1 / Math.tan(x), asin: Math.asin, acos: Math.acos, atan: Math.atan,
      };
      const CONSTANTS = { pi: Math.PI, e: Math.E };
      const variables = {};

      function parseExpression() { return parseAdditive(); }
      function parseAdditive() {
        let left = parseMultiplicative();
        for (;;) {
          if (eat('+')) left = { type: 'binary', op: '+', left, right: parseMultiplicative() };
          else if (eat('-')) left = { type: 'binary', op: '-', left, right: parseMultiplicative() };
          else return left;
        }
      }
      function parseMultiplicative() {
        let left = parseUnary();
        for (;;) {
          if (eat('*')) left = { type: 'binary', op: '*', left, right: parseUnary() };
          else if (eat('/')) left = { type: 'binary', op: '/', left, right: parseUnary() };
          else return left;
        }
      }
      function parseUnary() {
        if (eat('-')) return { type: 'unary', op: '-', operand: parseUnary() };
        if (eat('+')) return parseUnary();
        return parsePower();
      }
      function parsePower() {
        const base = parsePrimary();
        if (eat('^')) return { type: 'binary', op: '^', left: base, right: parseUnary() };
        return base;
      }
      function parsePrimary() {
        const t = peek();
        if (!t) throw new Error('unexpected end of expression');
        if (t.type === 'num') { pos++; return { type: 'number', value: t.value }; }
        if (t.type === 'name') {
          pos++;
          const name = t.value;
          if (FUNCS[name]) {
            eat('(');
            const arg = parseExpression();
            eat(')');
            return { type: 'call', fn: name, arg };
          }
          if (name === 'x') return { type: 'variable', name: 'x' };
          if (name in CONSTANTS) return { type: 'number', value: CONSTANTS[name] };
          // e.g. "2x" already handled; unknown identifiers count as free variables
          return { type: 'variable', name };
        }
        if (t.type === 'op' && t.value === '(') {
          pos++;
          const inner = parseExpression();
          eat(')');
          return inner;
        }
        throw new Error('unexpected token ' + JSON.stringify(t.value));
      }

      const ast = parseExpression();
      if (pos < tokens.length) throw new Error('unexpected trailing tokens');
      const evaluate = (node, env) => {
        switch (node.type) {
          case 'number': return node.value;
          case 'variable': {
            const v = env && node.name in env ? env[node.name]
              : (node.name in CONSTANTS ? CONSTANTS[node.name] : undefined);
            if (v === undefined) throw new Error('unknown variable ' + node.name);
            return v;
          }
          case 'unary': return -evaluate(node.operand, env);
          case 'call': return FUNCS[node.fn](evaluate(node.arg, env));
          case 'binary': {
            const a = evaluate(node.left, env), b = evaluate(node.right, env);
            switch (node.op) {
              case '+': return a + b;
              case '-': return a - b;
              case '*': return a * b;
              case '/': return a / b;
              case '^': return Math.pow(a, b);
              default: throw new Error('bad operator');
            }
          }
          default: throw new Error('bad node');
        }
      };
      return {
        source: src,
        variables,
        evaluate(env) { return evaluate(ast, env || {}); },
      };
    },
    evaluate(src, env) { return this.parse(src).evaluate(env || {}); },
    /** Sample a function of x on [from, to] for the plotter. */
    sample(src, from, to, steps) {
      const fn = this.parse(src);
      const points = [];
      const n = steps || 240;
      for (let i = 0; i <= n; i++) {
        const x = from + ((to - from) * i) / n;
        let y = null;
        try { y = fn.evaluate({ x }); } catch (e) { y = null; }
        if (y !== null && isFinite(y) && Math.abs(y) < 1e6) points.push({ x, y });
        else points.push({ x, y: null });
      }
      return points;
    },
  };

  /* ----------------------------------------------------------- analytics  */
  CT.analytics = {
    emptyProgress() {
      return {
        version: 1,
        attempts: [],          // finished tests
        topicStats: {},        // topic → {seen, correct}
        daily: {},             // date → tasks solved
        streak: { last: '', current: 0, best: 0 },
        goal: 20,
      };
    },
    /** Record one finished test (or practice batch). */
    recordAttempt(progress, attempt) {
      progress.attempts.push(attempt);
      if (progress.attempts.length > 300) progress.attempts = progress.attempts.slice(-300);
      attempt.results.forEach((r) => {
        const bucket = progress.topicStats[r.topic] || (progress.topicStats[r.topic] = { seen: 0, correct: 0 });
        bucket.seen += 1;
        if (r.correct) bucket.correct += 1;
      });
      progress.daily[attempt.date] = (progress.daily[attempt.date] || 0) + attempt.results.length;
      this.touchStreak(progress, attempt.date);
      return progress;
    },
    touchStreak(progress, day) {
      const s = progress.streak;
      if (s.last === day) return s;
      const prev = new Date(day);
      prev.setDate(prev.getDate() - 1);
      const yesterday = prev.toISOString().slice(0, 10);
      s.current = s.last === yesterday ? s.current + 1 : 1;
      s.last = day;
      s.best = Math.max(s.best || 0, s.current);
      return s;
    },
    totals(progress) {
      let solved = 0, correct = 0, timeMs = 0;
      progress.attempts.forEach((a) => {
        solved += a.results.length;
        correct += a.results.filter((r) => r.correct).length;
        timeMs += a.timeMs || 0;
      });
      return {
        tests: progress.attempts.length,
        solved,
        correct,
        rate: solved ? correct / solved : 0,
        timeMs,
        avgTaskMs: solved ? timeMs / solved : 0,
      };
    },
    topicAccuracy(progress) {
      const map = {};
      Object.keys(progress.topicStats || {}).forEach((topic) => {
        const s = progress.topicStats[topic];
        map[topic] = { seen: s.seen, correct: s.correct, rate: s.seen ? s.correct / s.seen : 0 };
      });
      return map;
    },
    weakTopics(progress, limit) {
      const map = this.topicAccuracy(progress);
      return Object.keys(map).map((k) => ({ topic: k, ...map[k] }))
        .filter((x) => x.seen >= 3 && x.rate < 0.7)
        .sort((a, b) => a.rate - b.rate || b.seen - a.seen)
        .slice(0, limit || 5);
    },
    strongTopics(progress, limit) {
      const map = this.topicAccuracy(progress);
      return Object.keys(map).map((k) => ({ topic: k, ...map[k] }))
        .filter((x) => x.seen >= 3 && x.rate >= 0.85)
        .sort((a, b) => b.rate - a.rate || b.seen - a.seen)
        .slice(0, limit || 5);
    },
    yearAccuracy(progress) {
      const map = {};
      progress.attempts.forEach((a) => {
        a.results.forEach((r) => {
          const key = r.year ? String(r.year) : 'gen';
          const b = map[key] || (map[key] = { seen: 0, correct: 0, rate: 0 });
          b.seen += 1; if (r.correct) b.correct += 1;
        });
      });
      Object.keys(map).forEach((k) => { map[k].rate = map[k].seen ? map[k].correct / map[k].seen : 0; });
      return map;
    },
    lastAttempts(progress, n) {
      return progress.attempts.slice(-(n || 8)).reverse();
    },
    /** Личный лучший результат по тесту. */
    bestForTest(progress, testId) {
      let best = null;
      progress.attempts.forEach((a) => {
        if (a.testId !== testId) return;
        const rate = a.results.length ? a.results.filter((r) => r.correct).length / a.results.length : 0;
        if (!best || rate > best.rate) best = { rate, date: a.date };
      });
      return best;
    },
  };

  /* ------------------------------------------------------------ storage   */
  CT.store = {
    progress: CT.analytics.emptyProgress(),
    settings: {
      lang: 'ru',
      theme: 'system',
      fontSize: 'normal',
      examMinutes: 180,
      autoAdvance: false,
      sound: true,
      vibration: true,
      keepScreenOn: true,
      autoUpdate: true,
      showEnglishSolutions: false,
      baseUrl: 'https://github.com/zigorminsk-debug/mathematics/releases/latest/download',
      contentVersionSeen: '',
    },
    session: null,
    app: {},
    async init() {
      const state = await CT.bridge.getState();
      this.app = (state && state.app) || {};
      this.content = (state && state.content) || {};
      const settings = await CT.bridge.loadBlob('settings');
      if (settings && typeof settings === 'object') Object.assign(this.settings, settings);
      const progress = await CT.bridge.loadBlob('progress');
      if (progress && typeof progress === 'object') {
        this.progress = Object.assign(CT.analytics.emptyProgress(), progress);
      }
      const session = await CT.bridge.loadBlob('session');
      if (session && typeof session === 'object') this.session = session;
      CT.i18n.setLang(this.settings.lang);
      return this;
    },
    saveSettings: null,   // assigned below (debounced)
    saveProgress: null,
    saveSession: null,
    flush() {
      CT.bridge.saveBlob('settings', this.settings);
      CT.bridge.saveBlob('progress', this.progress);
      CT.bridge.saveBlob('session', this.session || null);
    },
  };
  CT.store.saveSettings = CT.util.debounce(function () { CT.store.flush(); }, 300);
  CT.store.saveProgress = CT.util.debounce(function () { CT.store.flush(); }, 300);
  CT.store.saveSession = CT.util.debounce(function () { CT.store.flush(); }, 200);

  /* --------------------------------------------------------------- charts */
  CT.charts = {
    /** Simple accessible bar chart on a canvas (no dependencies). */
    bars(canvas, rows, options) {
      if (!canvas || !canvas.getContext) return;
      const opts = options || {};
      const dpr = global.devicePixelRatio || 1;
      const width = canvas.clientWidth || 320;
      const rowHeight = opts.rowHeight || 26;
      const height = rows.length * rowHeight + 8;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      const ctx = canvas.getContext('2d');
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, width, height);
      const styles = global.getComputedStyle ? getComputedStyle(document.body) : null;
      const text = (styles && styles.getPropertyValue('--text')) || '#222';
      const accent = opts.color || (styles && styles.getPropertyValue('--accent')) || '#2d7ff9';
      ctx.font = '12px system-ui, sans-serif';
      ctx.textBaseline = 'middle';
      rows.forEach((row, i) => {
        const y = i * rowHeight + rowHeight / 2;
        const labelWidth = Math.max(70, opts.labelWidth || 90);
        ctx.fillStyle = text;
        const label = String(row.label).slice(0, 14);
        ctx.fillText(label, 0, y);
        const barWidth = width - labelWidth - 48;
        const value = Math.max(0, Math.min(1, row.value || 0));
        ctx.fillStyle = 'rgba(127,127,127,0.18)';
        ctx.fillRect(labelWidth, y - 6, barWidth, 12);
        ctx.fillStyle = row.color || accent;
        ctx.fillRect(labelWidth, y - 6, Math.max(2, barWidth * value), 12);
        ctx.fillStyle = text;
        ctx.fillText(Math.round(value * 100) + '%', labelWidth + barWidth + 6, y);
      });
    },
    /** Function plotter: draws y = f(x) with adaptive axes. */
    plot(canvas, source, from, to) {
      const ctx = canvas.getContext('2d');
      const dpr = global.devicePixelRatio || 1;
      const width = canvas.clientWidth || 320;
      const height = canvas.clientHeight || 220;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const styles = getComputedStyle(document.body);
      const text = styles.getPropertyValue('--text') || '#222';
      const muted = styles.getPropertyValue('--muted') || '#888';
      const accent = styles.getPropertyValue('--accent') || '#2d7ff9';
      ctx.clearRect(0, 0, width, height);

      const points = CT.math.sample(source, from, to, 400);
      const ys = points.map((p) => p.y).filter((y) => y !== null);
      if (!ys.length) return false;
      let yMin = Math.min.apply(null, ys), yMax = Math.max.apply(null, ys);
      if (yMax - yMin < 1e-6) { yMax += 1; yMin -= 1; }
      const pad = (yMax - yMin) * 0.1;
      yMin -= pad; yMax += pad;
      const sx = (x) => ((x - from) / (to - from)) * (width - 24) + 12;
      const sy = (y) => height - 12 - ((y - yMin) / (yMax - yMin)) * (height - 24);

      // axes
      ctx.strokeStyle = muted;
      ctx.lineWidth = 1;
      ctx.beginPath();
      if (yMin <= 0 && yMax >= 0) { ctx.moveTo(0, sy(0)); ctx.lineTo(width, sy(0)); }
      if (from <= 0 && to >= 0) { ctx.moveTo(sx(0), 0); ctx.lineTo(sx(0), height); }
      ctx.stroke();
      ctx.fillStyle = muted;
      ctx.font = '11px system-ui, sans-serif';
      ctx.fillText('y=' + yMax.toFixed(2), 4, 10);
      ctx.fillText('y=' + yMin.toFixed(2), 4, height - 2);

      // curve
      ctx.strokeStyle = accent;
      ctx.lineWidth = 2;
      ctx.beginPath();
      let started = false;
      points.forEach((p) => {
        if (p.y === null) { started = false; return; }
        const px = sx(p.x), py = sy(p.y);
        if (!started) { ctx.moveTo(px, py); started = true; } else { ctx.lineTo(px, py); }
      });
      ctx.stroke();
      ctx.fillStyle = text;
      ctx.fillText('x ∈ [' + from + '; ' + to + ']', width - 90, height - 6);
      return true;
    },
  };

  CT.version = '1.0.0';
})(typeof window !== 'undefined' ? window : globalThis);

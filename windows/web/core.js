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
   * 3. Проверка ответов / physics answer checker
   *
   * Тот же контракт, что в content_src/quantities.py::check_answer и в
   * android/app/src/main/java/by/ziv/ctphysics/AnswerChecker.kt. Спецификация
   * задания (spec) приходит из банка: answerType, answerValue, unit,
   * unitPolicy, dimension, tolerance | rounding.
   *
   * Проверяется ФИЗИЧЕСКАЯ ВЕЛИЧИНА: число + единица + размерность.
   * «10 Н» не принимается вместо «10 кг», «10 см» — вместо «10 м»,
   * «36 км/ч» принимается как «10 м/с». Никакого eval: единицы разбираются
   * собственным парсером по белому списку (таблица сгенерирована из Python).
   * --------------------------------------------------------------------- */
  var A = CT.answer = {};

  /* Белый список единиц: symbol/ru/en, вектор размерности (m,kg,s,A,K,mol,cd),
     множитель к СИ, смещение (°C), приставки и синонимы. */

  /* >>> units:generated */
  A.UNITS = [{"a":["A","А","ампер","ампера","амперов"],"dim":[0,0,0,1,0,0,0],"en":"A","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"А","s":"A"},{"a":["C","Кл","кулон","кулона","кулонов"],"dim":[0,0,1,1,0,0,0],"en":"C","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"Кл","s":"C"},{"a":["F","Ф","фарад","фарада","фарадов"],"dim":[-2,-1,4,2,0,0,0],"en":"F","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"Ф","s":"F"},{"a":["H","Гн","генри"],"dim":[2,1,-2,-2,0,0,0],"en":"H","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"Гн","s":"H"},{"a":["Hz","Гц","герц","герца"],"dim":[0,0,-1,0,0,0,0],"en":"Hz","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"Гц","s":"Hz"},{"a":["J","Дж","джоулей","джоуль","джоуля"],"dim":[2,1,-2,0,0,0,0],"en":"J","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"Дж","s":"J"},{"a":["K","К","кельвин","кельвина","кельвинов"],"dim":[0,0,0,0,1,0,0],"en":"K","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"К","s":"K"},{"a":["N","Н","ньютон","ньютона","ньютонов"],"dim":[1,1,-2,0,0,0,0],"en":"N","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"Н","s":"N"},{"a":["Ohm","Ω","Ом","ом","ома","омов"],"dim":[2,1,-3,-2,0,0,0],"en":"Ω","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"Ом","s":"Ohm"},{"a":["Pa","Па","паскалей","паскаль","паскаля"],"dim":[-1,1,-2,0,0,0,0],"en":"Pa","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"Па","s":"Pa"},{"a":["T","Тл","тесла","теслы"],"dim":[0,1,-2,-1,0,0,0],"en":"T","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"Тл","s":"T"},{"a":["V","В","вольт","вольта","вольтов"],"dim":[2,1,-3,-1,0,0,0],"en":"V","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"В","s":"V"},{"a":["W","Вт","ватт","ватта"],"dim":[2,1,-3,0,0,0,0],"en":"W","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"Вт","s":"W"},{"a":["Wb","Вб","вебер","вебера","веберов"],"dim":[2,1,-2,-1,0,0,0],"en":"Wb","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"Вб","s":"Wb"},{"a":["cd","кандела","кд"],"dim":[0,0,0,0,0,0,1],"en":"cd","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"кд","s":"cd"},{"a":["day","сут","сутки","суток"],"dim":[0,0,1,0,0,0,0],"en":"сут","f":"86400","fexact":"86400/1","o":0.0,"p":false,"ru":"сут","s":"day"},{"a":["degC","°C","градусцельсия","цельсия","⁰C"],"dim":[0,0,0,0,1,0,0],"en":"°C","f":"1","fexact":"1/1","o":273.15,"p":false,"ru":"°C","s":"degC"},{"a":["dpt","диоптрии","диоптрия","дптр"],"dim":[-1,0,0,0,0,0,0],"en":"dpt","f":"1","fexact":"1/1","o":0.0,"p":false,"ru":"дптр","s":"dpt"},{"a":["eV","эВ","эв"],"dim":[2,1,-2,0,0,0,0],"en":"eV","f":"1.6e-19","fexact":"1/6250000000000000000","o":0.0,"p":false,"ru":"эВ","s":"eV"},{"a":["g","г","грамм","грамма","граммов"],"dim":[0,1,0,0,0,0,0],"en":"g","f":"0.001","fexact":"1/1000","o":0.0,"p":true,"ru":"г","s":"g"},{"a":["g/cm^3","g/cm³","г/см³"],"dim":[-3,1,0,0,0,0,0],"en":"g/cm³","f":"1000","fexact":"1000/1","o":0.0,"p":false,"ru":"г/см³","s":"g/cm^3"},{"a":["h","ч","час","часа","часов"],"dim":[0,0,1,0,0,0,0],"en":"h","f":"3600","fexact":"3600/1","o":0.0,"p":false,"ru":"ч","s":"h"},{"a":["kWh","кВт·ч","кВтч"],"dim":[2,1,-2,0,0,0,0],"en":"kWh","f":"3600000","fexact":"3600000/1","o":0.0,"p":false,"ru":"кВт·ч","s":"kWh"},{"a":["kg","кг","килограмм","килограмма","килограммов"],"dim":[0,1,0,0,0,0,0],"en":"kg","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"кг","s":"kg"},{"a":["km/h","км/ч"],"dim":[1,0,-1,0,0,0,0],"en":"km/h","f":"0.2777777777777778","fexact":"5/18","o":0.0,"p":false,"ru":"км/ч","s":"km/h"},{"a":["L","l","л","литр","литра","литров"],"dim":[3,0,0,0,0,0,0],"en":"l","f":"0.001","fexact":"1/1000","o":0.0,"p":true,"ru":"л","s":"l"},{"a":["m","м","метр","метра","метров"],"dim":[1,0,0,0,0,0,0],"en":"m","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"м","s":"m"},{"a":["m/s^2","m/s²","м/с²"],"dim":[1,0,-2,0,0,0,0],"en":"m/s²","f":"1","fexact":"1/1","o":0.0,"p":false,"ru":"м/с²","s":"m/s^2"},{"a":["min","мин","минут","минута","минуты"],"dim":[0,0,1,0,0,0,0],"en":"min","f":"60","fexact":"60/1","o":0.0,"p":false,"ru":"мин","s":"min"},{"a":["mm Hg","mmHg","мм рт. ст.","ммрт.ст."],"dim":[-1,1,-2,0,0,0,0],"en":"mm Hg","f":"133.32236842105263","fexact":"20265/152","o":0.0,"p":false,"ru":"мм рт. ст.","s":"mmHg"},{"a":["mol","молей","моль","моля"],"dim":[0,0,0,0,0,1,0],"en":"mol","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"моль","s":"mol"},{"a":["s","с","сек","секунд","секунда","секунды"],"dim":[0,0,1,0,0,0,0],"en":"s","f":"1","fexact":"1/1","o":0.0,"p":true,"ru":"с","s":"s"},{"a":["t","т","тонн","тонна","тонны"],"dim":[0,1,0,0,0,0,0],"en":"t","f":"1000","fexact":"1000/1","o":0.0,"p":false,"ru":"т","s":"t"},{"a":["u","а.е.м.","аем"],"dim":[0,1,0,0,0,0,0],"en":"u","f":"1.66e-27","fexact":"83/50000000000000000000000000000","o":0.0,"p":false,"ru":"а.е.м.","s":"u"}];
  A.PREFIXES = [{"f":"1e-12","la":"p","ru":"п"},{"f":"1e-09","la":"n","ru":"н"},{"f":"1e-06","la":"µ","ru":"мк"},{"f":"1e-06","la":"u","ru":"мк"},{"f":"0.001","la":"m","ru":"м"},{"f":"0.01","la":"c","ru":"с"},{"f":"0.1","la":"d","ru":"д"},{"f":"1000","la":"k","ru":"к"},{"f":"1000000","la":"M","ru":"М"},{"f":"1000000000","la":"G","ru":"Г"}];
/* <<< units:generated */
  A.DIM_AXES = ['m', 'kg', 's', 'A', 'K', 'mol', 'cd'];
  A.ZERO_DIM = [0, 0, 0, 0, 0, 0, 0];

  var SUPER = {'\u2070': '0', '\u00b9': '1', '\u00b2': '2', '\u00b3': '3', '\u2074': '4',
    '\u2075': '5', '\u2076': '6', '\u2077': '7', '\u2078': '8', '\u2079': '9', '\u207b': '-'};

  /** Ключ синонима: без регистра, пробелов, «^» и «·» (как в Python). */
  function aliasKey(name) {
    return String(name).trim().toLowerCase().replace(/[ ]/g, '').replace(/\^/g, '')
      .replace(/[\u00b7*]/g, '');
  }
  A.aliasKey = aliasKey;

  var UNITS_BY_NAME = {};
  var UNITS_BY_ALIAS = {};
  A.UNITS.forEach(function (unit) {
    [unit.s, unit.ru, unit.en].concat(unit.a || []).forEach(function (name) {
      var stripped = String(name).trim();
      if (stripped && UNITS_BY_NAME[stripped] === undefined) UNITS_BY_NAME[stripped] = unit;
      if (stripped && !(stripped.length === 1 && /[a-z]/i.test(stripped))) {
        var key = aliasKey(stripped);
        if (key && UNITS_BY_ALIAS[key] === undefined) UNITS_BY_ALIAS[key] = unit;
      }
    });
  });

  /** Надстрочные степени и знаки → обычная запись: «м²» → «м^2», «·» → «*». */
  A.toExpression = function (text) {
    var out = String(text === null || text === undefined ? '' : text);
    out = out.replace(/[\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079\u207b]+/g,
      function (match) {
        var digits = '';
        for (var i = 0; i < match.length; i++) digits += SUPER[match[i]];
        return '^(' + digits + ')';
      });
    out = out.replace(/[\u00b7\u2219\u00d7\u22c5]/g, '*');
    return out.replace(/\s+/g, '');
  };

  /* --- справочник единиц для интерфейса -------------------------------- */

  /** Как единица относится к СИ: «1», «5/18», «10³», «1/1000». */
  A.unitFactorText = function (unit) {
    if (!unit) return '';
    var exact = String(unit.fexact || '');
    var factor = Number(unit.f === undefined ? 1 : unit.f);
    if (factor === 1) return '1';
    if (/^-?\d+\/\d+$/.test(exact)) {
      var parts = exact.split('/');
      if (Math.abs(Number(parts[0])) <= 1e6 && Math.abs(Number(parts[1])) <= 1e6) {
        return Number(parts[0]) + '/' + Number(parts[1]);
      }
    }
    var absolute = Math.abs(factor);
    if (absolute >= 1e4 || absolute < 1e-3) {
      var exponent = Math.floor(Math.log(absolute) / Math.LN10);
      var mantissa = factor / Math.pow(10, exponent);
      var digits = Math.abs(mantissa - Math.round(mantissa)) < 1e-9
        ? String(Math.round(mantissa)) : mantissa.toFixed(3).replace(/0+$/, '').replace(/\.$/, '');
      return digits + '\u00b710' + A.superscript(exponent);
    }
    return String(factor).replace('.', ',');
  };

  /** Число надстрочными цифрами: 3 → «³», -2 → «⁻²». */
  A.superscript = function (value) {
    var digits = { '-': '\u207b', '0': '\u2070', '1': '\u00b9', '2': '\u00b2', '3': '\u00b3',
      '4': '\u2074', '5': '\u2075', '6': '\u2076', '7': '\u2077', '8': '\u2078', '9': '\u2079' };
    return String(value).split('').map(function (character) {
      return digits[character] === undefined ? character : digits[character];
    }).join('');
  };

  /** Размерность словами: [1,0,-2,…] → «м/с²» (язык — язык подписи). */
  A.dimsText = function (dim, lang) {
    var names = (lang === 'en')
      ? ['m', 'kg', 's', 'A', 'K', 'mol', 'cd']
      : ['\u043c', '\u043a\u0433', '\u0441', '\u0410', '\u041a', '\u043c\u043e\u043b\u044c', '\u043a\u0434'];
    var top = [], bottom = [];
    (dim || []).forEach(function (power, index) {
      if (!power) return;
      var name = names[index] || ('?' + index);
      var target = power > 0 ? top : bottom;
      target.push(name + (Math.abs(power) === 1 ? '' : A.superscript(Math.abs(power))));
    });
    if (!top.length && !bottom.length) return '';
    var head = top.length ? top.join('\u00b7') : '1';
    return bottom.length ? head + '/' + bottom.join('\u00b7') : head;
  };

  /* --- число в школьной записи ----------------------------------------- */

  /** «12», «12,5», «-3,5», «1/2», «1e-3», «1,5·10⁻³», «3·10⁵» → Number | null. */
  A.number = function (text) {
    if (text === null || text === undefined) return null;
    var s = String(text).trim();
    if (!s) return null;
    s = s.replace(/\u00a0/g, '').replace(/ /g, '');
    s = s.replace(/[\u2212\u2013\u2014\u2015]/g, '-');
    s = s.replace(/10([\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079\u207b]+)/g,
      function (match, digits) {
        var out = '';
        for (var i = 0; i < digits.length; i++) out += SUPER[digits[i]];
        return '10^(' + out + ')';
      });
    s = s.replace(/[\u22c5\u2219\u00d7\u00b7]/g, '*');
    var scientific = s.match(/^([+-]?\d+(?:[.,]\d+)?)(?:\*10(?:\^|\*\*)?\(?([+-]?\d+)\)?|[eE]([+-]?\d+))$/);
    if (scientific) {
      var mantissa = Number(scientific[1].replace(',', '.'));
      var exponent = Number(scientific[2] || scientific[3] || '0');
      if (!isFinite(mantissa) || !isFinite(exponent)) return null;
      return mantissa * Math.pow(10, exponent);
    }
    var power = s.match(/^10\^(?:\(([+-]?\d+)\)|([+-]?\d+))$/);
    if (power) return Math.pow(10, Number(power[1] || power[2]));
    var fraction = s.match(/^([+-]?\d+(?:[.,]\d+)?)\/([+-]?\d+(?:[.,]\d+)?)$/);
    if (fraction) {
      // обыкновенная дробь: «1/2» = 0,5; деление на ноль — не число
      var numerator = Number(fraction[1].replace(',', '.'));
      var denominator = Number(fraction[2].replace(',', '.'));
      if (!isFinite(numerator) || !isFinite(denominator) || denominator === 0) return null;
      return numerator / denominator;
    }
    var plain = s.replace(',', '.');
    if (!/^[-+]?\d+(?:\.\d+)?$/.test(plain)) return null;
    return Number(plain);
  };

  /* --- единицы измерения ----------------------------------------------- */

  /** Единица по точному обозначению или синониму (без приставок). */
  A.baseLookup = function (name) {
    var stripped = String(name).trim();
    if (UNITS_BY_NAME[stripped]) return UNITS_BY_NAME[stripped];
    return UNITS_BY_ALIAS[A.aliasKey(stripped)] || null;
  };

  /** Как в Python: сначала целое обозначение («Гн» — генри, а не гиганьютон),
      и только потом разбор «приставка + единица». */
  A.lookupUnit = function (name) {
    var exact = A.baseLookup(name);
    if (exact) return exact;
    return A.prefixedUnit(name);
  };

  /** Множитель и смещение единицы из таблицы («f»/«o») или уже вычисленные. */
  function unitFactor(unit) {
    if (unit.factor !== undefined && unit.factor !== null) return Number(unit.factor);
    return Number(unit.f === undefined ? 1 : unit.f);
  }
  function unitOffset(unit) {
    if (unit.offset !== undefined && unit.offset !== null) return Number(unit.offset);
    return Number(unit.o === undefined ? 0 : unit.o);
  }

  A.prefixedUnit = function (name) {
    var text = String(name).trim();
    var candidates = [];
    A.PREFIXES.forEach(function (prefix) {
      [prefix.ru, prefix.la].forEach(function (form) {
        if (text.length > form.length && text.indexOf(form) === 0) {
          candidates.push([form.length, prefix, text.slice(form.length)]);
        }
      });
    });
    candidates.sort(function (a, b) { return b[0] - a[0]; });
    for (var i = 0; i < candidates.length; i++) {
      var prefix = candidates[i][1];
      var base = A.baseLookup(candidates[i][2]);
      if (!base || !base.p || base.o) continue;          // °C не приставляется
      if (base.s === 'kg') continue;                     // масса: «мкг» — не микрокилограмм
      return { s: prefix.la + base.s, ru: prefix.ru + base.ru, en: prefix.la + base.en,
               dim: base.dim, factor: Number(prefix.f) * unitFactor(base), offset: 0,
               prefixed: true };
    }
    return null;
  };

  A.unitOf = function (text) {
    var raw = String(text === null || text === undefined ? '' : text).trim();
    if (!raw) return null;
    var expression = A.toExpression(raw);
    if (!expression) return null;
    if (expression === '1') {
      return { s: '1', ru: '', en: '', dim: A.ZERO_DIM.slice(), factor: 1, offset: 0 };
    }
    // токенизатор единиц повторяет Python `_tokenize`: буквы (включая греческие
    // Ω/µ), цифры, «.», «_», «°», операторы «* / ^ ( )» и знак «-»
    var tokens = [];
    var isUnitChar = function (ch) {
      return /[0-9A-Za-z\u0400-\u04ff._\u00b0\u03a9\u00b5\u03bc]/.test(ch);
    };
    var tokenizerFailed = false;
    (function () {
      var index = 0;
      while (index < expression.length && !tokenizerFailed) {
        var ch = expression[index];
        if ('*/^()'.indexOf(ch) >= 0) { tokens.push(ch); index += 1; continue; }
        if (/[0-9.]/.test(ch)) {
          var end = index;
          while (end < expression.length && /[0-9.]/.test(expression[end])) end += 1;
          tokens.push(expression.slice(index, end));
          index = end;
          continue;
        }
        if (ch === '-') { tokens.push(ch); index += 1; continue; }
        var stop = index;
        while (stop < expression.length && isUnitChar(expression[stop])) stop += 1;
        if (stop === index) { tokenizerFailed = true; break; }
        tokens.push(expression.slice(index, stop));
        index = stop;
      }
    })();
    if (tokenizerFailed || !tokens.length) return null;
    var position = 0;
    var peek = function () { return tokens[position]; };
    var next = function () { var token = tokens[position]; position += 1; return token; };

    var parseExpression = function () {
      var node = parseTerm();
      while (peek() === '*' || peek() === '/') {
        var operator = next();
        var right = parseTerm();
        node = operator === '*' ? mulDim(node, right) : divDim(node, right);
      }
      return node;
    };
    var parseTerm = function () {
      var node = parseAtom();
      if (peek() === '^') {
        next();
        var wrapped = false;
        if (peek() === '(') { next(); wrapped = true; }
        var sign = 1;
        if (peek() === '-') { next(); sign = -1; }
        else if (peek() === '+') { next(); }
        var exponent = next();
        if (!/^\d+$/.test(String(exponent))) throw new Error('exponent');
        if (wrapped && next() !== ')') throw new Error('exponent paren');
        node = powDim(node, sign * Number(exponent));
      }
      return node;
    };
    var parseAtom = function () {
      var token = next();
      if (token === undefined) throw new Error('end');
      if (token === '(') {
        var inner = parseExpression();
        if (next() !== ')') throw new Error('paren');
        return inner;
      }
      if (token === '1') return { dim: A.ZERO_DIM.slice(), factor: 1, offset: 0 };
      if (/^\d+$/.test(token)) throw new Error('numeric factor');
      if (token === '-') { var negated = parseAtom(); negated.factor = -negated.factor; return negated; }
      var unit = A.lookupUnit(token);
      if (!unit) throw new Error('unknown unit');
      return { dim: unit.dim.slice(), factor: unitFactor(unit), offset: unitOffset(unit),
               unit: unit };
    };
    var mulDim = function (a, b) {
      return { dim: a.dim.map(function (x, i) { return x + b.dim[i]; }),
               factor: a.factor * b.factor, offset: 0 };
    };
    var divDim = function (a, b) {
      return { dim: a.dim.map(function (x, i) { return x - b.dim[i]; }),
               factor: a.factor / b.factor, offset: 0 };
    };
    var powDim = function (node, exponent) {
      return { dim: node.dim.map(function (x) { return x * exponent; }),
               factor: Math.pow(node.factor, exponent), offset: 0 };
    };

    var parsed;
    try {
      parsed = parseExpression();
      if (position !== tokens.length) return null;
    } catch (error) {
      return null;
    }
    if (tokens.length === 1) {
      var single = A.lookupUnit(tokens[0]);
      if (single) {
        // сохраняем подпись и смещение °C: «°C» — единственная единица со сдвигом
        return { s: single.s, ru: single.ru, en: single.en, dim: single.dim.slice(),
                 factor: unitFactor(single), offset: unitOffset(single),
                 prefixed: !!single.prefixed };
      }
    }
    var label = raw;
    return { s: label, ru: label, en: label, dim: parsed.dim, factor: parsed.factor,
             offset: parsed.offset || 0 };
  };

  /* --- проверка ответа -------------------------------------------------- */

  A.sameDim = function (a, b) {
    if (!a || !b || a.length !== b.length) return false;
    for (var i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
    return true;
  };

  A.dimensionOf = function (text) {
    var raw = String(text === null || text === undefined ? '' : text).trim();
    if (!raw || raw === '1' || raw === '\u2014' || raw === '-') return A.ZERO_DIM.slice();
    var unit = A.unitOf(raw);
    return unit ? unit.dim : null;
  };

  /** Разделить «1,5·10⁻³ м» на («1,5·10⁻³», «м») по самой длинной числовой части. */
  A.splitNumberUnit = function (text) {
    var raw = String(text === null || text === undefined ? '' : text).trim();
    if (!raw) return ['', ''];
    for (var index = raw.length; index > 0; index--) {
      var head = raw.slice(0, index).trim();
      var tail = raw.slice(index).trim();
      if (!head || A.number(head) === null) continue;
      if (!tail || A.unitOf(tail) !== null) return [head, tail];
    }
    var fallback = raw.match(/^([^A-Za-z\u0410-\u044f\u0401\u0451\u00b5\u03bc\u00b0]+)\s*(.*)$/);
    if (fallback && A.number(fallback[1].trim()) !== null && fallback[2].trim()) {
      return [fallback[1].trim(), fallback[2].trim()];
    }
    return [raw, ''];
  };

  A.tolerance = function (spec) {
    if (spec.tolerance) {
      var value = Number(spec.tolerance.value);
      if (spec.tolerance.kind === 'relative') {
        return function (expected) { return Math.abs(value * expected); };
      }
      return function () { return Math.abs(value); };
    }
    if (spec.rounding !== undefined && spec.rounding !== null) {
      // как в Python: допуск по границе округления 5·10^-(знаков+1)
      var half = 5 * Math.pow(10, -(Number(spec.rounding) + 1));
      return function () { return half; };
    }
    return function () { return 1e-9; };
  };

  /** Вердикт и причина: empty | unit | dimension | missing_unit | value. */
  A.grade = function (user, spec) {
    spec = spec || {};
    var text = user === null || user === undefined ? '' : String(user).trim();
    if (!text) return { ok: false, reason: 'empty' };
    if (spec.answerType === 'choice') {
      var normalized = A.normalize(text);
      if (!normalized) return { ok: false, reason: 'empty' };
      var variants = (spec.accept || []).map(A.pick);
      if (spec.answer !== undefined && spec.answer !== null) variants.push(A.pick(spec.answer));
      for (var i = 0; i < variants.length; i++) {
        if (A.normalize(variants[i]) === normalized) return { ok: true, reason: '' };
      }
      return { ok: false, reason: 'value' };
    }
    var parts = A.splitNumberUnit(text);
    var number = A.number(parts[0]);
    if (number === null) return { ok: false, reason: 'empty' };
    var unit = parts[1] ? A.unitOf(parts[1]) : null;
    if (parts[1] && !unit) return { ok: false, reason: 'unit' };
    var policy = spec.unitPolicy || (spec.unit ? 'named' : 'optional');
    if (!unit && policy === 'required') return { ok: false, reason: 'missing_unit' };
    var dimension = spec.dimension ? A.dimensionOf(spec.dimension) : null;
    if (unit && dimension && !A.sameDim(unit.dim, dimension)) {
      return { ok: false, reason: 'dimension' };
    }
    if (spec.answerValue === undefined || spec.answerValue === null) {
      return { ok: false, reason: 'value' };
    }
    var expected = Number(spec.answerValue);
    var target = spec.unit ? A.unitOf(spec.unit) : null;
    var got;
    if (unit) {
      if (target) {
        if (!A.sameDim(unit.dim, target.dim)) return { ok: false, reason: 'dimension' };
        got = (number * unit.factor + (unit.offset || 0) - (target.offset || 0)) / target.factor;
      } else {
        if (dimension && !A.sameDim(unit.dim, dimension)) {
          return { ok: false, reason: 'dimension' };
        }
        got = number * unit.factor + (unit.offset || 0);
      }
    } else {
      got = number;
    }
    var allowed = A.tolerance(spec)(expected);
    // Double чуть менее точен, чем дроби Python: запас только относительно
    // самого значения, иначе сравнение «примерно ноль» стало бы бессмысленным.
    var slack = allowed + 1e-9 * Math.abs(expected);
    return Math.abs(got - expected) <= slack
      ? { ok: true, reason: '', value: got, unit: unit || target }
      : { ok: false, reason: 'value', value: got, unit: unit || target };
  };

  A.pick = function (value) {
    if (value === null || value === undefined) return '';
    return typeof value === 'string' ? value : I.pick(value);
  };

  /** Приведение варианта ответа: без «ответ:», с точкой вместо запятой. */
  A.normalize = function (value) {
    if (value === null || value === undefined) return '';
    var s = String(value).trim().toLowerCase();
    s = s.replace(/\u00a0/g, ' ').replace(/[\u2212\u2013\u2014\u2015]/g, '-');
    s = s.replace(/^\s*(ответ|answer)\s*[:.=]?\s*/i, '');
    s = s.replace(/^\s*[\u0430-\u044fa-z]\s*[).:]\s*/i, '');
    s = s.replace(/,/g, '.').replace(/ /g, '');
    return s;
  };

  /** Проверка ответа ученика для интерфейса: задание банка или готовая spec. */
  A.check = function (user, task) {
    if (!task) return false;
    if (task.spec) return A.grade(user, task.spec).ok;
    var spec = { answerType: task.answerType || 'number' };
    if (spec.answerType === 'choice') {
      spec.accept = (task.accept || []).concat(
        task.answer !== undefined && task.answer !== null ? [task.answer] : []);
      spec.answer = task.answer;
      return A.grade(user, spec).ok;
    }
    // без спецификации (старые данные) — сравнение по списку принимаемых записей
    var normalized = A.normalize(user).replace(/,/g, '.');
    var candidates = (task.accept || []).slice();
    if (task.answer !== undefined) candidates.push(A.pick(task.answer));
    for (var i = 0; i < candidates.length; i++) {
      var candidate = A.normalize(candidates[i]);
      if (candidate && candidate === normalized) return true;
      var left = A.number(user);
      var right = A.number(candidates[i]);
      if (left !== null && right !== null && Math.abs(left - right) <= 1e-9) return true;
    }
    return false;
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
    study: {}, lessons: {}, figures: {},
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
        self.figures = topics.figures || {};
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
    figureById: function (id) { return this.figures[id] || null; },

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

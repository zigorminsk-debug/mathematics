#!/usr/bin/env node
/* tests/native_smoke.js — the Android code path, exercised without a phone.
 *
 * Runs the same shared interface (webapp/index.html + core.js + app.js) inside
 * jsdom, but with a fake ``window.CTNative`` whose methods mirror
 * NativeBridge.kt: content comes from android/app/src/main/assets/webapp/content,
 * blobs are kept in memory, reports are collected.  Anything that would break on
 * the device — a bridge method the interface expects but the native side does
 * not implement, a blob that is not parsed, a state shape mismatch — fails here.
 *
 * jsdom is optional (same rule as tests/ui_smoke.js):
 *     npm install --no-save jsdom
 *
 * Usage:  node tests/native_smoke.js
 */
'use strict';

let JSDOM, VirtualConsole;
try {
  ({ JSDOM, VirtualConsole } = require('jsdom'));
} catch (error) {
  console.log('· native_smoke: jsdom is not installed — skipping (npm install --no-save jsdom)');
  process.exit(0);
}

const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const web = path.join(root, 'webapp');
const assets = path.join(root, 'android', 'app', 'src', 'main', 'assets', 'webapp');
const contentDir = path.join(assets, 'content');

if (!fs.existsSync(path.join(contentDir, 'bank.json'))) {
  console.error('✗ native_smoke: android assets are missing — run tools/sync_assets.py');
  process.exit(1);
}

let failures = 0;
const check = (name, condition, extra) => {
  console.log((condition ? '✓ ' : '✗ ') + name + (condition ? '' : '  ' + (extra || '')));
  if (!condition) failures += 1;
};
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const virtualConsole = new VirtualConsole();
virtualConsole.on('jsdomError', (error) => { console.log('✗ jsdom error:', error.message); failures += 1; });

const html = fs.readFileSync(path.join(web, 'index.html'), 'utf8');
const dom = new JSDOM(html, {
  url: 'https://appassets.androidplatform.net/assets/webapp/index.html',
  runScripts: 'outside-only',
  pretendToBeVisual: true,
  virtualConsole,
});
const { window } = dom;
const doc = window.document;
window.HTMLCanvasElement.prototype.getContext = () => new Proxy({}, { get: () => () => ({ measureText: () => ({ width: 9 }) }) });
window.scrollTo = () => {};

/* ------------------------------------------------------- the fake bridge --- */

const blobs = {};
const called = {};
const reports = [];
const toasts = [];
let keepScreenOn = null;
const vibrated = [];

const readSource = () => fs.readFileSync(path.join(web, 'core.js'), 'utf8');
const nativeSource = () => fs.readFileSync(path.join(web, 'app.js'), 'utf8');

window.CTNative = {
  getState() {
    called.getState = (called.getState || 0) + 1;
    return JSON.stringify({
      app: {
        version: '2026.10.1', build: '1', os: 'Android 14 (API 34)',
        platform: 'android', shell: 'webview', dataDir: '/data/user/0/by.ziv.ctmaths/files/data',
        contentDir: '/data/user/0/by.ziv.ctmaths/files/content', reportsDir: '/storage/emulated/0/Android/data/by.ziv.ctmaths/files/reports',
        repo: 'https://github.com/zigorminsk-debug/mathematics', email: 'ziv@csl.by', phone: '+3753371412',
      },
      content: { version: '2026.10.1', overlay: false },
      blobs: ['progress', 'settings', 'session'],
    });
  },
  loadBlob(key) { called.loadBlob = (called.loadBlob || 0) + 1; return Object.prototype.hasOwnProperty.call(blobs, key) ? blobs[key] : null; },
  saveBlob(key, json) { called.saveBlob = (called.saveBlob || 0) + 1; blobs[key] = json; },
  getContent(name) {
    called.getContent = (called.getContent || 0) + 1;
    const file = path.join(contentDir, name + '.json');
    return fs.existsSync(file) ? fs.readFileSync(file, 'utf8') : null;
  },
  checkUpdates(baseUrl, current) {
    called.checkUpdates = (called.checkUpdates || 0) + 1;
    return JSON.stringify({ status: 'uptodate', version: current, files: [], newTasks: 0, message: '' });
  },
  openExternal(url) { called.openExternal = url; },
  openFolder(which) { called.openFolder = which; return JSON.stringify({ ok: true, path: '/data/.../' + which }); },
  toast(message) { toasts.push(message); },
  vibrate(ms) { vibrated.push(ms); },
  setKeepScreenOn(on) { keepScreenOn = !!on; },
  saveReport(name, html) {
    reports.push({ name, html });
    return JSON.stringify({ path: '/storage/emulated/0/reports/' + name + '.html' });
  },
  quit() { called.quit = true; },
};

window.eval(readSource());
window.eval(nativeSource());

const text = () => (doc.getElementById('view') || {}).textContent || '';
const click = (node) => node.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
const buttonWith = (label) => Array.from(doc.querySelectorAll('button')).find((b) => b.textContent.trim() === label);

(async () => {
  for (let i = 0; i < 80 && !window.CT.content.bank.length; i++) await sleep(50);

  check('state requested from the native side', called.getState === 1, String(called.getState));
  check('platform reported as android', window.CT.bridge.platform === 'android', window.CT.bridge.platform);
  check('data folder from the native state', window.CT.bridge.info.dataDir === '/data/user/0/by.ziv.ctmaths/files/data');
  check('content read through the native bridge', window.CT.content.bank.length === 150, String(window.CT.content.bank.length));
  check('footer shows the native data folder', /by\.ziv\.ctmaths/.test(doc.getElementById('app-folder').textContent),
    doc.getElementById('app-folder').textContent);

  // a blob round trip: settings changed by the user must be stored natively
  window.location.hash = '#/settings';
  await sleep(80);
  const langButtons = Array.from(doc.querySelectorAll('button')).filter((b) => b.textContent.trim() === 'English');
  click(langButtons[0]);
  await sleep(40);
  check('settings blob saved natively', typeof blobs.settings === 'string' && /"lang":"en"/.test(blobs.settings), blobs.settings);
  check('saved settings are valid JSON', (() => { try { JSON.parse(blobs.settings); return true; } catch (e) { return false; } })());
  click(Array.from(doc.querySelectorAll('button')).filter((b) => b.textContent.trim() === 'Русский')[0]);
  await sleep(40);

  // data folder button goes through the native bridge
  const folderBtn = Array.from(doc.querySelectorAll('button')).find((b) => /Открыть папку/.test(b.textContent));
  click(folderBtn);
  await sleep(40);
  check('openFolder reached the native side', called.openFolder === 'data', String(called.openFolder));
  check('the interface confirmed it with a toast', /открыт/i.test(doc.getElementById('toast').textContent),
    doc.getElementById('toast').textContent);

  // update check through the bridge
  const updateBtn = Array.from(doc.querySelectorAll('button')).find((b) => /Проверить обновления/.test(b.textContent));
  click(updateBtn);
  await sleep(60);
  check('checkUpdates reached the native side', called.checkUpdates === 1, String(called.checkUpdates));
  check('up-to-date message rendered', /актуальн/i.test(text()), text().slice(0, 120));

  // a whole exam round trip: answers, vibration, progress blob
  window.location.hash = '#/exam';
  await sleep(60);
  click(Array.from(doc.querySelectorAll('button')).find((b) => b.textContent.trim() === '2024'));
  await sleep(80);
  check('exam screen opened', /Задание 1 из 30/.test(text()), text().slice(0, 90));
  const options = doc.querySelectorAll('.option');
  if (options.length) click(options[0]);
  await sleep(40);
  click(buttonWith('Завершить тест'));
  await sleep(40);
  click(Array.from(doc.querySelectorAll('.sheet button')).pop());
  await sleep(120);
  check('results screen rendered', /Результат/.test(text()), text().slice(0, 80));
  check('progress blob written natively', typeof blobs.progress === 'string' && blobs.progress.indexOf('attempts') >= 0);

  // report export writes an HTML file through the bridge
  click(buttonWith('Сохранить отчёт'));
  await sleep(80);
  check('report handed to the native side', reports.length === 1 && /<html/i.test(reports[0].html), String(reports.length));
  check('report toast shown', /Отчёт сохранён/.test(doc.getElementById('toast').textContent),
    doc.getElementById('toast').textContent);

  // keep-screen-on and vibration are wired
  window.location.hash = '#/tests';
  await sleep(80);
  const card2024 = Array.from(doc.querySelectorAll('.card')).find((card) => card.querySelector('h3') && card.querySelector('h3').textContent.indexOf('2024') >= 0);
  click(Array.from(card2024.querySelectorAll('button')).find((b) => b.textContent.trim() === 'Тренировка'));
  await sleep(80);
  check('keep screen on requested during a run', keepScreenOn === true, String(keepScreenOn));

  const back = window.CT.onAndroidBack();
  check('back from the run screen stays inside the app', back === null, String(back));

  console.log(failures ? `\n✗ ${failures} native bridge check(s) failed` : '\n✓ native bridge smoke test passed');
  process.exit(failures ? 1 : 0);
})();

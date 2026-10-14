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
let updateStatus = 'uptodate';
let foreignBank = false;
let availableVersion = fs.readFileSync(path.join(root, 'VERSION'), 'utf8').trim();
const vibrated = [];

const readSource = () => fs.readFileSync(path.join(web, 'core.js'), 'utf8');
const nativeSource = () => fs.readFileSync(path.join(web, 'app.js'), 'utf8');
// (core.js/app.js are read from webapp/; content from the Android assets copy)

window.CTNative = {
  getState() {
    called.getState = (called.getState || 0) + 1;
    return JSON.stringify({
      app: {
        version: '2026.10.1', build: '1', os: 'Android 14 (API 34)',
        platform: 'android', shell: 'webview', dataDir: '/data/user/0/by.ziv.ctrussian/files/data',
        contentDir: '/data/user/0/by.ziv.ctrussian/files/content', reportsDir: '/storage/emulated/0/Android/data/by.ziv.ctrussian/files/reports',
        repo: 'https://github.com/zigorminsk-debug/mathematics', email: 'ziv@csl.by', phone: '+3753371412',
        subject: 'russian', package: 'by.ziv.ctrussian',
      },
      content: { version: '2026.10.1', overlay: false, channel: 'russian-v' },
      blobs: ['progress', 'settings', 'session'],
    });
  },
  loadBlob(key) { called.loadBlob = (called.loadBlob || 0) + 1; return Object.prototype.hasOwnProperty.call(blobs, key) ? blobs[key] : null; },
  saveBlob(key, json) { called.saveBlob = (called.saveBlob || 0) + 1; blobs[key] = json; },
  getContent(name) {
    called.getContent = (called.getContent || 0) + 1;
    const file = path.join(contentDir, name + '.json');
    if (!fs.existsSync(file)) return null;
    const data = JSON.parse(fs.readFileSync(file, 'utf8'));
    if (data.meta) data.meta.contentVersion = availableVersion;
    if (foreignBank && data.meta) { data.meta.subject = 'mathematics'; data.meta.package = 'by.ziv.ctmaths'; }
    return JSON.stringify(data);
  },
  checkUpdatesAsync(baseUrl, current, requestId) {
    called.checkUpdatesAsync = (called.checkUpdatesAsync || 0) + 1;
    if (updateStatus === 'updated') availableVersion = '2099.1.0';
    const response = JSON.stringify({ status: updateStatus, version: availableVersion });
    window.setTimeout(() => window.CT.bridge.onUpdateResult(requestId, response), 5);
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
  check('data folder from the native state', window.CT.bridge.info.dataDir === '/data/user/0/by.ziv.ctrussian/files/data');
  check('content read through the native bridge', window.CT.content.bank.length === 240, String(window.CT.content.bank.length));
  check('the embedded bank belongs to this subject', window.CT.content.meta.subject === 'russian' && window.CT.content.meta.package === 'by.ziv.ctrussian');
  check('footer shows the native data folder', /by\.ziv\.ctrussian/.test(doc.getElementById('app-folder').textContent),
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

  // update check through the bridge (once at boot when autoUpdate is on, and
  // once more from this button)
  const updateBtn = Array.from(doc.querySelectorAll('button')).find((b) => /Проверить обновления/.test(b.textContent));
  const updatesBeforeClick = called.checkUpdatesAsync || 0;
  check('auto update checked at boot', updatesBeforeClick >= 1, String(updatesBeforeClick));
  click(updateBtn);
  await sleep(60);
  check('checkUpdates reached the native side', called.checkUpdatesAsync > updatesBeforeClick, String(called.checkUpdatesAsync));
  check('up-to-date message rendered', /последняя версия/i.test(text()), text().slice(0, 120));
  check('network checks use the asynchronous native bridge', !called.checkUpdates);
  const readsBeforeUpdate = called.getContent;
  updateStatus = 'updated';
  click(updateBtn);
  await sleep(80);
  check('manual content update reloads the bank without restarting',
    called.getContent > readsBeforeUpdate && window.CT.content.meta.contentVersion === '2099.1.0');
  check('updated content version is visible in settings', /2099\.1\.0/.test(text()));
  updateStatus = 'uptodate';

  // a whole exam round trip: answers, vibration, progress blob
  window.location.hash = '#/exam';
  await sleep(60);
  click(Array.from(doc.querySelectorAll('button')).find((b) => b.textContent.trim() === '2026'));
  await sleep(80);
  check('exam screen opened', /Задание 1 из 40/.test(text()), text().slice(0, 90));
  const options = doc.querySelectorAll('.option');
  if (options.length) click(options[0]);
  await sleep(40);
  click(buttonWith('Завершить'));
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
  const task = window.CT.runner.current();
  // part A needs several options: a single choice is always incomplete (wrong)
  click(doc.querySelectorAll('.option')[0]);
  check('first task of a variant is part A with five options', task.part === 'A' && doc.querySelectorAll('.option').length === 5);
  await sleep(20);
  click(buttonWith('Проверить'));
  await sleep(30);
  const study = doc.querySelector('.study-topic');
  check('native wrong answer opens the relevant study topic', study && study.getAttribute('data-topic') === task.topic);

  const back = window.CT.onAndroidBack();
  check('back from the run screen stays inside the app', back === null, String(back));

  // a foreign (mathematics) bank delivered through the bridge is rejected by the client
  foreignBank = true;
  let rejected = false;
  await window.CT.content.load().catch((error) => { rejected = /foreign content/.test(String(error && error.message)); });
  check('the client rejects a mathematics bank', rejected);
  foreignBank = false;

  console.log(failures ? `\n✗ ${failures} native bridge check(s) failed` : '\n✓ native bridge smoke test passed');
  process.exit(failures ? 1 : 0);
})();

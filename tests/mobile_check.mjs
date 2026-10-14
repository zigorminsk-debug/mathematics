#!/usr/bin/env node
/* tests/mobile_check.mjs — the shared interface in a REAL mobile Chromium
 * (manual gate, not run by CI: it needs a local Chromium binary).
 *
 * Emulates a 393×851 touch phone and checks, for RU/EN × light/dark × text
 * scale 1.0/1.3: no horizontal page overflow on every screen, tap targets
 * >= 44 px, every rule card (tables, decision trees, SVG) without overflow
 * outside its scroll region, the nested SVG viewer zoom + Back, and the answer
 * controls of every type. Writes screenshots and a JSON report.
 *
 *   CHROMIUM=/path/to/chrome PUPPETEER_MODULES=/path/to/node_modules node tests/mobile_check.mjs [outDir]
 * (in the build session: @sparticuz/chromium + puppeteer-core in /tmp/browser,
 *  LD_LIBRARY_PATH=/tmp/al2023/lib — see docs/WORKLOG.md)
 */
import fs from 'fs';
import http from 'http';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'windows', 'web');
const outDir = process.argv[2] || '/tmp/mobile-check';
fs.mkdirSync(outDir, { recursive: true });
const require = createRequire(path.join(process.env.PUPPETEER_MODULES || path.join(root, 'node_modules'), 'x.js'));
const puppeteer = require('puppeteer-core');

const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css',
  '.json': 'application/json; charset=utf-8', '.png': 'image/png', '.svg': 'image/svg+xml' };
const blobs = {};
const server = http.createServer((request, response) => {
  const url = new URL(request.url, 'http://local');
  const send = (status, body, type) => { response.writeHead(status, { 'Content-Type': type || 'application/json' }); response.end(body); };
  if (url.pathname === '/api/state') {
    return send(200, JSON.stringify({ app: { platform: 'windows', version: '2026.10.1', dataDir: 'C:\\Users\\student\\AppData\\Roaming\\CTRussianTutor' },
      content: { version: '2026.10.1', overlay: {}, channel: 'russian-v' } }));
  }
  if (url.pathname === '/api/blob') {
    const key = url.searchParams.get('key');
    if (request.method === 'POST') {
      let body = '';
      request.on('data', (chunk) => { body += chunk; });
      request.on('end', () => { blobs[key] = body; send(200, '{"ok":true}'); });
      return undefined;
    }
    return send(200, blobs[key] || '');
  }
  if (url.pathname.startsWith('/api/')) return send(200, JSON.stringify({ status: 'uptodate', version: '2026.10.1', path: 'C:\\r.html' }));
  const file = path.join(web, decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname));
  if (!file.startsWith(web) || !fs.existsSync(file)) return send(404, '{}');
  return send(200, fs.readFileSync(file), types[path.extname(file)] || 'application/octet-stream');
});
// BASE_URL=http://127.0.0.1:8765/index.html runs against the REAL Go backend
// (go build -o ctrussian . && ./ctrussian -no-browser -addr 127.0.0.1:8765 -data /tmp/x -idle-exit 0).
const external = process.env.BASE_URL || '';
if (!external) await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const base = external || `http://127.0.0.1:${server.address().port}/index.html`;

const browser = await puppeteer.launch({ executablePath: process.env.CHROMIUM, headless: 'shell',
  args: ['--no-sandbox', '--disable-gpu', '--single-process', '--no-zygote', '--disable-dev-shm-usage'] });
const report = { viewport: '393x851@2.75, touch', combinations: [], screenshots: [], failures: [] };
const fail = (message) => { report.failures.push(message); console.log('✗ ' + message); };

async function configure(page, lang, theme, scale) {
  const settings = JSON.stringify({ lang, theme, fontScale: scale, autoUpdate: false, autoAdvance: false });
  for (const key of Object.keys(blobs)) delete blobs[key];
  blobs.settings = settings;
  if (external) {  // store the settings through the real backend API, then reload
    await page.goto(base, { waitUntil: 'networkidle0' });
    await page.evaluate(async (body) => {
      await fetch('api/blob?key=settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body });
      await fetch('api/blob?key=session', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: 'null' });
    }, settings);
  }
  await page.goto(base, { waitUntil: 'networkidle0' });
  await page.waitForFunction(() => window.CT && window.CT.content.loaded);
}

// Mobile Chrome zooms out to fit overflowing content, which also widens
// window.innerWidth — so compare against the fixed device width instead.
const DEVICE_WIDTH = 393;
async function overflow(page, label) {
  const result = await page.evaluate((limit) => {
    const doc = document.documentElement;
    const wide = Array.from(document.querySelectorAll('body *')).filter((node) => {
      const rect = node.getBoundingClientRect();
      if (!rect.width || node.closest('.table-scroll, .diagram-viewport, .mainnav')) return false;
      return rect.right > limit + 1 || rect.left < -1;
    }).slice(0, 3).map((node) => (node.className || node.tagName) + ':' + Math.round(node.getBoundingClientRect().right));
    return { page: doc.scrollWidth - limit, wide };
  }, DEVICE_WIDTH);
  if (result.page > 1 || result.wide.length) fail(`${label}: horizontal overflow ${result.page}px ${result.wide.join(',')}`);
}

async function smallTargets(page, label) {
  const small = await page.evaluate(() => Array.from(document.querySelectorAll(
    '#view button:not(.theory-trigger), .sheet button, .nav-link, .chip, .option, .stress-letter.vowel, select'))
    .filter((node) => { const r = node.getBoundingClientRect(); return r.width > 0 && (r.height < 43.5 || r.width < 32); })
    .slice(0, 3).map((node) => `${node.className || node.tagName}:${Math.round(node.getBoundingClientRect().height)}`));
  if (small.length) fail(`${label}: tap targets below 44px: ${small.join(' ')}`);
}

const page = await browser.newPage();
await page.emulate({ viewport: { width: 393, height: 851, deviceScaleFactor: 2.75, isMobile: true, hasTouch: true },
  userAgent: 'Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0 Mobile Safari/537.36' });
page.on('pageerror', (error) => fail('page error: ' + error.message));

for (const [lang, theme, scale] of [['ru', 'light', 1], ['ru', 'dark', 1.3], ['en', 'light', 1.3], ['en', 'dark', 1]]) {
  const label = `${lang}/${theme}/${scale}`;
  await configure(page, lang, theme, scale);
  for (const hash of ['#/home', '#/tests', '#/exam', '#/practice', '#/study', '#/rules', '#/stats', '#/tools', '#/settings', '#/about']) {
    await page.evaluate((h) => { window.location.hash = h; }, hash);
    await new Promise((resolve) => setTimeout(resolve, 60));
    await overflow(page, `${label} ${hash}`);
    await smallTargets(page, `${label} ${hash}`);
  }
  // every answer type in a run
  const taskTypes = await page.evaluate(() => {
    const CT = window.CT, wanted = ['multi', 'numbers', 'word', 'match', 'integer', 'stress', 'single'];
    const picked = wanted.map((type) => CT.content.bank.concat(CT.content.analogous).find((task) => task.check.type === type)).filter(Boolean);
    CT.runner.startSet(picked, 'mobile', 'train');
    window.location.hash = '#/run'; CT.render();
    return picked.map((task) => task.check.type);
  });
  for (let index = 0; index < taskTypes.length; index++) {
    await page.evaluate((i) => { window.CT.runner.jump(i); window.CT.render(); }, index);
    await new Promise((resolve) => setTimeout(resolve, 40));
    await overflow(page, `${label} run:${taskTypes[index]}`);
    await smallTargets(page, `${label} run:${taskTypes[index]}`);
    if (lang === 'ru' && theme === 'dark') {
      const shot = path.join(outDir, `run-${taskTypes[index]}-${lang}-${theme}-${scale}.png`);
      await page.screenshot({ path: shot, fullPage: true });
      report.screenshots.push(shot);
    }
  }
  // every rule card: figures inside the sheet never overflow outside their scroll regions
  const ruleIds = await page.evaluate(() => Object.keys(window.CT.content.lessons));
  for (const id of ruleIds) {
    await page.evaluate((rule) => { window.location.hash = '#/rules'; window.CT.render();
      const row = document.querySelector('.rule-row[data-lesson="' + rule + '"]'); row.click(); }, id);
    await new Promise((resolve) => setTimeout(resolve, 20));
    await overflow(page, `${label} card:${id}`);
    if (['prep-conj-particles', 'ne-parts', 'stress', 'asyndetic'].includes(id) && theme === 'light') {
      const shot = path.join(outDir, `card-${id}-${lang}-${theme}-${scale}.png`);
      await page.screenshot({ path: shot, fullPage: false });
      report.screenshots.push(shot);
    }
    await page.evaluate(() => window.CT.onAndroidBack());
  }
  // nested SVG viewer: zoom, internal pan, Back restores the card and focus
  const viewer = await page.evaluate(async () => {
    window.location.hash = '#/study/phonetics'; window.CT.render();
    document.querySelector('.study-point-link[data-lesson="stress"]').click();
    const enlarge = document.querySelector('.diagram-enlarge');
    enlarge.focus(); enlarge.click();
    document.querySelector('.diagram-zoom-in').click(); document.querySelector('.diagram-zoom-in').click();
    const viewport = document.querySelector('.diagram-viewport');
    viewport.scrollLeft = 120;
    const panned = viewport.scrollLeft > 0;
    const width = document.querySelector('.diagram-viewport svg').style.width;
    window.CT.onAndroidBack();
    const restored = document.activeElement === enlarge && !!document.querySelector('.rule-card[data-lesson="stress"]');
    window.CT.onAndroidBack();
    return { width, panned, restored };
  });
  if (viewer.width !== '200%' || !viewer.panned || !viewer.restored) fail(`${label}: diagram viewer ${JSON.stringify(viewer)}`);
  if (lang === 'ru' && theme === 'light') {
    await page.evaluate(() => { window.location.hash = '#/home'; window.CT.render(); });
    const shot = path.join(outDir, `home-${lang}-${theme}-${scale}.png`);
    await page.screenshot({ path: shot, fullPage: true });
    report.screenshots.push(shot);
  }
  report.combinations.push({ lang, theme, scale, rulesChecked: ruleIds.length, answerTypes: taskTypes });
  console.log(`✓ ${label}: 10 screens, ${taskTypes.length} answer types, ${ruleIds.length} rule cards, viewer zoom/pan/Back`);
}

await browser.close();
if (!external) server.close();
report.browser = 'HeadlessChrome (mobile emulation)';
report.backend = external ? 'real Go backend at ' + external : 'in-process mock of the loopback API';
fs.writeFileSync(path.join(outDir, 'mobile-report.json'), JSON.stringify(report, null, 2));
console.log(report.failures.length ? `\n✗ ${report.failures.length} mobile issue(s)` : `\n✓ mobile check passed; report: ${outDir}/mobile-report.json`);
process.exit(report.failures.length ? 1 : 0);

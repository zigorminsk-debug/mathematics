#!/usr/bin/env node
/* tests/rules_smoke.js — every rule card is reachable and complete offline:
 * from each study point and each «Правила» row, in RU and EN; every figure
 * renders (safe SVG, semantic table, decision tree); the nested SVG viewer
 * zooms and pans, and one-level Back restores the exact card, scroll and focus.
 * Runs on the Android assets copy (the WebView path). */
'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
let JSDOM, VirtualConsole;
try {
  ({ JSDOM, VirtualConsole } = require('jsdom'));
} catch (_) {
  console.log('· rules_smoke: jsdom is not installed — skipping (npm install --no-save jsdom)');
  process.exit(0);
}
const root = path.join(__dirname, '..');
const assets = path.join(root, 'android/app/src/main/assets/webapp');
const read = (file) => fs.readFileSync(path.join(assets, file), 'utf8');
const errors = [];
const virtualConsole = new VirtualConsole();
virtualConsole.on('jsdomError', (error) => errors.push(error.message));
const dom = new JSDOM(read('index.html'), { url: 'https://appassets.androidplatform.net/assets/webapp/index.html',
  runScripts: 'outside-only', pretendToBeVisual: true, virtualConsole });
const { window } = dom;
const doc = window.document;
const blobs = { settings: JSON.stringify({ autoUpdate: false, lang: 'ru' }) };
window.fetch = () => Promise.reject(new Error('unexpected network request'));
window.scrollTo = () => {};
window.CTNative = {
  getState: () => JSON.stringify({ app: { platform: 'android' }, content: {} }),
  getContent: (name) => read('content/' + name + '.json'),
  loadBlob: (key) => blobs[key] || null, saveBlob: (key, json) => { blobs[key] = json; },
  setKeepScreenOn: () => {}, vibrate: () => {},
};
window.eval(read('core.js'));
window.eval(read('app.js'));
const sleep = (ms = 4) => new Promise((resolve) => setTimeout(resolve, ms));
const $ = (selector, scope) => (scope || doc).querySelector(selector);
const $$ = (selector, scope) => Array.from((scope || doc).querySelectorAll(selector));
const open = () => doc.getElementById('modal').classList.contains('open');
const route = async (hash) => { window.location.hash = hash; await sleep(); };
const kinds = { svg: 0, table: 0, tree: 0 };
const zoomed = new Set();

function checkCard(id, lang) {
  const CT = window.CT;
  const lesson = CT.content.lessonById(id);
  const article = $('.rule-card[data-lesson="' + id + '"]');
  assert(open() && article, 'card opened: ' + id);
  assert(article.textContent.includes(lesson.rule[lang][0]), 'formulation in the selected language: ' + id);
  assert(article.textContent.includes(lesson.everyday[lang][0]), 'everyday explanation: ' + id);
  assert(article.textContent.includes(lesson.steps[lang][0]), 'reasoning steps: ' + id);
  lesson.correct.forEach((example) => assert(article.textContent.includes(example), 'Russian example kept: ' + example));
  assert($('.examples-good', article).getAttribute('lang') === 'ru', 'examples are marked Russian');
  const cards = $$('.theory-figure', article);
  assert.strictEqual(cards.length, lesson.figures.length, 'every linked figure rendered: ' + id);
  cards.forEach((card, index) => {
    const figure = CT.content.figureById(lesson.figures[index]);
    kinds[figure.kind] += 1;
    assert.strictEqual(card.querySelector('h4').textContent, figure.title[lang]);
    if (figure.kind === 'svg') {
      const svg = card.querySelector('svg');
      assert(svg && svg.namespaceURI === 'http://www.w3.org/2000/svg' && svg.getAttribute('role') === 'img');
      assert.strictEqual(svg.querySelector('desc').textContent, figure.caption[lang]);
      assert(!svg.querySelector('script, image, foreignObject, use, a'), 'no executable or external SVG');
    } else if (figure.kind === 'table') {
      const table = card.querySelector('table.rule-table');
      assert(table && table.querySelector('caption').textContent === figure.caption[lang]);
      assert.strictEqual(table.querySelectorAll('thead th[scope="col"]').length, figure.columns.length);
      assert.strictEqual(table.querySelectorAll('tbody tr').length, figure.rows.length);
      assert(card.querySelector('.table-scroll[tabindex="0"]'), 'wide tables scroll inside a focusable region');
    } else {
      assert(card.querySelector('.decision-tree .tree-question') && card.querySelector('.tree-yes') && card.querySelector('.tree-no'));
    }
  });
}

async function zoomFirstSvg(id) {
  const button = $('.rule-card[data-lesson="' + id + '"] .diagram-enlarge');
  if (!button || zoomed.has(id)) return;
  zoomed.add(id);
  const sheet = $('.sheet');
  sheet.scrollTop = 97;
  const article = $('.rule-card[data-lesson="' + id + '"]');
  button.focus();
  button.click();
  await sleep();
  const expanded = $('.diagram-viewport svg');
  assert(expanded, 'nested viewer opened');
  const larger = $('.diagram-zoom-in');
  for (let i = 0; i < 5; i++) larger.click();
  assert.strictEqual(expanded.style.width, '300%');
  assert(larger.disabled, 'zoom is bounded');
  $('.diagram-zoom-out').click();
  assert.strictEqual(expanded.style.width, '250%');
  $('.diagram-zoom-reset').click();
  assert.strictEqual(expanded.style.width, '100%');
  assert.strictEqual(window.CT.onAndroidBack(), null);
  assert.strictEqual($('.rule-card[data-lesson="' + id + '"]'), article, 'Back restores the same card DOM');
  assert.strictEqual($('.sheet').scrollTop, 97, 'scroll position preserved');
  assert.strictEqual(doc.activeElement, button, 'focus returns to the enlarge control');
}

(async () => {
  for (let i = 0; i < 200 && !window.CT.content.loaded; i++) await sleep(10);
  const CT = window.CT;
  assert(CT.content.loaded);
  let fromStudy = 0, fromRules = 0;
  for (const lang of ['ru', 'en']) {
    CT.i18n.setLang(lang);
    CT.store.settings.lang = lang;
    for (const topic of CT.content.order) {
      await route('#/study/' + topic);
      const buttons = $$('.study-points-card .study-point-link');
      assert.strictEqual(buttons.length, CT.content.rulesOfTopic(topic).length, 'every rule of the area is listed');
      for (const button of buttons) {
        assert.strictEqual(button.tagName, 'BUTTON');
        assert.strictEqual(button.getAttribute('aria-haspopup'), 'dialog');
        button.focus();
        button.click();
        await sleep();
        const id = button.getAttribute('data-lesson');
        checkCard(id, lang);
        await zoomFirstSvg(id);
        assert.strictEqual(CT.onAndroidBack(), null, 'Back closes the card, not the app');
        assert(!open());
        assert.strictEqual(window.location.hash, '#/study/' + topic);
        assert.strictEqual(doc.activeElement, button, 'focus returns to the study point');
        fromStudy += 1;
      }
    }
    await route('#/rules');
    for (const row of $$('.rule-row')) {
      row.click();
      await sleep();
      checkCard(row.getAttribute('data-lesson'), lang);
      // switching language inside the card re-renders it in place
      $('.modal-lang').click();
      await sleep();
      const other = lang === 'ru' ? 'en' : 'ru';
      checkCard(row.getAttribute('data-lesson'), other);
      $('.modal-lang').click();
      await sleep();
      assert.strictEqual(CT.onAndroidBack(), null);
      fromRules += 1;
    }
  }
  assert.strictEqual(fromStudy, 2 * 54);
  assert.strictEqual(fromRules, 2 * 54);
  assert(kinds.svg > 0 && kinds.table > 0 && kinds.tree > 0, JSON.stringify(kinds));
  assert.deepStrictEqual(errors, []);
  console.log(`✓ rules_smoke: ${fromStudy} study openings and ${fromRules} «Правила» openings (RU+EN); ` +
    `figures checked svg=${kinds.svg}, table=${kinds.table}, tree=${kinds.tree}; ${zoomed.size} SVG viewers zoomed with Back/focus`);
  process.exit(0);
})().catch((error) => {
  console.error('✗ rules_smoke failed:', error && error.stack || error, errors.slice(0, 3));
  process.exit(1);
});

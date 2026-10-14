#!/usr/bin/env node
/* Every study point and formula must open offline definitions/theorems, not a
 * dead link. Also exercise Android Back, nested tools, language changes and
 * preservation of entered answers/searches. Run after sync_assets.py. */
'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
let JSDOM, VirtualConsole;
try {
  ({ JSDOM, VirtualConsole } = require('jsdom'));
} catch (_) {
  console.log('· theory_smoke: jsdom is not installed — skipping (npm install --no-save jsdom)');
  process.exit(0);
}
const root = path.join(__dirname, '..');
const assets = path.join(root, 'android/app/src/main/assets/webapp');
const read = (file) => fs.readFileSync(path.join(assets, file), 'utf8');
const errors = [];
const virtualConsole = new VirtualConsole();
virtualConsole.on('jsdomError', (error) => errors.push(error.message));
virtualConsole.on('error', (error) => errors.push(String(error)));
const dom = new JSDOM(read('index.html'), {
  url: 'https://appassets.androidplatform.net/assets/webapp/index.html',
  runScripts: 'outside-only', pretendToBeVisual: true, virtualConsole,
});
const { window } = dom;
const doc = window.document;
const blobs = { settings: JSON.stringify({ autoUpdate: false, autoAdvance: false, lang: 'ru' }) };
let networkCalls = 0;
window.fetch = () => { networkCalls++; return Promise.reject(new Error('unexpected network request')); };
window.scrollTo = () => {};
window.CTNative = {
  getState: () => JSON.stringify({ app: { platform: 'android' }, content: {} }),
  getContent: (name) => read('content/' + name + '.json'),
  loadBlob: (key) => blobs[key] || null,
  saveBlob: (key, json) => { blobs[key] = json; },
  setKeepScreenOn: () => {}, vibrate: () => {},
};
window.eval(read('core.js'));
window.eval(read('app.js'));
const sleep = (ms = 5) => new Promise((resolve) => setTimeout(resolve, ms));
const click = (node) => { assert(node, 'the expected clickable element exists'); node.click(); };
const open = () => doc.getElementById('modal').classList.contains('open');
const close = () => click(doc.querySelector('.modal-close'));
const route = async (hash) => { window.location.hash = hash; await sleep(); };
const visualCoverage = new Set();

function checkLesson(id, lang) {
  const lesson = window.CT.content.lessonById(id);
  const article = doc.querySelector('.theory-lesson[data-lesson="' + id + '"]');
  assert(open(), 'a theory dialog is open');
  assert(article, 'the correct lesson is opened: ' + id);
  assert(article.querySelector('.theory-everyday'), 'everyday explanation is rendered');
  assert(article.textContent.includes(lesson.everyday[lang][0]), 'everyday explanation uses the selected language');
  assert(article.textContent.includes(lesson.everyday[lang][1]), 'the bridge to the formal rule is present');
  const cards = Array.from(article.querySelectorAll('.theory-figure'));
  assert.equal(cards.length, lesson.figures.length, 'each linked figure is rendered');
  cards.forEach((card, index) => {
    const figure = window.CT.content.figureById(lesson.figures[index]);
    const svg = card.querySelector('svg');
    assert(svg, 'a real vector figure is present');
    assert.equal(svg.namespaceURI, 'http://www.w3.org/2000/svg');
    assert.equal(svg.getAttribute('viewBox'), '0 0 420 280');
    assert.equal(svg.getAttribute('role'), 'img');
    assert(svg.getAttribute('aria-label').includes(figure.caption[lang]));
    assert.equal(svg.querySelector('title').textContent, figure.title[lang]);
    assert.equal(svg.querySelector('desc').textContent, figure.caption[lang]);
    assert.equal(card.querySelector('figcaption').textContent, figure.caption[lang]);
    assert(!svg.querySelector('script, image, foreignObject, use, a'), 'no executable or external SVG');
    const key = lang + ':' + figure.id;
    if (visualCoverage.has(key)) return;
    visualCoverage.add(key);
    const parent = doc.querySelector('.sheet');
    const button = card.querySelector('.diagram-enlarge');
    parent.scrollTop = 117;
    click(button);
    assert(doc.querySelector('.diagram-viewer'), 'diagram opens in a nested viewer');
    const expanded = doc.querySelector('.diagram-viewport svg');
    assert.equal(expanded.getAttribute('data-figure'), figure.id);
    const larger = doc.querySelector('.diagram-zoom-in');
    for (let i = 0; i < 5; i++) click(larger);
    assert.equal(expanded.style.width, '300%');
    assert(larger.disabled, 'zoom is bounded');
    click(doc.querySelector('.diagram-zoom-out'));
    assert.equal(expanded.style.width, '250%');
    click(doc.querySelector('.diagram-zoom-reset'));
    assert.equal(expanded.style.width, '100%');
    assert.equal(window.CT.onAndroidBack(), null);
    assert.equal(doc.querySelector('.theory-lesson[data-lesson="' + id + '"]'), article,
      'one-level Back restores the exact original article/figure DOM');
    assert.equal(parent.scrollTop, 117, 'parent reading position is preserved');
    assert.equal(doc.activeElement, button, 'focus returns to the enlarge control');
  });
  assert(article.querySelector('.theory-definitions'), 'definitions are rendered');
  assert(article.querySelector('.theory-rules'), 'rules and theorems are rendered');
  assert(article.querySelector('.theory-example'), 'a worked example is rendered');
  assert(article.textContent.includes(lesson.definitions[lang][0]), 'definition uses the selected language');
  assert(article.textContent.includes(lesson.rules[lang][0]), 'theorem uses the selected language');
  assert(article.textContent.includes(lesson.examples[0].steps[lang][0]), 'solution uses the selected language');
  assert.equal(doc.getElementById('modal').getAttribute('aria-labelledby'), 'modal-title');
}

(async () => {
  for (let i = 0; i < 100 && !window.CT.content.loaded; i++) await sleep(10);
  assert(window.CT.content.loaded, 'content loaded');
  await sleep(20);
  const CT = window.CT;
  assert(doc.getElementById('mainnav').textContent.includes('Главная'));
  assert(doc.getElementById('mainnav').textContent.includes('О программе'));
  assert(!/nav_[a-z_]+/.test(doc.getElementById('mainnav').textContent));

  let points = 0, formulas = 0, groups = 0;
  for (const lang of ['ru', 'en']) {
    CT.i18n.setLang(lang);
    CT.store.settings.lang = lang;
    for (const topic of CT.content.order) {
      await route('#/study/' + topic);
      const entry = CT.content.studyFor(topic);
      const buttons = Array.from(doc.querySelectorAll('.study-points-card .study-point-link'));
      assert.equal(buttons.length, entry[lang].length, 'every summary point is clickable: ' + topic);
      for (let index = 0; index < buttons.length; index++) {
        const button = buttons[index];
        assert.equal(button.tagName, 'BUTTON', 'keyboard-accessible native control');
        assert.equal(button.getAttribute('aria-haspopup'), 'dialog');
        click(button);
        checkLesson(entry.lessons[index], lang);
        assert.equal(CT.onAndroidBack(), null, 'Android Back closes theory, not the app');
        assert(!open());
        assert.equal(window.location.hash, '#/study/' + topic, 'the original topic remains open');
        assert.equal(doc.activeElement, button, 'focus returns to the originating control');
        points++;
      }
    }
    await route('#/formulas');
    const cards = Array.from(doc.querySelectorAll('#view .formula-group'));
    assert.equal(cards.length, CT.content.formulas.length);
    for (let index = 0; index < cards.length; index++) {
      const group = CT.content.formulas[index];
      const card = cards[index];
      click(card.querySelector('.formula-group-link'));
      group.lessons.forEach((id) => checkLesson(id, lang));
      close();
      groups++;
      const rows = Array.from(card.querySelectorAll('.formula-link'));
      assert.equal(rows.length, group.items.length, 'every formula is clickable');
      rows.forEach((row, itemIndex) => {
        click(row);
        const item = group.items[itemIndex];
        checkLesson(item.lesson, lang);
        assert(doc.querySelector('.theory-formula').textContent.includes(item.formula));
        assert.equal(doc.getElementById('modal-title').textContent, item.name[lang]);
        close();
        formulas++;
      });
    }
  }

  // Language changes in a theory window also preserve a standalone search.
  CT.i18n.setLang('ru');
  CT.store.settings.lang = 'ru';
  CT.render();
  const standaloneSearch = doc.querySelector('#view input[type="search"]');
  standaloneSearch.value = 'Виета';
  standaloneSearch.dispatchEvent(new window.Event('input', { bubbles: true }));
  click(doc.querySelector('#view .formula-link'));
  click(doc.querySelector('.modal-lang'));
  checkLesson('quadratic', 'en');
  close();
  assert.equal(doc.querySelector('#view input[type="search"]').value, 'Виета');
  assert.equal(doc.querySelectorAll('#view .formula-link').length, 1);

  // Wrong answers open the same clickable definitions inside remediation.
  CT.i18n.setLang('ru');
  CT.store.settings.lang = 'ru';
  CT.runner.startVariant(CT.content.variants()[0], 'train');
  CT.runner.setAnswer(CT.runner.current().id, 'wrong');
  CT.runner.checkCurrent();
  await route('#/run');
  const wrongBlock = doc.querySelector('.study-topic');
  const view = doc.getElementById('view');
  view.scrollTop = 170;
  const savedRun = JSON.stringify(CT.store.session);
  const savedProgress = JSON.stringify(CT.store.progress);
  click(wrongBlock.querySelector('.study-point-link'));
  checkLesson(CT.content.studyFor(CT.runner.current().topic).lessons[0], 'ru');
  CT.onAndroidBack();
  assert.equal(view.scrollTop, 170, 'closing study preserves the position in the task');
  assert.equal(JSON.stringify(CT.store.session), savedRun, 'the run and its answer are unchanged');
  assert.equal(JSON.stringify(CT.store.progress), savedProgress, 'reading theory does not alter statistics');

  const analogue = doc.querySelector('.analogous-item');
  const input = analogue.querySelector('.answer-input');
  input.value = 'saved incorrect analogous answer';
  click(Array.from(analogue.querySelectorAll('button')).find((button) => button.textContent === 'Проверить'));
  click(analogue.querySelector('.study-point-link'));
  CT.onAndroidBack();
  assert.equal(input.value, 'saved incorrect analogous answer', 'the analogous input is not rebuilt or lost');
  assert.equal(doc.querySelector('.analogous-item'), analogue, 'the same task DOM is retained');

  // A theory window opened above the formula tool has a true one-level Back.
  CT.tools.sheet(CT.runner.current());
  const search = doc.querySelector('.sheet input[type="search"]');
  search.value = 'Виета';
  search.dispatchEvent(new window.Event('input', { bubbles: true }));
  const originalRow = doc.querySelector('.sheet .formula-link');
  const sheet = doc.querySelector('.sheet');
  sheet.scrollTop = 123;
  click(originalRow);
  assert(doc.querySelector('.modal-back'), 'nested theory exposes a Back control');
  checkLesson('quadratic', 'ru');
  CT.onAndroidBack();
  assert(open(), 'Back restores the formula tool instead of closing all tools');
  assert.equal(doc.querySelector('.sheet input[type="search"]'), search, 'the exact parent search node is restored');
  assert.equal(search.value, 'Виета');
  assert.equal(sheet.scrollTop, 123, 'parent formula-tool scroll is preserved');
  assert.equal(doc.activeElement, originalRow, 'focus returns to the selected formula');

  // Changing language inside theory also translates the restored parent tool.
  click(originalRow);
  click(doc.querySelector('.modal-lang'));
  checkLesson('quadratic', 'en');
  assert.equal(doc.querySelector('.analogous-item .answer-input').value, 'saved incorrect analogous answer',
    'an analogous answer also survives a theory-language change');
  assert(doc.querySelector('.analogous-item .feedback.bad').textContent.includes('Not yet'));
  click(doc.querySelector('.modal-back'));
  assert.equal(doc.getElementById('modal-title').textContent, 'Formulas');
  assert.equal(doc.querySelector('.sheet input[type="search"]').value, 'Виета');
  assert(doc.querySelector('.sheet .formula-link').textContent.includes("Vieta's theorem"),
    'the preserved Russian query still finds an English formula');

  // Escape backs out one level; the close control closes the complete stack.
  click(doc.querySelector('.sheet .formula-link'));
  doc.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
  assert(doc.querySelector('.sheet input[type="search"]'));
  click(doc.querySelector('.sheet .formula-link'));
  close();
  assert(!open());
  assert.equal(window.location.hash, '#/run');
  assert.equal(JSON.stringify(CT.store.session), savedRun);
  // Three levels: task -> formula search -> lesson -> zoom. Language changes
  // translate diagram labels/captions, retaining zoom and parent reading state.
  await route('#/run');
  const zoomProgress = JSON.stringify(CT.store.progress);
  CT.tools.sheet(CT.runner.current());
  let threeSearch = doc.querySelector('.sheet input[type="search"]');
  threeSearch.value = 'Виета';
  threeSearch.dispatchEvent(new window.Event('input', { bubbles: true }));
  click(doc.querySelector('.sheet .formula-link'));
  const parentLesson = doc.querySelector('.sheet');
  parentLesson.scrollTop = 211;
  const originalFigureButton = doc.querySelector('.diagram-enlarge');
  click(originalFigureButton);
  click(doc.querySelector('.diagram-zoom-in'));
  assert.equal(doc.querySelector('.diagram-viewport svg').style.width, '150%');
  const beforeLang = CT.i18n.lang;
  click(doc.querySelector('.modal-lang'));
  const afterLang = CT.i18n.lang;
  assert.notEqual(beforeLang, afterLang);
  assert.equal(doc.querySelector('.diagram-viewport svg').style.width, '150%', 'zoom survives language change');
  assert(doc.querySelector('.diagram-caption').textContent.includes(CT.content.figureById('parabola-roots').caption[afterLang]));
  CT.onAndroidBack();
  assert(doc.querySelector('.theory-everyday').textContent.includes(CT.content.lessonById('quadratic').everyday[afterLang][0]));
  assert.equal(doc.querySelector('.sheet').scrollTop, 211, 'translated parent retains its reading position');
  assert(doc.activeElement.classList.contains('diagram-enlarge'), 'translated Back restores focus');
  CT.onAndroidBack();
  assert.equal(doc.querySelector('.sheet input[type="search"]').value, 'Виета');
  CT.onAndroidBack();
  assert(!open());
  assert.equal(JSON.stringify(CT.store.session), savedRun);
  assert.equal(JSON.stringify(CT.store.progress), zoomProgress);

  // Downloaded SVG data is untrusted: invalid late nodes reject the whole
  // drawing; plain caption/definition text remains available. No partial SVG.
  CT.i18n.setLang('ru'); CT.store.settings.lang = 'ru';
  await route('#/study/numbers');
  const originalFigure = CT.content.figures['fraction-bar'];
  for (const bad of [
    { kind: 'script', role: 'text', filled: false },
    { kind: '__proto__', role: 'text', filled: false },
    { kind: 'constructor', role: 'text', filled: false },
    { kind: 'line', role: 'primary', filled: false, x1: 0, y1: 0, x2: 1, y2: 1, onclick: 'alert(1)' },
    { kind: 'line', role: 'primary', filled: false, x1: NaN, y1: 0, x2: 1, y2: 1 },
  ]) {
    CT.content.figures['fraction-bar'] = { ...originalFigure, drawing: [...originalFigure.drawing, bad] };
    click(doc.querySelector('.study-point-link[data-lesson="fractions"]'));
    assert(!doc.querySelector('.theory-figure svg'), 'no partially built unsafe figure');
    assert(doc.querySelector('.theory-figure figcaption').textContent.includes(originalFigure.caption.ru));
    close();
  }
  const escaped = JSON.parse(JSON.stringify(originalFigure));
  escaped.drawing.push({ kind: 'text', role: 'text', filled: false, x: 15, y: 15,
    anchor: 'start', text: { ru: '<img src=x onerror=alert(1)>', en: '<img src=x onerror=alert(1)>' } });
  CT.content.figures['fraction-bar'] = escaped;
  click(doc.querySelector('.study-point-link[data-lesson="fractions"]'));
  assert(doc.querySelector('.theory-figure svg').textContent.includes('<img src=x onerror=alert(1)>'));
  assert(!doc.querySelector('.theory-figure img'), 'SVG labels are text, never markup');
  close();
  CT.content.figures['fraction-bar'] = originalFigure;
  assert.equal(visualCoverage.size, 104, 'all 52 diagrams enlarged in both languages');
  assert.equal(networkCalls, 0, 'studying definitions/theorems is entirely offline');
  assert.deepEqual(errors, [], 'no JavaScript or DOM errors');
  process.stdout.write(`✓ theory journeys: ${points} points, ${groups} sections, ${formulas} formulas (RU/EN), ` +
    '56 everyday explanations, 104 figure zooms, offline SVG safety, nested Back, language, answers/searches preserved\n');
  dom.window.close();
})().catch((error) => {
  process.stderr.write('✗ theory journey failed: ' + error.stack + '\n');
  dom.window.close();
  process.exitCode = 1;
});

#!/usr/bin/env node
/* tests/ui_smoke.js — whole-interface journeys in jsdom through the Windows code
 * path (fetch to the loopback API, content from windows/web/content):
 * training with every answer type, exam, wrong answer → rule card → analogs,
 * results/mistakes/reinforcement, report, statistics, offline, Back, rule search,
 * RU/EN with untranslated Russian material, settings (dark, font 1.3), diagrams.
 *
 * Usage: npm install --no-save jsdom && node tests/ui_smoke.js
 */
'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
let JSDOM, VirtualConsole;
try {
  ({ JSDOM, VirtualConsole } = require('jsdom'));
} catch (_) {
  console.log('· ui_smoke: jsdom is not installed — skipping (npm install --no-save jsdom)');
  process.exit(0);
}

const root = path.join(__dirname, '..');
const web = path.join(root, 'windows', 'web');
const read = (file) => fs.readFileSync(path.join(web, file), 'utf8');
const errors = [];
const virtualConsole = new VirtualConsole();
virtualConsole.on('jsdomError', (error) => errors.push(error.message));
virtualConsole.on('error', (error) => errors.push(String(error)));
const dom = new JSDOM(read('index.html'), { url: 'http://127.0.0.1:8123/index.html', runScripts: 'outside-only',
  pretendToBeVisual: true, virtualConsole });
const { window } = dom;
const doc = window.document;
window.scrollTo = () => {};
window.HTMLElement.prototype.scrollIntoView = function () {};

const blobs = { settings: JSON.stringify({ autoUpdate: false, autoAdvance: false, lang: 'ru' }) };
const requests = [], reports = [];
const respond = (body, status) => Promise.resolve({ ok: (status || 200) < 400, status: status || 200,
  json: () => Promise.resolve(typeof body === 'string' ? JSON.parse(body) : body),
  text: () => Promise.resolve(typeof body === 'string' ? body : JSON.stringify(body)) });
window.fetch = (url, options) => {
  requests.push(String(url));
  if (/^[a-z]+:\/\//i.test(String(url))) return Promise.reject(new Error('unexpected network request ' + url));
  const [route, query] = String(url).split('?');
  if (route === 'api/state') return respond({ app: { platform: 'windows', dataDir: 'C:\\Users\\u\\AppData\\Roaming\\CTRussianTutor',
    version: '2026.10.1', subject: 'russian' }, content: { version: '2026.10.1', overlay: {}, channel: 'russian-v' } });
  if (route === 'api/blob') {
    const key = decodeURIComponent(query.split('=')[1]);
    if (options && options.method === 'POST') { blobs[key] = options.body; return respond({ ok: true }); }
    return respond(blobs[key] || '');
  }
  if (route === 'api/report') { reports.push(JSON.parse(options.body)); return respond({ path: 'C:\\reports\\r.html' }); }
  if (route === 'api/update') return respond({ status: 'uptodate', version: '2026.10.1' });
  if (route.indexOf('content/') === 0) return respond(read(route));
  return respond({ error: 'not found' }, 404);
};
window.eval(read('core.js'));
window.eval(read('app.js'));

const sleep = (ms = 8) => new Promise((resolve) => setTimeout(resolve, ms));
const $ = (selector, scope) => (scope || doc).querySelector(selector);
const $$ = (selector, scope) => Array.from((scope || doc).querySelectorAll(selector));
const view = () => doc.getElementById('view');
const click = (node, message) => { assert(node, message || 'expected a clickable element'); node.click(); };
const button = (label, scope) => $$('button', scope).find((node) => node.textContent.trim() === label);
const route = async (hash) => {
  if (window.location.hash === hash) window.CT.render(); else window.location.hash = hash;
  await sleep(15);
};
const modalOpen = () => doc.getElementById('modal').classList.contains('open');
const type = (input, value) => { input.value = value; input.dispatchEvent(new window.Event('input', { bubbles: true })); };
let passed = 0;
const step = (name) => { passed += 1; console.log('✓ ' + name); };

function sample(spec) {
  if (spec.type === 'multi' || spec.type === 'numbers') return spec.answer.join(' ');
  if (spec.type === 'single' || spec.type === 'integer') return String(spec.answer);
  if (spec.type === 'word') return spec.answer;
  if (spec.type === 'stress') return spec.display;
  return spec.labels.map((label) => label + spec.answer[label]).join('');
}

/** Answer the visible task card through its own controls. */
function answerCard(card, task, correct) {
  const spec = task.check;
  if (spec.type === 'multi' || spec.type === 'single') {
    const wanted = correct ? (spec.type === 'multi' ? spec.answer : [spec.answer]) : [spec.type === 'multi' ? spec.answer[0] : (spec.answer % spec.options) + 1];
    wanted.forEach((n) => click($(`.option[data-index="${n}"]`, card)));
  } else if (spec.type === 'numbers') {
    if (correct && spec.order === 'unordered') spec.answer.forEach((n) => click($(`.chip[data-n="${n}"]`, card)));
    else type($('.answer-control input', card), correct ? sample(spec) : String(spec.max) + ' ' + String(spec.max));
  } else if (spec.type === 'stress') {
    click($(`.stress-letter[data-i="${correct ? spec.answer : (spec.answer + 1) % spec.word.length}"]`, card) ||
      $$('.stress-letter.vowel', card).find((node) => Number(node.getAttribute('data-i')) !== spec.answer));
  } else if (spec.type === 'match') {
    spec.labels.forEach((label, index) => {
      const select = $$('.match-select', card)[index];
      select.value = String(correct ? spec.answer[label] : (spec.answer[label] % spec.right) + 1);
      select.dispatchEvent(new window.Event('change', { bubbles: true }));
    });
  } else {
    type($('.answer-control input', card), correct ? '  ' + sample(spec) + '  ' : sample(spec).replace(/ /g, '') + 'x');
  }
}

(async () => {
  for (let i = 0; i < 200 && !window.CT.content.loaded; i++) await sleep(10);
  await sleep(30);
  const CT = window.CT;
  assert(CT.content.loaded, 'content loaded through the Windows API');
  assert.strictEqual(CT.content.meta.subject, 'russian');
  const nav = doc.getElementById('mainnav').textContent;
  ['Главная', 'Варианты', 'Тренировка', 'Изучение', 'Правила', 'Статистика', 'Инструменты', 'О программе']
    .forEach((label) => assert(nav.indexOf(label) >= 0, 'navigation has ' + label));
  assert(nav.indexOf('Формул') < 0, 'no maths formula sheet in the navigation');
  assert.strictEqual(doc.title, 'Репетитор ЦТ: Русский язык');
  step('boot: Russian tutor, eight sections, «Правила» instead of formulas');

  for (const hash of ['#/home', '#/tests', '#/exam', '#/practice', '#/study', '#/rules', '#/stats', '#/tools', '#/settings', '#/about']) {
    await route(hash);
    assert(!/\b[a-z]+_[a-z_]+\b/.test(view().textContent), 'no raw string keys on ' + hash);
  }
  await route('#/tools');
  assert(!/Калькулятор|График|Calculator/.test(view().textContent), 'calculator/plotter hidden');
  step('every screen renders translated strings; calculator and plotter are gone');

  // training: every task of a variant answered correctly through its control
  const variant = CT.content.variants().find((v) => v.year === 2026);
  CT.runner.startVariant(variant, 'train');
  await route('#/run');
  const types = new Set();
  for (let index = 0; index < variant.tasks.length; index++) {
    CT.runner.jump(index); CT.render(); await sleep(2);
    const task = CT.runner.current();
    const card = $('.task-card');
    answerCard(card, task, true);
    click(button('Проверить', card));
    await sleep(2);
    assert(/Верно/.test($('.feedback').textContent), `${task.id} (${task.check.type}) correct through the UI`);
    types.add(task.check.type);
  }
  ['multi', 'numbers', 'word', 'match'].forEach((kind) => assert(types.has(kind), 'variant uses ' + kind));
  step('training: all 40 tasks of variant 2026 answered through multi/number/word/match controls');

  // wrong answer → misjudged options, typical error, rule card, analogs by rule
  const second = CT.content.variants().find((v) => v.year === 2025);
  CT.runner.startVariant(second, 'train');
  await route('#/run');
  let task = CT.runner.current();
  answerCard($('.task-card'), task, false);
  click(button('Проверить', $('.task-card')));
  await sleep(10);
  assert(/Неверно/.test($('.feedback').textContent));
  assert($('.breakdown .banner.bad'), 'misjudged options are named');
  assert($('.breakdown .why'), 'typical error diagnosis shown');
  const remedy = $('.remedy-rule-link');
  const ruleId = remedy.getAttribute('data-lesson');
  assert(task.rules.indexOf(ruleId) >= 0 || task.itemRules.indexOf(ruleId) >= 0, 'remediation names a rule of the task');
  remedy.focus(); click(remedy); await sleep(5);
  assert(modalOpen() && $('.rule-card[data-lesson="' + ruleId + '"]'), 'the rule card opens');
  ['.theory-rules', '.theory-exceptions', '.theory-everyday', '.theory-example', '.theory-steps', '.theory-sources']
    .forEach((selector) => assert($(selector), 'rule card section ' + selector));
  assert.strictEqual(CT.onAndroidBack(), null);
  assert(!modalOpen() && doc.activeElement === remedy, 'Back closes the card and restores focus');
  const analogs = $$('.analogous-item');
  assert(analogs.length >= 1, 'analogous exercises offered');
  const analogTask = CT.content.taskById(analogs[0].getAttribute('data-task-id'));
  assert(C_rules(task, analogTask), 'the analog drills one of the misjudged rules');
  answerCard(analogs[0], analogTask, true);
  click(button('Проверить', analogs[0])); await sleep(5);
  assert(/good/.test($('.feedback', analogs[0]).className), 'analog checked in place');
  step('wrong answer: misjudged options, diagnosis, rule card with Back/focus, analog of the same rule');

  function C_rules(original, analog) {
    return CT.content.rulesFor(original, CT.store.session.answers[original.id]).indexOf(analog.rule) >= 0;
  }

  // significant spaces/hyphens are part of the answer
  const wordTask = CT.content.bank.find((t) => t.check.type === 'word' && / /.test(t.check.answer));
  CT.runner.startSet([wordTask], 'word', 'train'); await route('#/run');
  type($('.answer-control input'), wordTask.check.answer.replace(/ /g, ''));
  click(button('Проверить', $('.task-card'))); await sleep(5);
  assert(/Неверно/.test($('.feedback').textContent), 'deleting a significant space is wrong');
  const input = $('.answer-control input');
  assert.strictEqual(input.getAttribute('autocorrect'), 'off');
  assert.strictEqual(input.getAttribute('spellcheck'), 'false');
  assert.strictEqual(input.getAttribute('autocapitalize'), 'none');
  step('word answers: significant space checked; autocorrect/spellcheck/capitalisation off');

  // stress task through letter buttons; ordered sequence through chips
  const stressTask = CT.content.analogous.find((t) => t.check.type === 'stress');
  const sequenceTask = CT.content.analogous.find((t) => t.check.type === 'numbers' && t.check.order === 'ordered');
  CT.runner.startSet([stressTask, sequenceTask], 'mixed', 'train'); await route('#/run');
  click($(`.stress-letter[data-i="${stressTask.check.answer}"]`));
  assert.strictEqual($('.answer-control input').value, stressTask.check.display);
  click(button('Проверить', $('.task-card'))); await sleep(5);
  assert(/Верно/.test($('.feedback').textContent), 'stress tapped');
  CT.runner.step(1); CT.render(); await sleep(5);
  sequenceTask.check.answer.forEach((n) => click($(`.chip[data-n="${n}"]`)));
  assert.strictEqual($('.chip[data-n="' + sequenceTask.check.answer[0] + '"] .chip-order').textContent, '1');
  click(button('Проверить', $('.task-card'))); await sleep(5);
  assert(/Верно/.test($('.feedback').textContent), 'ordered sequence through chips');
  step('stress by tapping the vowel; ordered sequence keeps the click order');

  // exam: timer, no checking/hints, result, mistakes, reinforcement by rule, report
  await route('#/exam');
  click(button('2024')); await sleep(15);
  assert(/Задание 1 из 40/.test(view().textContent));
  assert(/\d+ мин/.test($('#run-timer').textContent), 'exam timer runs (120 minutes by default)');
  assert.strictEqual(CT.store.settings.examMinutes, 120);
  assert(!button('Проверить', $('.task-card')), 'no check button in an exam');
  assert(button('Подсказка').disabled, 'hints disabled in an exam');
  const examTasks = CT.content.variants().find((v) => v.year === 2024).tasks;
  for (let index = 0; index < 10; index++) {
    CT.runner.jump(index); CT.render(); await sleep(2);
    answerCard($('.task-card'), examTasks[index], index % 2 === 0);
  }
  click(button('Завершить')); await sleep(5);
  click($$('.sheet button').pop()); await sleep(20);
  assert(/Результат/.test(view().textContent) && /Верно 5 из 40/.test(view().textContent), view().textContent.slice(0, 200));
  click($$('button', view()).find((node) => /Разобрать ошибки/.test(node.textContent))); await sleep(20);
  assert(/Разбор ошибок/.test(view().textContent) && $('.plan-rule-link'), 'mistakes screen with a rule plan');
  click(button('Закрепить: аналогичные упражнения')); await sleep(15);
  const reinforcement = CT.store.session;
  assert(reinforcement.kind === 'set' && reinforcement.order.every((id) => id.indexOf('an-') === 0), 'reinforcement uses analogs');
  step('exam: 120-minute timer, no hints/checks, result 5/40, mistakes by rule, reinforcement with analogs');

  await route('#/stats');
  assert(/По областям программы/.test(view().textContent) && $('.bar-row'), 'statistics by area');
  click(button('Сохранить отчёт')); await sleep(15);
  assert(reports.length === 1 && /Отчёт о подготовке: русский язык/.test(reports[0].html), 'report saved through the API');
  assert(/lang="ru"/.test(reports[0].html), 'correct answers in the report are marked Russian');
  step('statistics and a self-contained HTML report');

  // rules: search, language switch keeps the query, Russian examples stay Russian
  await route('#/rules');
  type($('input[type="search"]'), 'тоже');
  const rows = $$('.rule-row');
  assert(rows.length >= 1 && rows.every((row) => /тоже|ТОЖЕ|Тоже/i.test(row.textContent)), 'search finds the тоже/то же rule');
  click(doc.getElementById('lang-toggle')); await sleep(15);
  assert.strictEqual($('input[type="search"]').value, 'тоже', 'the query survives the language switch');
  assert(/Rules/.test(doc.getElementById('mainnav').textContent));
  assert(/Я тоже пойду\./.test(view().textContent), 'Russian examples are not translated');
  click($('.rule-row')); await sleep(5);
  assert(modalOpen() && $('.rule-table') && $('.rule-table caption') && $$('.rule-table th[scope="col"]').length >= 2,
    'contrast table is semantic HTML with caption and headers');
  assert.strictEqual(CT.onAndroidBack(), null);
  step('«Правила»: search, EN switch keeps query, Russian examples untranslated, semantic tables');

  // EN interface keeps the checked Russian material
  CT.runner.startVariant(CT.content.variants().find((v) => v.year === 2023), 'train');
  await route('#/run');
  task = CT.runner.current();
  assert.strictEqual($('.task-text').textContent, task.instruction.en, 'instruction in English');
  $$('.option-value').forEach((node, index) => {
    assert.strictEqual(node.textContent, task.items[index], 'Russian option stays Russian');
    assert.strictEqual(node.getAttribute('lang'), 'ru');
  });
  click(doc.getElementById('lang-toggle')); await sleep(15);
  step('EN interface: English instruction, untranslated Russian items with lang="ru"');

  // decision tree and SVG figure inside rule cards
  CT.ui = undefined;
  await route('#/study/spelling-ne');
  click($$('.study-point-link').find((node) => node.getAttribute('data-lesson') === 'ne-parts')); await sleep(5);
  assert($('.decision-tree .tree-question') && $('.tree-yes') && $('.tree-no'), 'decision tree with yes/no branches');
  assert.strictEqual(CT.onAndroidBack(), null);
  await route('#/study/phonetics');
  click($$('.study-point-link').find((node) => node.getAttribute('data-lesson') === 'stress')); await sleep(5);
  const svg = $('.theory-figure svg');
  assert(svg && svg.getAttribute('viewBox') === '0 0 420 280' && !svg.querySelector('script, image, foreignObject, use, a'));
  assert($('.diagram-accent'), 'the stressed vowel is highlighted');
  assert.strictEqual(CT.onAndroidBack(), null);
  step('decision trees and safe SVG schemes in rule cards');

  // settings: dark theme and font scale 1.3
  await route('#/settings');
  click(button('Тёмное')); await sleep(5);
  assert.strictEqual(doc.documentElement.getAttribute('data-theme'), 'dark');
  click(button('Очень крупный')); await sleep(5);
  assert.strictEqual(doc.documentElement.style.getPropertyValue('--font-scale'), '1.3');
  step('dark theme and text scale 1.3');

  // Back navigation and offline behaviour
  await route('#/rules');
  assert.strictEqual(CT.onAndroidBack(), null);
  await sleep(10);
  assert.strictEqual(window.location.hash, '#/home');
  assert.strictEqual(CT.onAndroidBack(), 'exit');
  assert(requests.every((url) => !/^[a-z]+:\/\//i.test(url)), 'only relative local API/content requests');
  step('Back returns home then exits; no external network requests');

  assert.deepStrictEqual(errors, [], 'no runtime errors');
  console.log(`\n✓ ui_smoke: ${passed} journeys passed`);
  process.exit(0);
})().catch((error) => {
  console.error('✗ ui_smoke failed:', error && error.stack || error);
  console.error('runtime errors:', errors.slice(0, 5));
  process.exit(1);
});

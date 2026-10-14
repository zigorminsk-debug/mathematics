#!/usr/bin/env node
/* tests/content_schema.js — structural checks of the built content bank and of
 * the interface strings.
 *
 *  * every task of bank.json / analogous.json has the fields the interface
 *    relies on, unique ids and a non-empty bilingual solution;
 *  * every ui_strings key referenced from webapp/*.js actually exists (so a
 *    typo cannot leave a raw key on the screen);
 *  * the auxiliary banks (topics, formulas, mistakes) keep their shape.
 *
 * Usage: node tests/content_schema.js
 */
'use strict';

const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const contentDir = path.join(root, 'dist', 'content');
const read = (name) => JSON.parse(fs.readFileSync(path.join(contentDir, name + '.json'), 'utf8'));

let failures = 0;
const fail = (message) => { failures++; console.error('✗ ' + message); };

function checkTask(task, where) {
  const required = ['id', 'year', 'part', 'n', 'topic', 'answerType', 'text', 'answer', 'solution'];
  required.forEach((field) => {
    if (!(field in task)) fail(`${where}: ${task.id || '?'} misses "${field}"`);
  });
  if (!task.text || !task.text.ru || !task.text.en) fail(`${where}: ${task.id} has no bilingual statement`);
  if (!task.solution || !task.solution.ru || !task.solution.en) fail(`${where}: ${task.id} has no bilingual solution`);
  if (!Array.isArray(task.solution.ru) || task.solution.ru.length < 2) fail(`${where}: ${task.id} solution too short`);
  if (!Array.isArray(task.accept) || !task.accept.length) fail(`${where}: ${task.id} has no accepted answers`);
  if (!Array.isArray(task.tools) || !task.tools.length) fail(`${where}: ${task.id} lists no tools`);
  if (task.part === 'A') {
    if (task.answerType !== 'choice') fail(`${where}: ${task.id} part A must be a choice task`);
    if (!task.options || !task.options.ru || task.options.ru.length !== 5) {
      fail(`${where}: ${task.id} part A must have exactly five options`);
    }
  }
}

const bank = read('bank');
const analogous = read('analogous');

[...bank.tasks.map((t) => [t, 'bank']), ...analogous.tasks.map((t) => [t, 'analogous'])]
  .forEach(([task, where]) => checkTask(task, where));

const ids = new Set();
[...bank.tasks, ...analogous.tasks].forEach((task) => {
  if (ids.has(task.id)) fail(`duplicate task id ${task.id}`);
  ids.add(task.id);
});

const years = new Set(bank.tasks.map((t) => t.year).filter(Boolean));
if (years.size < 6) fail(`expected six exam years (2021–2026), found ${[...years].join(', ')}`);
if (!years.has(2026)) fail('the 2026 variant is missing from the bank');
bank.tasks.forEach((task) => {
  if (!['A', 'B'].includes(task.part)) fail(`${task.id}: unknown part ${task.part}`);
});

const topics = read('topics');
if (!topics.topics || !Object.keys(topics.topics).length) fail('topics.json has no topics');
if (!topics.counts || !Object.keys(topics.counts).length) fail('topics.json has no per-topic counts');

/* Тема для изучения: при неверном ответе приложение открывает тему задания,
 * поэтому у каждой темы обязаны быть конспект и существующие разделы формул. */
if (!topics.study || !Object.keys(topics.study).length) fail('topics.json has no study notes');
(topics.order || Object.keys(topics.topics || {})).forEach((topic) => {
  const entry = (topics.study || {})[topic];
  if (!entry) { fail(`topic "${topic}" has no study notes to open on a wrong answer`); return; }
  if (!Array.isArray(entry.ru) || entry.ru.length < 2) fail(`study notes for "${topic}" are too short (ru)`);
  if (!Array.isArray(entry.en) || entry.en.length < 2) fail(`study notes for "${topic}" are too short (en)`);
  if (!Array.isArray(entry.formulas) || !entry.formulas.length) fail(`study notes for "${topic}" name no formula group`);
  if (!Array.isArray(entry.lessons) || entry.lessons.length !== entry.ru.length || entry.lessons.length !== entry.en.length) {
    fail(`study notes for "${topic}" need one theory link per point`);
  }
  (entry.lessons || []).forEach((id) => {
    if (!(topics.lessons || {})[id]) fail(`study point in "${topic}" links to missing theory "${id}"`);
  });
});
const unknownTopics = new Set();
bank.tasks.concat(analogous.tasks).forEach((task) => {
  if (!topics.topics[task.topic]) unknownTopics.add(task.topic);
});
if (unknownTopics.size) fail('tasks reference unknown topics: ' + [...unknownTopics].join(', '));

const lessons = topics.lessons || {};
if (!Object.keys(lessons).length) fail('topics.json has no detailed lessons');
const bilingualLines = (value, where, minimum = 1) => {
  ['ru', 'en'].forEach((lang) => {
    const lines = value && value[lang];
    if (!Array.isArray(lines) || lines.length < minimum || lines.some((line) => typeof line !== 'string' || !line.trim())) {
      fail(`${where} is incomplete (${lang})`);
    }
  });
  if (value && value.ru && value.en && value.ru.length !== value.en.length) fail(`${where} differs between languages`);
};
Object.entries(lessons).forEach(([id, lesson]) => {
  if (id !== lesson.id || !/^[a-z][a-z0-9-]*$/.test(id)) fail(`invalid theory lesson id "${id}"`);
  if (!lesson.title || !lesson.title.ru || !lesson.title.en) fail(`lesson "${id}" has no bilingual title`);
  bilingualLines(lesson.everyday, `lesson "${id}" everyday explanations`, 2);
  if (!Array.isArray(lesson.figures) || new Set(lesson.figures).size !== lesson.figures.length) fail(`lesson "${id}" has invalid figure links`);
  (lesson.figures || []).forEach((figure) => { if (!(topics.figures || {})[figure]) fail(`lesson "${id}" links to missing figure "${figure}"`); });
  bilingualLines(lesson.definitions, `lesson "${id}" definitions`);
  bilingualLines(lesson.rules, `lesson "${id}" theorems/rules`);
  if (!Array.isArray(lesson.examples) || !lesson.examples.length) fail(`lesson "${id}" has no example`);
  (lesson.examples || []).forEach((example) => {
    if (!example.statement || !example.statement.ru || !example.statement.en) fail(`lesson "${id}" has no example statement`);
    bilingualLines(example.steps, `lesson "${id}" worked example`, 2);
  });
});

const figures = topics.figures || {};
const usedFigures = new Set(Object.values(lessons).flatMap((lesson) => lesson.figures || []));
if (Object.keys(figures).length < 50) fail('offline mathematical figure catalogue is incomplete');
Object.entries(figures).forEach(([id, figure]) => {
  if (id !== figure.id || !/^[a-z][a-z0-9-]*$/.test(id)) fail(`invalid figure id "${id}"`);
  if (!usedFigures.has(id)) fail(`unreachable diagram "${id}"`);
  if (!figure.title || !figure.title.ru || !figure.title.en || !figure.caption || !figure.caption.ru || !figure.caption.en) fail(`diagram "${id}" is not bilingual`);
  if (figure.width !== 420 || figure.height !== 280 || !Array.isArray(figure.drawing) || !figure.drawing.length) fail(`diagram "${id}" is not drawable`);
  (figure.drawing || []).forEach((node) => {
    const allowed = { line: ['x1','y1','x2','y2'], circle: ['cx','cy','r'], ellipse: ['cx','cy','rx','ry'],
      rect: ['x','y','width','height'], polyline: ['points'], polygon: ['points'], text: ['x','y','text','anchor'] };
    if (!Object.hasOwn(allowed, node.kind)) { fail(`diagram "${id}" contains unsafe primitive`); return; }
    if (Object.keys(node).some((key) => !['kind','role','filled',...allowed[node.kind]].includes(key))) fail(`diagram "${id}" contains unsafe attributes`);
    if (node.kind === 'text' && (!node.text || !node.text.ru || !node.text.en)) fail(`diagram "${id}" has untranslated labels`);
    if (node.points && node.points.some((point) => !Array.isArray(point) || point.length !== 2 || point.some((value) => typeof value !== 'number' || !Number.isFinite(value)))) fail(`diagram "${id}" has invalid coordinates`);
  });
});

const formulas = read('formulas');
if (!Array.isArray(formulas.groups) || formulas.groups.length < 5) fail('formulas.json is too small');
const formulaGroupIds = new Set(formulas.groups.map((group) => group.id));
Object.keys(topics.study || {}).forEach((topic) => {
  (topics.study[topic].formulas || []).forEach((id) => {
    if (!formulaGroupIds.has(id)) fail(`study notes for "${topic}" reference the missing formula group "${id}"`);
  });
});
formulas.groups.forEach((group) => {
  if (!group.items || !group.items.length) fail(`formula group ${group.id} is empty`);
  if (!Array.isArray(group.lessons) || !group.lessons.length) fail(`formula group ${group.id} has no theory`);
  (group.lessons || []).forEach((id) => {
    if (!lessons[id]) fail(`formula group "${group.id}" links to missing theory "${id}"`);
  });
  group.items.forEach((item) => {
    if (!item.formula) fail(`formula "${JSON.stringify(item.name)}" has no body`);
    if (!item.name || !item.name.ru || !item.name.en) fail(`formula in ${group.id} is not bilingual`);
    if (!lessons[item.lesson] || !(group.lessons || []).includes(item.lesson)) fail(`formula in ${group.id} links to missing theory`);
  });
});

const mistakes = read('mistakes');
if (!mistakes.errors || Object.keys(mistakes.errors).length < 50) fail('mistakes.json catalogue is too small');
if (!Array.isArray(mistakes.checklist) || !mistakes.checklist.length) fail('mistakes.json has no checklist');
Object.keys(mistakes.errors).forEach((tag) => {
  const entry = mistakes.errors[tag];
  if (!entry.ru || !entry.en) fail(`typical error "${tag}" is not bilingual`);
});

const ui = read('ui_strings').strings;
if (!ui || Object.keys(ui).length < 50) fail('ui_strings.json is too small');
Object.keys(ui).forEach((key) => {
  const entry = ui[key];
  if (!entry.ru || !entry.en) fail(`string "${key}" is not bilingual`);
});

/* Every t('key') used by the interface must exist in the catalogue. */
const usedKeys = new Set();
['core.js', 'app.js'].forEach((file) => {
  const source = fs.readFileSync(path.join(root, 'webapp', file), 'utf8');
  // the localisation helper t('key', ...) — the lookbehind skips look-alikes such
  // as document.createElement('div') or getContext('2d')
  const pattern = /(?<![A-Za-z0-9_$.])t\(\s*['"]([a-z0-9_]+)['"]/g;
  let match;
  while ((match = pattern.exec(source)) !== null) usedKeys.add(match[1]);
  // NAV and the theory panels pass keys indirectly to t(...). Validate these
  // too: the previous literal-only gate missed nav_home and nav_about.
  const indirect = /['"]((?:nav_|theory_)[a-z0-9_]+)['"]/g;
  while ((match = indirect.exec(source)) !== null) usedKeys.add(match[1]);
});
usedKeys.forEach((key) => {
  if (!ui[key]) fail(`the interface uses the missing string "${key}"`);
});

const version = read('version');
if (!version.contentVersion) fail('version.json has no contentVersion');
if (!version.files || !Object.keys(version.files).length) fail('version.json lists no files');
if (!Array.isArray(version.years) || version.years.length < 5) fail('version.json has no exam years');

/* Периоды (годы ЦТ): манифест должен совпадать с тем, что реально лежит в банке. */
if (!Array.isArray(version.periods) || version.periods.length !== version.years.length) {
  fail('version.json has no period manifest');
} else {
  version.periods.forEach((period) => {
    if (!period.year || !period.parts || !period.label || !period.label.ru || !period.label.en) {
      fail('period entry is incomplete: ' + JSON.stringify(period));
      return;
    }
    if (!version.years.includes(period.year)) fail(`period ${period.year} is not in the years list`);
    const inBank = bank.tasks.filter((task) => task.year === period.year);
    if (inBank.length !== period.tasks) {
      fail(`period ${period.year}: manifest says ${period.tasks} tasks, the bank has ${inBank.length}`);
    }
    const partA = inBank.filter((task) => task.part === 'A').length;
    const partB = inBank.filter((task) => task.part === 'B').length;
    if (partA !== period.parts.A || partB !== period.parts.B) {
      fail(`period ${period.year}: parts mismatch (A ${partA}/${period.parts.A}, B ${partB}/${period.parts.B})`);
    }
  });
  if (!version.disclaimer || !version.disclaimer.ru || !version.disclaimer.en) {
    fail('version.json has no bilingual disclaimer');
  }
  if (!(version.examMinutes > 0)) fail('version.json has no exam duration');
}

if (failures) {
  console.error(`✗ ${failures} content problem(s) found`);
  process.exit(1);
}
console.log(`✓ content schema: ${bank.tasks.length} exam tasks, ${analogous.tasks.length} analogous, ` +
  `${Object.keys(ui).length} interface strings, ${Object.keys(lessons).length} everyday/detailed lessons, ${Object.keys(figures).length} offline figures, ` +
  `${Object.keys(mistakes.errors).length} error diagnoses, ` +
  `${usedKeys.size} strings referenced by the UI`);

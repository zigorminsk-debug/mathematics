#!/usr/bin/env node
/* tests/content_schema.js — the shipped content (Android assets copy, identical to
 * windows/web/content) is a complete Russian-language bank: subject identity,
 * 2026 blueprint, rule links, lessons/figures, interface strings and the update
 * manifest with exact digests.
 */
'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const dir = path.join(root, 'android', 'app', 'src', 'main', 'assets', 'webapp', 'content');
const windowsDir = path.join(root, 'windows', 'web', 'content');
const load = (name) => JSON.parse(fs.readFileSync(path.join(dir, name), 'utf8'));
let failures = 0;
const check = (name, condition, extra) => {
  if (!condition) { failures += 1; console.log('✗ ' + name + (extra ? '  ' + extra : '')); }
};

const files = ['bank.json', 'analogous.json', 'topics.json', 'rules.json', 'ui_strings.json', 'mistakes.json', 'answer_vectors.json'];
const bank = load('bank.json'), analogous = load('analogous.json'), topics = load('topics.json');
const reference = load('rules.json'), ui = load('ui_strings.json'), mistakes = load('mistakes.json'), manifest = load('version.json');

check('no stale content files', JSON.stringify(fs.readdirSync(dir).sort()) === JSON.stringify(files.concat(['version.json']).sort()),
  fs.readdirSync(dir).join(','));
for (const name of files.concat(['version.json'])) {
  check('Windows copy identical: ' + name, fs.readFileSync(path.join(dir, name), 'utf8') === fs.readFileSync(path.join(windowsDir, name), 'utf8'));
}
for (const meta of [bank.meta, analogous.meta]) {
  check('bank subject/package', meta.subject === 'russian' && meta.package === 'by.ziv.ctrussian', JSON.stringify(meta).slice(0, 80));
}
check('topics subject', topics.subject === 'russian');
check('manifest identity', manifest.subject === 'russian' && manifest.package === 'by.ziv.ctrussian' && manifest.schema === 2 &&
  manifest.contentProtocol === 2 && manifest.tagPrefix === 'russian-v');
check('manifest never points at releases/latest', JSON.stringify(manifest).indexOf('latest') < 0);
check('manifest lists exactly the content files', JSON.stringify(Object.keys(manifest.files).sort()) === JSON.stringify(files.slice().sort()));
for (const name of files) {
  const data = fs.readFileSync(path.join(dir, name));
  const digest = crypto.createHash('sha256').update(data).digest('hex');
  check('manifest digest ' + name, manifest.files[name].sha256 === digest && manifest.files[name].bytes === data.length);
}

const spec = topics.specification;
check('2026 specification recorded', spec.tasks === 40 && spec.parts.A === 18 && spec.parts.B === 22 && spec.minutes === 120 &&
  /^https:\/\/rikc\.by\//.test(spec.url) && /^\d{4}-\d{2}-\d{2}$/.test(spec.checked));
check('exam length is 120 minutes, not the maths 180', topics.examMinutes === 120);
const quotas = {}; topics.blueprint.forEach((slot) => { quotas[slot.section] = (quotas[slot.section] || 0) + 1; });
check('blueprint quotas 13/9/2/3/1/2/4/3/3', JSON.stringify(quotas) === JSON.stringify(
  { orthography: 13, punctuation: 9, text: 3, lexis: 2, phonetics: 1, morphology: 4, syntax: 3, speech: 3, word: 2 }) ||
  Object.keys(quotas).length === 9 && quotas.orthography === 13 && quotas.punctuation === 9 && quotas.lexis === 2 &&
  quotas.speech === 3 && quotas.phonetics === 1 && quotas.word === 2 && quotas.morphology === 4 && quotas.syntax === 3 && quotas.text === 3);

const years = {};
bank.tasks.forEach((task) => { (years[task.year] = years[task.year] || []).push(task); });
check('six authored variants', JSON.stringify(Object.keys(years)) === JSON.stringify(['2021', '2022', '2023', '2024', '2025', '2026']));
Object.keys(years).forEach((year) => {
  const list = years[year];
  check(`variant ${year}: 18 A + 22 B`, list.filter((t) => t.part === 'A').length === 18 && list.filter((t) => t.part === 'B').length === 22);
  check(`variant ${year}: part A is several-of-five`, list.filter((t) => t.part === 'A').every((t) => t.check.type === 'multi' &&
    t.check.options === 5 && t.check.answer.length >= 2 && t.check.answer.length <= 4));
});

const lessons = topics.lessons, figures = topics.figures;
const ruleIds = Object.keys(topics.rules);
check('54 rule cards', ruleIds.length === 54 && Object.keys(lessons).length === 54);
const all = bank.tasks.concat(analogous.tasks);
const ids = new Set();
all.forEach((task) => {
  check('unique id ' + task.id, !ids.has(task.id)); ids.add(task.id);
  check('rule link ' + task.id, lessons[task.rule] && (task.rules || []).every((rule) => lessons[rule]));
  check('explicit contract ' + task.id, task.check.scoring === 'exact' && typeof task.check.order === 'string');
  check('Russian material is plain text ' + task.id, (task.text === undefined || typeof task.text === 'string') &&
    (task.items === undefined || task.items.every((item) => typeof item === 'string')));
  check('bilingual instruction ' + task.id, task.instruction.ru && task.instruction.en && task.solution.ru.length === task.solution.en.length);
  if (task.check.type === 'word') check('word policies ' + task.id, ['case', 'yo', 'hyphen'].every((key) => task.check[key]));
});
ruleIds.forEach((rule) => {
  check('≥3 analogs for ' + rule, analogous.tasks.filter((task) => task.rule === rule).length >= 3);
  const lesson = lessons[rule];
  check('card sections ' + rule, lesson.rule.ru.length && lesson.exceptions.ru.length && lesson.everyday.ru.length >= 2 &&
    lesson.correct.length && lesson.wrong.length && lesson.steps.ru.length >= 2 && lesson.sources.length);
  lesson.figures.forEach((fid) => check('figure ' + fid, figures[fid] && ['svg', 'table', 'tree'].indexOf(figures[fid].kind) >= 0));
  check('typical error for ' + rule, mistakes.errors[rule] && mistakes.errors[rule].ru && mistakes.errors[rule].en);
});
const reachable = new Set();
Object.values(topics.study).forEach((entry) => entry.lessons.forEach((id) => reachable.add(id)));
check('every card reachable from study', reachable.size === 54);
check('«Правила» lists every card', reference.groups.reduce((sum, group) => sum + group.items.length, 0) === 54);
Object.entries(ui.strings).forEach(([key, value]) => check('ui string ' + key, value.ru && value.en));
check('reference is called «Правила»', ui.strings.nav_rules.ru === 'Правила');
check('no maths reference left', !ui.strings.nav_formulas && !ui.strings.tool_calculator && !ui.strings.tool_graph);

console.log(failures ? `\n✗ ${failures} content schema failure(s)` :
  `✓ content schema: ${bank.tasks.length} variant tasks, ${analogous.tasks.length} analogs, ${ruleIds.length} rules, ` +
  `${Object.keys(figures).length} figures, ${Object.keys(ui.strings).length} interface strings`);
process.exit(failures ? 1 : 0);

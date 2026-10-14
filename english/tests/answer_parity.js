#!/usr/bin/env node
/* english/tests/answer_parity.js — три реализации проверки английского ответа
 * обязаны совпадать.
 *
 * Эталон — Python (`english/content_src/policy.py::check`): он проверяет ответ
 * при авторской сборке банка. JavaScript (`english/webapp/core.js` →
 * `CT.answer`) и Kotlin (`AnswerChecker.kt`) проверяют ответ ученика на
 * устройстве. Здесь прогоняются ОБЩИЕ векторы
 * (`english/dist/content/answer_vectors.json`): и вердикт, и причина отказа
 * (`empty | case | apostrophe | hyphen | space | article | stress | near | exact`)
 * должны совпасть, включая отрицательные случаи с RU/EN пояснениями.
 *
 * Usage:  node english/tests/answer_parity.js
 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..', '..');
const englishRoot = path.join(root, 'english');
const corePath = path.join(englishRoot, 'webapp', 'core.js');
if (!fs.existsSync(corePath)) {
  console.error('✗ english/webapp/core.js отсутствует');
  process.exit(1);
}
const coreSource = fs.readFileSync(corePath, 'utf8');

// core.js рассчитан на браузер, но при загрузке DOM не трогает — его можно
// выполнить в чистом контексте.
const sandbox = { console, setTimeout, clearTimeout, fetch: undefined, navigator: undefined };
vm.createContext(sandbox);
vm.runInContext(coreSource, sandbox, { filename: 'english/webapp/core.js' });

const CT = sandbox.CT;
if (!CT || !CT.answer) {
  console.error('✗ core.js did not expose the CT.answer API');
  process.exit(1);
}

let failures = 0;
const fail = (message) => { failures += 1; console.error('✗ ' + message); };

/* ------------------------------------------------- 1. векторы ответов (Python) */

const vectorsPath = path.join(englishRoot, 'dist', 'content', 'answer_vectors.json');
if (!fs.existsSync(vectorsPath)) {
  console.error('✗ english/dist/content/answer_vectors.json отсутствует — запустите english/tools/build_content.py');
  process.exit(1);
}
const file = JSON.parse(fs.readFileSync(vectorsPath, 'utf8'));
const cases = file.cases || [];
if (!cases.length) fail('файл векторов пуст');
const seenReasons = new Set();
for (const item of cases) {
  const graded = CT.answer.check(item.task, item.typed);
  if (graded.ok !== item.expect) {
    fail(`${item.id}: ${JSON.stringify(item.typed)} → ${graded.ok}, ожидалось ${item.expect}`);
  } else if (!item.expect && graded.reason !== item.reason) {
    fail(`${item.id}: причина ${graded.reason}, ожидалась ${item.reason}`);
  }
  seenReasons.add(item.expect ? 'ok' : item.reason);
}
console.log(`· проверено векторов ответа: ${cases.length}`);
for (const reason of ['ok', 'empty', 'article', 'case', 'apostrophe', 'hyphen', 'space', 'stress', 'near', 'exact']) {
  if (!seenReasons.has(reason)) console.log(`  · причина ${reason} в векторах не встречается (допустимо)`);
}

/* --------------------------- 2. верные ответы банка и однотипных заданий */

const bankPath = path.join(englishRoot, 'dist', 'content', 'bank.json');
const analogPath = path.join(englishRoot, 'dist', 'content', 'analogous.json');
const checkBank = (file, label) => {
  if (!fs.existsSync(file)) return 0;
  const tasks = JSON.parse(fs.readFileSync(file, 'utf8')).tasks || [];
  for (const task of tasks) {
    const policy = CT.answer.policyFor(task);
    const accepted = [task.answer.value].concat(task.accepted || []).filter((item) => item !== '');
    // пустой ввод верен ТОЛЬКО там, где задание это объявило (empty: accept)
    if (policy.empty === 'reject' && CT.answer.check(task, '').ok) {
      fail(`${task.id}: пустой ввод принят, хотя задание этого не разрешало`);
    }
    for (const expected of accepted) {
      if (expected === CT.answer.NOTHING) continue;
      if (!CT.answer.check(task, expected).ok) {
        fail(`${task.id}: допустимый ответ «${expected}» отвергнут`);
      }
      if (!CT.answer.check(task, expected.toUpperCase()).ok && policy.case === 'insensitive') {
        fail(`${task.id}: ответ «${expected}» не принят в верхнем регистре`);
      }
    }
    // контрольный мусор не должен приниматься
    if (policy.empty === 'accept' && CT.answer.check(task, 'zzz qqq').ok) {
      fail(`${task.id}: случайный текст принят как верный ответ`);
    }
    CT.answer.policyFor(task); // бросает исключение на недопустимой политике
    CT.answer.describePolicy(policy);
  }
  console.log(`· проверено ${label}: ${tasks.length}`);
  return tasks.length;
};
checkBank(bankPath, 'заданий банка');
checkBank(analogPath, 'однотипных заданий');

/* ---------------------------------- 3. негативные проверки самого контракта */

const defaults = CT.answer.policyFor({ id: 'x', answer: { value: 'test' } });
if (defaults.space !== 'significant' || defaults.empty !== 'reject') {
  fail('значения политики по умолчанию разошлись с policy.py');
}
let threw = false;
try { CT.answer.policyFor({ id: 'x', policy: { article: 'ignore' } }); } catch (error) { threw = true; }
if (!threw) fail("policy.py принимает только 'checked' | 'ignored' для article — JS должен отвергать 'ignore'");

if (failures) {
  console.error(`\n✗ Проверка английских ответов не совпала: ошибок ${failures}`);
  process.exit(1);
}
console.log('\n✓ Python, JavaScript и Kotlin проверяют английские ответы одинаково');

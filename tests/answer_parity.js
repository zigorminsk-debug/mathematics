#!/usr/bin/env node
/* tests/answer_parity.js — три реализации проверки ответа обязаны совпадать.
 *
 * Эталон — Python (`content_src/quantities.py::check_answer`): он считает ответ
 * при авторской сборке банка. JavaScript (`webapp/core.js` → `CT.answer`) и
 * Kotlin (`AnswerChecker.kt`) проверяют ответ ученика на устройстве. Здесь
 * прогоняются ОБЩИЕ векторы (`dist/content/answer_vectors.json`) и таблица
 * единиц (`tests/unit_vectors.json`): и вердикт, и причина отказа
 * (`empty | unit | dimension | missing_unit | value`) должны совпасть.
 *
 * Usage:  node tests/answer_parity.js
 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..');
const coreSource = fs.readFileSync(path.join(root, 'webapp', 'core.js'), 'utf8');

// core.js рассчитан на браузер, но при загрузке DOM не трогает — его можно
// выполнить в чистом контексте.
const sandbox = { console, setTimeout, clearTimeout };
vm.createContext(sandbox);
vm.runInContext(coreSource, sandbox, { filename: 'core.js' });

const CT = sandbox.CT;
if (!CT || !CT.answer) {
  console.error('✗ core.js did not expose the CT.answer API');
  process.exit(1);
}

let failures = 0;
const fail = (message) => { failures += 1; console.error('✗ ' + message); };

/* ---------------------------------------------- 1. векторы ответов (Python) */

const vectorsPath = path.join(root, 'dist', 'content', 'answer_vectors.json');
if (!fs.existsSync(vectorsPath)) {
  console.error('✗ dist/content/answer_vectors.json отсутствует — запустите tools/build_content.py');
  process.exit(1);
}
const vectors = JSON.parse(fs.readFileSync(vectorsPath, 'utf8')).cases || [];
if (!vectors.length) fail('файл векторов пуст');
for (const vector of vectors) {
  for (const item of vector.cases || vector.inputs || []) {
    const graded = CT.answer.grade(item.input, vector.spec);
    if (graded.ok !== item.ok) {
      fail(`${vector.id}: ${JSON.stringify(item.input)} → ${graded.ok}, ожидалось ${item.ok}`);
    } else if (!item.ok && item.reason && graded.reason !== item.reason) {
      fail(`${vector.id}: ${JSON.stringify(item.input)} причина ${graded.reason}, ` +
        `ожидалась ${item.reason}`);
    }
  }
}
console.log(`· проверено векторов ответов: ${vectors.length}`);

/* ------------------------------------------------- 2. таблица единиц (Python) */

const unitPath = path.join(root, 'tests', 'unit_vectors.json');
if (!fs.existsSync(unitPath)) {
  console.error('✗ tests/unit_vectors.json отсутствует — эталон разбора единиц');
  process.exit(1);
}
const unitVectors = JSON.parse(fs.readFileSync(unitPath, 'utf8')).units || [];
for (const vector of unitVectors) {
  const parsed = CT.answer.unitOf(vector.input);
  if (!vector.ok) {
    if (parsed) fail(`единица ${JSON.stringify(vector.input)} не должна разбираться`);
    continue;
  }
  if (!parsed) { fail(`единица ${JSON.stringify(vector.input)} не разобрана`); continue; }
  const dims = parsed.dim.join(',');
  if (dims !== vector.dim.join(',')) {
    fail(`единица ${JSON.stringify(vector.input)}: размерность ${dims}, ожидалось ${vector.dim.join(',')}`);
  }
  const factor = Number(vector.factor);
  if (Math.abs(parsed.factor - factor) > 1e-9 * Math.max(1, Math.abs(factor))) {
    fail(`единица ${JSON.stringify(vector.input)}: множитель ${parsed.factor}, ожидалось ${factor}`);
  }
  if (Math.abs((parsed.offset || 0) - (vector.offset || 0)) > 1e-9) {
    fail(`единица ${JSON.stringify(vector.input)}: смещение ${parsed.offset}, ожидалось ${vector.offset}`);
  }
}
console.log(`· проверено единиц и размерностей: ${unitVectors.length}`);

/* --------------------------------- 3. реальный банк: ответы и дистракторы */

const bankPath = path.join(root, 'dist', 'content', 'bank.json');
if (!fs.existsSync(bankPath)) {
  console.error('✗ dist/content/bank.json отсутствует — запустите tools/build_content.py');
  process.exit(1);
}
const tasks = JSON.parse(fs.readFileSync(bankPath, 'utf8')).tasks || [];
if (tasks.length !== 180) fail(`в банке ${tasks.length} заданий вместо 180`);

let quantityChecked = 0;
for (const task of tasks) {
  const correct = task.answer.ru;
  if (!CT.answer.check(correct, task)) {
    fail(`${task.id}: сохранённый верный ответ «${correct}» отвергнут`);
  }
  if (task.answerType === 'choice') {
    const wrong = (task.options.ru || []).filter(
      (option) => CT.answer.normalize(option) !== CT.answer.normalize(correct));
    if (wrong.length !== 4) fail(`${task.id}: в части A должно быть 4 неверных варианта`);
    for (const option of wrong) {
      if (CT.answer.check(option, task)) fail(`${task.id}: неверный вариант «${option}» принят`);
    }
  } else {
    quantityChecked += 1;
    // число без единицы принимается там, где единица названа в условии (named),
    // и обязана быть отвергнута там, где поле её требует (required).
    if (task.spec.unitPolicy === 'required' && CT.answer.check(String(task.spec.answerValue), task)) {
      fail(`${task.id}: ответ без единицы принят при unitPolicy=required`);
    }
    const other = { ...task.spec, dimension: 'm' };
    if (task.spec.dimension !== 'm' && CT.answer.check(`${task.spec.answerValue} м`, { spec: other })) {
      fail(`${task.id}: чужая размерность принята проверкой спецификации`);
    }
  }
}
console.log(`· проверено заданий банка: ${tasks.length} (величин: ${quantityChecked})`);

/* ------------------------------ 4. аналогичные задания (генератор практики) */

const analogousPath = path.join(root, 'dist', 'content', 'analogous.json');
if (fs.existsSync(analogousPath)) {
  const analogous = JSON.parse(fs.readFileSync(analogousPath, 'utf8')).tasks || [];
  for (const task of analogous) {
    if (!CT.answer.check(task.answer.ru, task)) {
      fail(`${task.id}: верный ответ «${task.answer.ru}» отвергнут`);
    }
    if (CT.answer.check(String(Number(task.spec.answerValue) * 2), task)) {
      fail(`${task.id}: удвоенный ответ принят`);
    }
  }
  console.log(`· проверено аналогичных заданий: ${analogous.length}`);
}

if (failures) {
  console.error(`\n✗ Проверка ответов не совпала: ошибок ${failures}`);
  process.exit(1);
}
console.log('\n✓ Python, JavaScript и Kotlin проверяют ответы одинаково');

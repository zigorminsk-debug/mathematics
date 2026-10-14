#!/usr/bin/env node
/* tests/answer_parity.js — the JavaScript checker (webapp/core.js) grades the
 * shared, hand-written vector corpus exactly like Python and Kotlin, and accepts
 * the canonical answer of every task in both banks.
 *
 * Usage: node tests/answer_parity.js   (after tools/build_content.py + sync_assets.py)
 */
'use strict';

const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const content = path.join(root, 'android', 'app', 'src', 'main', 'assets', 'webapp', 'content');
global.document = undefined;
eval(fs.readFileSync(path.join(root, 'webapp', 'core.js'), 'utf8'));
const A = globalThis.CT.answer;

let failures = 0;
const fail = (message) => { failures += 1; console.log('✗ ' + message); };

const vectors = JSON.parse(fs.readFileSync(path.join(content, 'answer_vectors.json'), 'utf8'));
const kotlinCopy = path.join(root, 'android', 'app', 'src', 'test', 'resources', 'answer_vectors.json');
if (fs.readFileSync(kotlinCopy, 'utf8') !== fs.readFileSync(path.join(content, 'answer_vectors.json'), 'utf8')) {
  fail('the Kotlin test resource differs from the shipped vector corpus (run tools/sync_assets.py)');
}
if (vectors.schema !== 2 || vectors.cases.length < 100) fail('unexpected vector corpus shape');
const kinds = new Set();
for (const vector of vectors.cases) {
  kinds.add(vector.check.type);
  const got = A.checkSpec(vector.user, vector.check);
  if (got !== vector.expect) fail(`${vector.id} ${JSON.stringify(vector.user)} → ${got}, expected ${vector.expect} (${vector.why})`);
}
for (const kind of ['multi', 'single', 'numbers', 'word', 'stress', 'match', 'integer']) {
  if (!kinds.has(kind)) fail('the corpus does not cover ' + kind);
}

function sample(spec) {
  if (spec.type === 'multi' || spec.type === 'numbers') return spec.answer.join(' ');
  if (spec.type === 'single' || spec.type === 'integer') return String(spec.answer);
  if (spec.type === 'word') return spec.answer;
  if (spec.type === 'stress') return spec.display;
  return spec.labels.map((label) => label + spec.answer[label]).join('');
}

let tasks = 0;
for (const file of ['bank.json', 'analogous.json']) {
  for (const task of JSON.parse(fs.readFileSync(path.join(content, file), 'utf8')).tasks) {
    tasks += 1;
    if (!A.check(sample(task.check), task)) fail(`${task.id}: the canonical answer is rejected by JS`);
    for (const alternative of task.check.accept || []) {
      if (!A.checkSpec(alternative, task.check)) fail(`${task.id}: a justified alternative is rejected`);
    }
    if (A.check('', task)) fail(`${task.id}: an empty answer is accepted`);
    if (task.check.type === 'multi') {
      const extra = [...new Set(task.check.answer.concat([1, 2, 3, 4, 5].filter((n) => task.check.answer.indexOf(n) < 0).slice(0, 1)))];
      if (A.checkSpec(extra.join(''), task.check)) fail(`${task.id}: an extra selection is accepted`);
    }
  }
}

console.log(failures ? `\n✗ ${failures} parity failure(s)` :
  `✓ ${vectors.cases.length} shared vectors and ${tasks} canonical task answers graded identically by JavaScript`);
process.exit(failures ? 1 : 0);

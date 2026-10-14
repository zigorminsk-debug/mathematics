#!/usr/bin/env node
/* tests/answer_parity.js — the JavaScript answer checker and the statistics
 * engine must agree with the Python reference implementation used while
 * authoring the bank.
 *
 * The vectors in dist/content/answer_vectors.json are produced by
 * tools/build_content.py (default_vectors); Android asserts the very same file
 * in AnswerCheckerTest.kt, so all three implementations stay in sync.
 *
 * Usage:  node tests/answer_parity.js
 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..');
const coreSource = fs.readFileSync(path.join(root, 'webapp', 'core.js'), 'utf8');

// core.js is written for browsers but touches no DOM at load time, so it can be
// evaluated in a bare VM context.
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

/* ---------------------------------------------------- answer-check tiers --- */

const vectorsPath = path.join(root, 'dist', 'content', 'answer_vectors.json');
if (!fs.existsSync(vectorsPath)) {
  console.error('✗ dist/content/answer_vectors.json is missing — run tools/build_content.py');
  process.exit(1);
}
const vectors = JSON.parse(fs.readFileSync(vectorsPath, 'utf8')).cases || [];
if (!vectors.length) fail('the vector file is empty');

vectors.forEach((vector, index) => {
  const task = { accept: vector.accept || [], answerType: vector.answerType || 'short' };
  const got = CT.answer.check(vector.user, task);
  if (got !== vector.expect) {
    fail(`#${index} "${vector.user}" vs ${JSON.stringify(vector.accept)}: ` +
      `expected ${vector.expect}, got ${got}`);
  }
});

/* Real bank items: the stored correct answer must be accepted as typed, and a
 * neighbouring option of a choice task must not be. */
const bankPath = path.join(root, 'dist', 'content', 'bank.json');
if (fs.existsSync(bankPath)) {
  const bank = JSON.parse(fs.readFileSync(bankPath, 'utf8')).tasks || [];
  bank.forEach((task) => {
    const correct = task.answer.ru;
    const taskForChecker = { accept: task.accept || [], answerType: task.answerType, answer: task.answer };
    if (!CT.answer.check(correct, taskForChecker)) {
      fail(`the stored answer of ${task.id} ("${correct}") is rejected by the checker`);
    }
    if (task.answerType === 'choice') {
      const wrong = (task.options.ru || []).find((option) => CT.answer.normalize(option) !== CT.answer.normalize(correct));
      if (wrong !== undefined && CT.answer.check(wrong, taskForChecker)) {
        fail(`${task.id}: the wrong option "${wrong}" is accepted`);
      }
    }
  });
  console.log(`· ${bank.length} bank items re-checked against the stored answers`);
}

/* ------------------------------------------------------ statistics engine --- */

const AN = CT.analytics;
const progress = AN.empty();
const task = { id: 'gen-lin-001', part: 'B', topic: 'equations', tags: [], year: 0 };
AN.record(progress, task, true, 30);
AN.record(progress, { id: 'gen-lin-002', part: 'B', topic: 'equations', tags: [], year: 0 }, false, 60);
AN.record(progress, { id: 'gen-lin-003', part: 'B', topic: 'equations', tags: [], year: 0 }, false, 60);
AN.record(progress, { id: 'ct-2024-a1', part: 'A', topic: 'numbers', tags: [], year: 2024 }, true, 20);

const totals = AN.totals(progress);
if (totals.tests !== 0 || totals.tasks !== 4 || totals.correct !== 2) {
  fail('analytics.totals produced unexpected numbers: ' + JSON.stringify(totals));
}
if (Math.abs(totals.accuracy - 0.5) > 1e-9) {
  fail('accuracy should be 0.5, got ' + totals.accuracy);
}
const topicStats = AN.topicStats(progress);
if (!topicStats.equations || topicStats.equations.total !== 3 || topicStats.equations.correct !== 1) {
  fail('topic statistics are wrong: ' + JSON.stringify(topicStats));
}
if (Math.abs(topicStats.equations.rate - 1 / 3) > 1e-9 || Math.abs(topicStats.numbers.rate - 1) > 1e-9) {
  fail('topic rates are wrong: ' + JSON.stringify(topicStats));
}
if (!AN.yearStats(progress)[2024] || AN.yearStats(progress)[2024].total !== 1) {
  fail('year statistics are wrong: ' + JSON.stringify(AN.yearStats(progress)));
}
if ((progress.daily[CT.util.today()] || 0) !== 4) {
  fail('the daily counter was not increased: ' + JSON.stringify(progress.daily));
}
if (progress.streak !== 1) fail('the streak was not started: ' + progress.streak);

const weak = AN.weakTopics(progress, 3);
if (!weak.length || weak[0].topic !== 'equations') {
  fail('weak topics are wrong: ' + JSON.stringify(weak));
}

const attempt = {
  id: 'x', title: 'Вариант 2024', seconds: 3600, year: 2024,
  results: [
    { taskId: 'ct-2024-a1', part: 'A', topic: 'numbers', correct: true, user: '1' },
    { taskId: 'ct-2024-a2', part: 'A', topic: 'expressions', correct: false, user: '5' },
    { taskId: 'ct-2024-b1', part: 'B', topic: 'equations', correct: true, user: '3' },
  ],
};
const summary = AN.attemptSummary(attempt);
if (summary.correct !== 2 || summary.total !== 3 || summary.mistakes.length !== 1) {
  fail('attempt summary is wrong: ' + JSON.stringify(summary));
}
if (summary.byPart.A.correct !== 1 || summary.byPart.B.total !== 1) {
  fail('per-part summary is wrong: ' + JSON.stringify(summary.byPart));
}
if (summary.grade !== 67) fail('the grade should be 67, got ' + summary.grade);

/* Calendar plumbing used by the streak counter. */
if (CT.util.daysBetween('2026-10-01', '2026-10-03') !== 2) fail('daysBetween is broken');
if (CT.util.today(new Date('2026-01-05T10:00:00')) !== '2026-01-05') fail('today() is broken');

if (failures) {
  console.error(`✗ ${failures} parity check(s) failed`);
  process.exit(1);
}
console.log(`✓ answer/analytics parity: ${vectors.length} vectors passed`);

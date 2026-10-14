#!/usr/bin/env node
/* tests/ui_smoke.js — end-to-end smoke test of the shared interface.
 *
 * Boots webapp/index.html in jsdom, feeds it the real bank from windows/web/content
 * (the copies produced by tools/sync_assets.py), and walks the main user journey:
 * language switch → variant → wrong answer → mistake breakdown → analogous task →
 * tools (calculator, formulas) → exam → results → statistics → contacts → settings.
 *
 * jsdom is an optional development dependency; when it is missing the test skips
 * itself instead of failing the build.  Install it with:
 *     npm install --no-save jsdom
 *
 * Usage:  node tests/ui_smoke.js
 */
'use strict';

let JSDOM, VirtualConsole;
try {
  ({ JSDOM, VirtualConsole } = require('jsdom'));
} catch (error) {
  console.log('· ui_smoke: jsdom is not installed — skipping (npm install --no-save jsdom)');
  process.exit(0);
}

const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const web = path.join(root, 'webapp');
const contentDir = path.join(root, 'windows', 'web', 'content');

if (!fs.existsSync(path.join(contentDir, 'bank.json'))) {
  console.error('✗ ui_smoke: windows/web/content is missing — run tools/sync_assets.py');
  process.exit(1);
}

let failures = 0;
const check = (name, condition, extra) => {
  console.log((condition ? '✓ ' : '✗ ') + name + (condition ? '' : '  ' + (extra || '')));
  if (!condition) failures += 1;
};
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const virtualConsole = new VirtualConsole();
virtualConsole.on('jsdomError', (error) => { console.log('✗ jsdom error:', error.message); failures += 1; });
virtualConsole.on('error', (message) => { console.log('✗ console error:', message); failures += 1; });

const html = fs.readFileSync(path.join(web, 'index.html'), 'utf8');
const dom = new JSDOM(html, {
  url: 'http://localhost/index.html',
  runScripts: 'outside-only',
  pretendToBeVisual: true,
  virtualConsole,
});
const { window } = dom;
const doc = window.document;

// jsdom has no canvas: give the charts a no-op 2d context and no scrolling.
window.HTMLCanvasElement.prototype.getContext = function () {
  return new Proxy({}, {
    get: () => () => ({
      setTransform() {}, clearRect() {}, fillRect() {}, strokeRect() {},
      beginPath() {}, moveTo() {}, lineTo() {}, arc() {}, stroke() {}, fill() {},
      fillText() {}, save() {}, restore() {}, measureText: () => ({ width: 10 }),
    }),
  });
};
window.scrollTo = () => {};
window.fetch = async (url) => {
  const file = path.join(contentDir, String(url).split('/').pop());
  if (!fs.existsSync(file)) return { ok: false, status: 404, json: async () => { throw new Error('404'); } };
  return { ok: true, status: 200, json: async () => JSON.parse(fs.readFileSync(file, 'utf8')) };
};

window.eval(fs.readFileSync(path.join(web, 'core.js'), 'utf8'));
window.eval(fs.readFileSync(path.join(web, 'app.js'), 'utf8'));

const text = () => (doc.getElementById('view') || {}).textContent || '';
const bodyText = () => doc.body.textContent || '';
const click = (node) => { node.dispatchEvent(new window.MouseEvent('click', { bubbles: true })); };
const buttonWith = (label) => Array.from(doc.querySelectorAll('button')).find((b) => b.textContent.trim() === label);

(async () => {
  for (let i = 0; i < 80 && !window.CT.content.bank.length; i++) await sleep(50);
  check('bank loaded into the interface', window.CT.content.bank.length === 180, String(window.CT.content.bank.length));
  check('analogous bank loaded', window.CT.content.analogous.length > 300, String(window.CT.content.analogous.length));
  check('formula sheet loaded', window.CT.content.formulas.length >= 5);
  check('bilingual error catalogue loaded', Object.keys(window.CT.content.mistakes.errors || {}).length >= 50);
  check('interface strings loaded', Object.keys(window.CT.i18n.strings || {}).length >= 100);

  await sleep(60);
  check('home screen rendered', /Репетитор ЦТ/.test(text()), text().slice(0, 60));

  // ---- язык / language toggle ------------------------------------------------
  click(doc.getElementById('lang-toggle'));
  await sleep(40);
  check('language switches to English', window.CT.store.settings.lang === 'en' && /Tests/.test(doc.getElementById('mainnav').textContent));
  check('interface strings follow the language', /Tasks solved|Tests/.test(text()) || /CT Maths Tutor/.test(doc.getElementById('brand-name').textContent),
    doc.getElementById('brand-name').textContent);
  click(doc.getElementById('lang-toggle'));
  await sleep(40);
  check('language switches back to Russian', window.CT.store.settings.lang === 'ru');

  // ---- вариант: тренировка и разбор ошибки -----------------------------------
  window.location.hash = '#/tests';
  await sleep(80);
  check('variant list rendered', /Вариант 2024/.test(text()), text().slice(0, 80));
  check('variant 2026 is offered', /Вариант 2026/.test(text()), text().slice(0, 120));
  const cardFor = (year) => Array.from(doc.querySelectorAll('.card'))
    .find((card) => card.querySelector('h3') && card.querySelector('h3').textContent.indexOf(String(year)) >= 0);
  const card2024 = cardFor(2026);
  check('each year has its card with exam and train buttons', !!card2024 && !!card2024.querySelector('button'));
  const trainBtn = Array.from(card2024.querySelectorAll('button')).find((b) => b.textContent.trim() === 'Тренировка');
  click(trainBtn);
  await sleep(80);
  check('train runner opened', /Задание 1 из 30/.test(text()), text().slice(0, 90));

  const session = window.CT.store.session;
  const task = window.CT.content.taskById(session.order[session.index]) || window.CT.content.bank[0];
  check('session has 30 tasks', session.order.length === 30, String(session.order.length));

  // отвечаем заведомо неверно
  if (task.answerType === 'choice') {
    const wrong = Array.from(doc.querySelectorAll('.option')).find((option) => {
      const value = option.querySelector('.option-value').textContent;
      return !window.CT.answer.check(value, task);
    });
    click(wrong);
  } else {
    const input = doc.querySelector('.answer-input');
    input.value = '0,000001';
    input.dispatchEvent(new window.Event('input', { bubbles: true }));
  }
  await sleep(40);
  click(buttonWith('Проверить'));
  await sleep(80);
  check('wrong answer is reported', /Пока неверно/.test(bodyText()), bodyText().slice(0, 120));
  check('mistake breakdown shown', /Типичная причина|Правильное решение|Верный ответ/.test(bodyText()));
  // при неверном ответе открывается тема, к которой относится задание
  const studyBlock = doc.querySelector('.study-topic');
  check('wrong answer opens the topic to study', !!studyBlock && /Изучить тему/.test(studyBlock.textContent)
    && studyBlock.getAttribute('data-topic') === task.topic,
    studyBlock ? studyBlock.textContent.slice(0, 80) : 'no .study-topic');
  check('the opened topic shows its formulas', !!studyBlock && studyBlock.querySelectorAll('.formula-row').length >= 1,
    studyBlock ? String(studyBlock.querySelectorAll('.formula-row').length) : '0');
  check('analogous task offered', doc.querySelectorAll('.analogous-item').length >= 1,
    String(doc.querySelectorAll('.analogous-item').length));

  const savedRunId = window.CT.store.session.id;
  const savedAnswer = window.CT.store.session.answers[task.id];
  click(Array.from(studyBlock.querySelectorAll('button')).find((b) => b.textContent === 'Открыть тему'));
  await sleep(50);
  check('the study link opens the full topic', window.location.hash === '#/study/' + task.topic);
  click(doc.getElementById('lang-toggle'));
  await sleep(20);
  check('study notes switch to English', /What to revise/.test(text()));
  click(doc.getElementById('lang-toggle'));
  await sleep(20);
  click(buttonWith('Вернуться к заданию'));
  await sleep(50);
  check('return from studying preserves the run and answer', window.CT.store.session.id === savedRunId
    && window.CT.store.session.answers[task.id] === savedAnswer && window.location.hash === '#/run');

  const analog = doc.querySelector('.analogous-item');
  if (analog) {
    const known = window.CT.content.analogous.find((item) => analog.textContent.indexOf(item.text.ru.slice(0, 24)) >= 0);
    check('the analogous task comes from the bank', !!known);
    if (known) {
      const input = analog.querySelector('.answer-input');
      const button = Array.from(analog.querySelectorAll('button')).find((b) => b.textContent === 'Проверить');
      input.value = 'incorrect';
      click(button);
      const analogStudy = analog.querySelector('.study-topic');
      check('a wrong analogous answer also opens its study topic', !!analogStudy
        && analogStudy.getAttribute('data-topic') === known.topic && !analogStudy.parentElement.classList.contains('hidden'));
      input.value = known.answer.ru;
      click(button);
      check('a correct analogous answer closes automatic remediation', analogStudy.parentElement.classList.contains('hidden'));
      await sleep(40);
      check('the analogous task accepts the stored answer', /Верно/.test(analog.textContent), analog.textContent.slice(0, 80));
    }
  }

  // ---- инструменты -----------------------------------------------------------
  const toolButtons = Array.from(doc.querySelectorAll('.tools-strip button')).map((b) => b.textContent.trim());
  check('tools are offered during the task', toolButtons.length >= 4, toolButtons.join(' | '));
  const calcTool = Array.from(doc.querySelectorAll('.tools-strip button')).find((b) => /Калькулятор/.test(b.textContent));
  click(calcTool);
  await sleep(60);
  const calcInput = doc.querySelector('.calc-display');
  if (calcInput) {
    calcInput.value = '2*(3+4)+√9';
    click(buttonWith('='));
    await sleep(30);
    const result = doc.querySelector('.calc-result');
    check('calculator evaluates roots and brackets', result && /17/.test(result.textContent), result && result.textContent);
  } else {
    check('calculator opens', false, 'no input found');
  }
  window.CT.closeModal();
  await sleep(20);

  const formulaTool = Array.from(doc.querySelectorAll('.tools-strip button')).find((b) => /Формулы/.test(b.textContent));
  click(formulaTool);
  await sleep(60);
  check('formula sheet opens over the task', doc.querySelectorAll('.formula-group').length >= 5,
    String(doc.querySelectorAll('.formula-group').length));
  const search = doc.querySelector('.sheet .answer-input');
  if (search) {
    search.value = 'Виета';
    search.dispatchEvent(new window.Event('input', { bubbles: true }));
    await sleep(40);
    check('formula search filters the list', /Виета/.test(doc.body.textContent));
  }
  window.CT.closeModal();
  await sleep(20);

  // ---- экзамен: завершаем сразу ----------------------------------------------
  window.location.hash = '#/exam';
  await sleep(60);
  const yearBtn = Array.from(doc.querySelectorAll('button')).find((b) => b.textContent.trim() === '2023');
  click(yearBtn);
  await sleep(80);
  const viewButtons = () => Array.from(doc.getElementById('view').querySelectorAll('button')).map((b) => b.textContent.trim());
  check('exam mode hides the check button', viewButtons().indexOf('Проверить') < 0, viewButtons().join(' | '));
  const finish = buttonWith('Завершить тест');
  check('finish button available', !!finish);
  click(finish);
  await sleep(40);
  const confirm = Array.from(doc.querySelectorAll('.sheet button')).pop();
  click(confirm);
  await sleep(120);
  check('results screen shown', /Результат/.test(text()), text().slice(0, 80));
  const progress = window.CT.store.progress;
  check('attempt stored', progress.attempts.length === 1, String(progress.attempts.length));
  const attempt = progress.attempts[0];
  check('attempt holds 30 graded results', attempt.results.length === 30);
  // 1 задание решено в тренировке + 30 в экзамене
  // 30 экзаменационных + 1 неверный ответ в тренировке + 2 проверки аналога
  check('statistics counters updated', progress.tasksDone === 33 && Object.keys(progress.byTopic).length > 4,
    'tasksDone=' + progress.tasksDone);
  check('daily activity matches the solved tasks',
    Object.values(progress.daily).reduce((a, b) => a + b, 0) === progress.tasksDone,
    JSON.stringify(progress.daily));
  check('topic statistics are filled', Object.keys(progress.byTopic).length >= 5, JSON.stringify(Object.keys(progress.byTopic)));

  // ---- разбор ошибок и закрепление -------------------------------------------
  const review = Array.from(doc.querySelectorAll('button')).find((b) => /Разобрать ошибки/.test(b.textContent));
  check('mistake review button offered', !!review);
  if (review) {
    click(review);
    await sleep(100);
    check('mistake screen shows the breakdown', /Разбор ошибок|Заданий с ошибками/.test(text()), text().slice(0, 80));
    const reinforce = Array.from(doc.querySelectorAll('button')).find((b) => /Закрепить/.test(b.textContent));
    check('reinforcement button offered', !!reinforce);
    if (reinforce) {
      click(reinforce);
      await sleep(100);
      check('reinforcement screen starts a set of analogous tasks',
        doc.querySelectorAll('.task-card').length >= 1, String(doc.querySelectorAll('.task-card').length));
    }
  }

  // ---- статистика -------------------------------------------------------------
  window.location.hash = '#/stats';
  await sleep(140);
  check('statistics screen rendered', /Статистика/.test(text()), text().slice(0, 80));
  check('topic statistics drawn as bars', doc.querySelectorAll('.bar-row').length >= 5,
    String(doc.querySelectorAll('.bar-row').length));
  check('attempt ledger shown', /Последние попытки/.test(text()), text().slice(0, 120));

  // ---- формулы и контакты ------------------------------------------------------
  window.location.hash = '#/formulas';
  await sleep(100);
  check('standalone formula sheet rendered', doc.querySelectorAll('.formula-group').length >= 5);

  window.location.hash = '#/about';
  await sleep(80);
  const contacts = Array.from(doc.querySelectorAll('a')).map((a) => a.getAttribute('href') || '');
  check('email is a clickable mailto link', contacts.some((href) => href.startsWith('mailto:ziv@csl.by')), contacts.join(' '));
  check('phone is a clickable tel link', contacts.includes('tel:+3753371412'));
  check('WhatsApp link present', contacts.some((href) => href.indexOf('https://wa.me/3753371412') === 0));
  check('developer name shown', /Захаревич Игорь|Zakharevich Igor/.test(text()));

  // ---- тренировка по теме и настройки -----------------------------------------
  window.location.hash = '#/practice/planimetry';
  await sleep(120);
  check('topic practice renders a task', !!doc.querySelector('.answer-input') || !!doc.querySelector('.option'));

  // ---- изучение темы -------------------------------------------------------
  window.location.hash = '#/study/planimetry';
  await sleep(100);
  check('study screen opens the topic', /Изучить тему/.test(text()) && doc.querySelectorAll('.formula-group').length >= 1,
    text().slice(0, 120));
  check('study screen has worked examples', doc.querySelectorAll('.study-example').length >= 1,
    String(doc.querySelectorAll('.study-example').length));

  window.location.hash = '#/settings';
  await sleep(80);
  check('settings screen rendered', /Настройки/.test(text()), text().slice(0, 80));
  check('theme control present', /Оформление|Theme/.test(text()));
  check('font size control present', /Размер шрифта|Font size/.test(text()), text().slice(0, 200));

  // ---- системная кнопка «назад» ------------------------------------------------
  const backHome = window.CT.onAndroidBack();
  check('hardware back leaves settings for home', backHome === null && window.location.hash === '#/home', String(backHome));
  const backExit = window.CT.onAndroidBack();
  check('hardware back exits only from home', backExit === 'exit', String(backExit));

  console.log(failures ? `\n✗ ${failures} interface check(s) failed` : '\n✓ interface smoke test passed');
  process.exit(failures ? 1 : 0);
})();

#!/usr/bin/env node
/* english/tests/ui_smoke.js — дымовые проверки английского интерфейса в jsdom.
 *
 * Повторяют то, что делает ученик, и падают, если экран перестал работать:
 * главная, вариант 2026 (40 заданий: 18 A + 22 B, таймер 120 минут), ответ на
 * задание части A, сохранение статистики, тренировка с разбором ошибки
 * (диагноз → правило → однотипные задания), справочник со схемой, статистика,
 * настройки и «О программе».
 *
 * Отдельно проверяется требование к языку: переключатель интерфейса RU/EN не
 * переводит сам проверяемый английский текст.
 *
 * Usage:  npm install --no-save jsdom && node english/tests/ui_smoke.js
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const englishRoot = path.join(__dirname, '..');
const contentDir = path.join(englishRoot, 'dist', 'content');
const html = fs.readFileSync(path.join(englishRoot, 'webapp', 'index.html'), 'utf8');

const dom = new JSDOM(html, { url: 'http://localhost/index.html', runScripts: 'outside-only', pretendToBeVisual: true });
const { window } = dom;

// Платформа-заглушка Windows: content/<name>.json отдаём из собранного банка.
window.fetch = (url) => {
  const target = String(url);
  const json = (value) => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(value),
    text: () => Promise.resolve(JSON.stringify(value)) });
  if (target.indexOf('content/') === 0) {
    const file = path.join(contentDir, target.replace('content/', '').replace('.json', '') + '.json');
    if (!fs.existsSync(file)) return Promise.resolve({ ok: false, status: 404 });
    return json(JSON.parse(fs.readFileSync(file, 'utf8')));
  }
  if (target === 'api/state') {
    return json({ app: { platform: 'windows', dataDir: 'C:/tmp', version: '2026.10.1' },
      content: { version: '2026.10.1' } });
  }
  if (target.indexOf('api/blob') === 0) return json(null);
  if (target === 'api/update') return json({ status: 'ok', version: '2026.10.1' });
  return json({ ok: true });
};

window.eval(fs.readFileSync(path.join(englishRoot, 'webapp', 'core.js'), 'utf8'));
window.eval(fs.readFileSync(path.join(englishRoot, 'webapp', 'app.js'), 'utf8'));

const $ = (selector) => window.document.querySelector(selector);
const $$ = (selector) => Array.prototype.slice.call(window.document.querySelectorAll(selector));
const click = (node) => node.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
const wait = () => new Promise((resolve) => setTimeout(resolve, 30));

let failures = 0;
const check = (condition, label, extra) => {
  if (!condition) { failures++; console.error('✗ ' + label + (extra ? ' — ' + extra : '')); }
  else console.log('· ' + label);
};
const show = (hash) => { window.location.hash = hash; window.CT.render(); };

(async () => {
  await window.CT.boot();
  await wait();
  check(!!$('.hero'), 'главная отрисована');
  check(document_title_ok(), 'заголовок называет предмет', window.document.title);
  function document_title_ok() { return /Английский/.test(window.document.title); }

  /* ---------------------------------------------------- reviewed source archive */
  window.CT.store.settings.autoAdvance = false;
  show('#/archives');
  check($$('.archive-card').length === 5, 'архив: пять отдельных исходных вариантов');
  check(/год издания независимо не подтверждён/.test($('#view').textContent), 'архив: оговорка о годе файла 2024 видна');
  const authoredIds = new Set(window.CT.content.variants().flatMap((v) => v.tasks.map((task) => task.id)));
  for (const source of window.CT.content.archiveVariants) {
    const count = source.parts.A + source.parts.B;
    show('#/archives');
    const card = $(`.archive-card[data-archive-id="${source.id}"]`);
    check(card.querySelector('.archive-source-link').getAttribute('href') === source.url, `${source.id}: ссылка на исходный файл видна в карточке`);
    check(!!card.querySelector('.source-citation'), `${source.id}: атрибуция видна в карточке`);
    click(card.querySelector('.primary')); await wait();
    let session = window.CT.store.session;
    check(session.archiveId === source.id && session.order.length === count,
      `${source.id}: исходный формат ${source.parts.A}+${source.parts.B} сохранён`);
    check(session.order.every((id) => !authoredIds.has(id)), `${source.id}: нет подмены авторскими заданиями`);
    check(!!$('.source-scan') && $('.source-scan').getAttribute('src').startsWith('data:image/jpeg;base64,'),
      `${source.id}: исходный скан встроен офлайн`);
    const first = window.CT.run.task();
    const citation = $('.task-card > .source-citation');
    check(!!citation && citation.querySelector('a').getAttribute('href') === source.url, `${source.id}: источник виден без раскрытия скана`);
    const openExternal = window.CT.bridge.openExternal;
    let openedSource = null; window.CT.bridge.openExternal = (url) => { openedSource = url; };
    citation.querySelector('a').click();
    check(openedSource === source.url, `${source.id}: источник открывается через системный браузер`);
    window.CT.bridge.openExternal = openExternal;
    check($('.task-text').textContent === first.conditionText && first.conditionText.length > 80, `${source.id}: условие доступно как текст без открытия скана`);
    check($$('.choice').every((node) => node.textContent.includes(first.optionLabels[node.getAttribute('data-option')])), `${source.id}: варианты ответа распознаны текстом`);
    check($$('.choice').map((node) => node.getAttribute('data-option')).join(',') === first.options.slice().sort().join(','), `${source.id}: исходные номера не выдают ключ порядком кнопок`);
    const imageBefore = $('.source-scan').getAttribute('src');
    const pageSelect = $('.source-page-select');
    pageSelect.selectedIndex = pageSelect.options.length - 1;
    pageSelect.dispatchEvent(new window.Event('change', {bubbles:true}));
    check($('.source-scan').getAttribute('src') !== imageBefore, `${source.id}: доступны остальные страницы контекста`);
    $('.source-prev').click();
    const zoom = $('.source-zoom input'); zoom.value = '200'; zoom.dispatchEvent(new window.Event('input'));
    check($('.source-scan').style.width === '200%', `${source.id}: масштабирование скана работает`);
    window.CT.i18n.setLang('en'); window.CT.render();
    check(window.CT.run.task().text === first.text, `${source.id}: язык интерфейса не изменяет условие`);
    const good = $$('.choice').find((node) => node.getAttribute('data-option') === first.answer.value);
    click(good); await wait();
    check(!$('.choice.correct,.choice.wrong,.q-cell.ok,.q-cell.bad'), `${source.id}: цвет не выдаёт правильность экзаменационного ответа`);
    check(!!$('.banner.info') && !$('.diagnosis') && !$('.rule-card'), `${source.id}: ключ и разбор не раскрываются на экзамене`);
    window.CT.i18n.setLang('ru');
    show('#/archives');
    click($(`.archive-card[data-archive-id="${source.id}"] .btn:not(.primary)`)); await wait();
    const bad = $$('.choice').find((node) => node.getAttribute('data-option') !== window.CT.run.task().answer.value);
    click(bad); await wait();
    check(!!$('.diagnosis') && !!$('.rule-card') && !!$('.analogous-box'),
      `${source.id}: ошибка ведёт к диагностике/правилу/однотипным упражнениям`);
    window.CT.run.moveTo(source.parts.A);
    const written = window.CT.run.task();
    $('.answer-input').value = written.answer.value; click($('.btn.primary')); await wait();
    check(window.CT.store.session.results[source.parts.A].correct === true, `${source.id}: ответ B1 принят`);
    window.CT.run.finish(); await wait();
    const attempt = window.CT.store.progress.attempts.at(-1);
    check(attempt.archiveId === source.id, `${source.id}: история сохраняет идентичность источника`);
  }
  show('#/home');

  /* ---------------------------------------------------- вариант целиком */
  const variant = window.CT.content.variants()[0];
  check(variant && variant.tasks.length === 40, 'вариант 2026 содержит 40 заданий',
    variant ? String(variant.tasks.length) : 'нет');
  check(variant.partA === 18 && variant.partB === 22, 'структура варианта 18 A + 22 B',
    variant.partA + ' A + ' + variant.partB + ' B');
  check(window.CT.content.meta.minutes === 120, 'на вариант отведено 120 минут',
    String(window.CT.content.meta.minutes));
  check(window.CT.content.plannedYears().length === 0, 'все годы выпущены, не помечены как готовящиеся');

  const variants = window.CT.content.variants();
  check(variants.map((v) => v.year).join(',') === '2026,2025,2024,2023,2022,2021',
    'все шесть годов доступны в порядке от нового к старому');
  for (const v of variants) {
    show('#/tests');
    check($$('#view .card').filter((node) => /^202[1-6]$/.test(node.querySelector('h3').textContent)).length === 6, 'экран содержит шесть готовых наборов');
    check(/40/.test($('#view .muted').textContent) && !/521/.test($('#view .muted').textContent),
      'описание варианта показывает 40, а не размер всего банка');
    const card = $$('#view .card').find((node) => node.querySelector('h3').textContent === String(v.year));
    check(!!card, `есть карточка ${v.year}`);
    click(card.querySelector('.btn.primary'));
    await wait();
    const session = window.CT.store.session;
    check(session.year === v.year && session.order.length === 40, `экзамен ${v.year}: свой год и 40 заданий`);
    check(session.order.every((id) => window.CT.content.taskById(id).year === v.year),
      `экзамен ${v.year}: нет заданий соседних годов`);
    check(!!$('#run-clock') && session.limit === 7200, `экзамен ${v.year}: таймер на 120 минут`);
    show('#/tests');
    const trainCard = $$('#view .card').find((node) => node.querySelector('h3').textContent === String(v.year));
    click(trainCard.querySelector('.btn:not(.primary)'));
    await wait();
    check(window.CT.store.session.year === v.year && window.CT.store.session.mode === 'train',
      `тренировка ${v.year}: выбран правильный набор`);
    const current = window.CT.run.task();
    click($$('.choice').find((node) => node.textContent.indexOf(current.answer.value) < 0));
    await wait();
    check(!!$('.diagnosis') && !!$('.rule-card') && !!$('.analogous-box'),
      `тренировка ${v.year}: ошибка ведёт к разбору, правилу и однотипным заданиям`);
    if (v.year < 2026) {
      for (const number of [1, 9, 19]) {
        window.CT.run.moveTo(18 + number - 1);
        const written = window.CT.run.task();
        check(written.part === 'B' && written.n === number, `тренировка ${v.year}: открывается B${number}`);
        $('.answer-input').value = written.answer.value;
        click($('.btn.primary'));
        await wait();
        check(window.CT.store.session.results[18 + number - 1].correct === true,
          `тренировка ${v.year}: ввод правильного ответа B${number} работает`);
      }
    }
  }
  show('#/tests');
  check($$('#view .card').filter((node) => /^202[1-6]$/.test(node.querySelector('h3').textContent)).length === 6, 'экран вариантов открылся');
  click($$('#view .btn.primary')[0]);
  await wait();
  check(window.location.hash === '#/run', 'вариант запущен', window.location.hash);
  check(!!$('#run-clock'), 'таймер варианта виден');
  check(/осталось/i.test($('#run-clock').textContent), 'таймер показывает остаток времени');

  const task = window.CT.run.task();
  check(!!task && task.part === 'A', 'первое задание — из части A', task && task.id);
  if (task.type === 'choice') {
    const right = $$('.choice').filter((node) => node.textContent.indexOf(task.answer.value) >= 0)[0];
    check(!!right, 'вариант с верным ответом есть на экране');
    click(right);
  } else {
    $('.answer-input').value = task.answer.value;
    click($('.btn.primary'));
  }
  await wait();
  // В варианте целиком правильность не раскрывается до завершения.
  check(!!$('.banner.info'), 'ответ на задание варианта записан');
  check(!$('.policy-note') && !$('.diagnosis'), 'в варианте разбор не подсказывает ответ');
  check(window.CT.store.progress.tasksDone >= 1, 'статистика учла задание',
    String(window.CT.store.progress.tasksDone));
  check(!!window.CT.store.progress.byTopic[task.topic], 'тема учтена в статистике');
  const result = window.CT.store.session.results[0];
  check(result && result.correct === true && result.part === 'A', 'ответ записан в прогон вместе с частью');

  /* ------------------------------------------------ тренировка и разбор */
  show('#/practice');
  check($$('#view .card').length >= 10, 'в тренировке перечислены темы',
    String($$('#view .card').length));
  click($$('#view .btn.primary')[0]);
  await wait();
  const practice = window.CT.run.task();
  if (practice.type === 'choice') {
    click($$('.choice').filter((node) => node.textContent.indexOf(practice.answer.value) < 0)[0]);
  } else {
    $('.answer-input').value = 'zzz';
    click($('.btn.primary'));
  }
  await wait();
  check(!!$('.banner.bad'), 'неверный ответ отмечен');
  check(!!$('.policy-note'), 'показано, что именно проверяется в задании');
  check(!!$('.diagnosis'), 'показан диагноз типичной ошибки');
  check(!!$('.rule-card'), 'открылась карточка правила');
  check(!!$('.analogous-box'), 'предложены однотипные задания');
  check(/Ожидалось/.test($('#view').textContent), 'показан ожидаемый ответ');

  /* --------------------------------------- перевод ответа не переводится */
  const before = window.CT.content.bank.slice(0, 5).map((item) => item.text);
  window.CT.i18n.setLang('en');
  window.CT.render();
  const after = window.CT.content.bank.slice(0, 5).map((item) => item.text);
  check(before.join('|') === after.join('|'), 'английский текст заданий не переводится');
  check(/Topics|Practice|Rules/i.test(window.document.body.textContent), 'интерфейс переключился на английский');
  window.CT.i18n.setLang('ru');
  window.CT.render();

  /* --------------------------------------------------- справочник и схема */
  show('#/study');
  check($$('.rule-card').length >= 13, 'в справочнике есть карточки правил',
    String($$('.rule-card').length));
  const lesson = Object.keys(window.CT.content.lessons)[0];
  show('#/study/' + lesson);
  check(!!$('.diagram-svg'), 'нарисована схема урока');
  check($$('.diagram-svg .diagram-node').length >= 2, 'у схемы есть узлы');
  check($$('.diagram-svg .diagram-edge').length >= 1, 'у схемы есть связи');
  show('#/study');
  const search = $('.search');
  if (search) {
    search.value = 'артикл';
    search.dispatchEvent(new window.Event('input', { bubbles: true }));
    check($$('.rule-card').length >= 1, 'поиск по справочнику находит правило');
  }

  /* ---------------------------------------------------- статистика, экраны */
  for (const hash of ['#/home', '#/stats', '#/mistakes', '#/settings', '#/about']) {
    show(hash);
    const view = $('#view');
    check(view.children.length > 0 && view.textContent.indexOf('undefined') < 0, 'экран ' + hash);
  }
  show('#/about');
  check(/Английский/.test($('#view').textContent), 'в «О программе» назван предмет');
  check(/не являются официальными|не официальные/i.test($('#view').textContent),
    'есть оговорка, что задания не РИКЗ');

  /* ---------------------------------------------------------- завершение */
  show('#/run');
  click($$('#view .btn.ghost').pop());
  await wait();
  const confirmYes = $$('.confirm .btn.primary')[0];
  if (confirmYes) { click(confirmYes); await wait(); }
  check(window.location.hash === '#/result' || window.location.hash === '#/run',
    'вариант можно завершить', window.location.hash);
  if (window.location.hash === '#/result') {
    check(/Верных ответов/.test($('#view').textContent), 'результат показывает счёт');
  }

  /* ----------------------- malformed downloaded archive metadata fails closed */
  const readContent = window.CT.bridge.getContent;
  const goodBank = JSON.parse(fs.readFileSync(path.join(contentDir, 'bank.json'), 'utf8'));
  const goodTopics = JSON.parse(fs.readFileSync(path.join(contentDir, 'topics.json'), 'utf8'));
  const cases = [
    ['missing task in source variant', (bank, topics) => { topics.archiveVariants[0].taskIds[0] = 'missing-task'; }],
    ['missing context page', (bank, topics) => { topics.archiveVariants[0].pageIds.push('missing-page'); }],
    ['remote image instead of offline JPEG', (bank) => { Object.values(bank.sourcePages)[0].data = 'https://invalid.example/page.jpg'; }],
    ['wrong source page owner', (bank) => { Object.values(bank.sourcePages)[0].sourceId = 'another-source'; }],
    ['missing transcribed option', (bank) => { delete bank.tasks.find((task) => task.source === 'archive').optionLabels['1']; }],
    ['missing transcribed condition', (bank) => { bank.tasks.find((task) => task.source === 'archive').conditionText = ''; }],
  ];
  for (const [label, mutate] of cases) {
    const bank = JSON.parse(JSON.stringify(goodBank));
    const topics = JSON.parse(JSON.stringify(goodTopics));
    mutate(bank, topics);
    window.CT.bridge.getContent = (name) => name === 'bank' ? Promise.resolve(bank) : name === 'topics' ? Promise.resolve(topics) : readContent.call(window.CT.bridge, name);
    let rejected = false;
    try { await window.CT.content.load(); } catch (_) { rejected = true; }
    check(rejected, 'повреждённый архив отвергнут: ' + label);
  }
  window.CT.bridge.getContent = readContent;
  await window.CT.content.load();

  if (failures) { console.error('\n✗ ошибок: ' + failures); process.exit(1); }
  console.log('\n✓ интерфейс английского тренажёра проходит дымовой тест');
})().catch((error) => { console.error(error); process.exit(1); });

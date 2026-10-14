#!/usr/bin/env node
/* english/tests/content_schema.js — структурные проверки английского банка и
 * надписей интерфейса.
 *
 *  * у каждого задания обязательного варианта есть часть A или B, номер, тема,
 *    инструкция на двух языках, ответ и разбор;
 *  * варианты: ровно 18 заданий части A и 22 части B, 120 минут — формат
 *    РИКЗ-2025/ДРТ (источник и дата указаны в docs/subjects/ENGLISH.md);
 *  * авторские задания не выдаются за официальные (в текстах нет «РИКЗ/РИКЗ»,
 *    манифест помечен `authored`);
 *  * каждый ключ надписей, который использует интерфейс (`english/webapp/*.js`),
 *    существует — опечатка не оставит на экране сырое имя ключа;
 *  * задания не перепутаны с другими предметами: в контенте нет чужих слов
 *    («математика», «физика», «атом», «размерность») и чужих идентификаторов;
 *  * схемы (topics.figures) укладываются в свои размеры, а уроки ссылаются на
 *    существующие схемы и правила.
 *
 * Usage: node english/tests/content_schema.js
 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..', '..');
const englishRoot = path.join(root, 'english');
const contentDir = path.join(englishRoot, 'dist', 'content');
const read = (name) => JSON.parse(fs.readFileSync(path.join(contentDir, name + '.json'), 'utf8'));

let failures = 0;
const fail = (message) => { failures++; console.error('✗ ' + message); };
const bilingual = (value) => value && typeof value.ru === 'string' && value.ru.trim() &&
  typeof value.en === 'string' && value.en.trim();

/* ------------------------------------------------------------ манифест */

const version = read('version');
if (!version.contentVersion || !/^[0-9]+(\.[0-9]+)*$/.test(version.contentVersion)) {
  fail('version.json: нет числовой версии контента');
}
if (version.subject !== 'english') fail('version.json: subject должен быть english');
if (version.package !== 'by.ziv.ctenglish') fail('version.json: чужой пакет');
if (version.app !== 'CTEnglishTutor') fail('version.json: чужое имя приложения');
if (version.schema !== 1) fail('version.json: неизвестная схема контента');
const disclosure = typeof version.disclosure === 'string' ? version.disclosure
  : Object.values(version.disclosure || {}).join(' ');
if (!disclosure.trim()) fail('version.json: нет оговорки об авторстве');
if (!/не являются официальн|не официальн|not official|authored/i.test(disclosure)) {
  fail('version.json: оговорка не сообщает, что задания авторские, а не РИКЗ');
}

/* ------------------------------------------------------- банк и аналоги */

const bank = read('bank');
const analogous = read('analogous');
const taskFields = ['id', 'topic', 'type', 'instruction', 'text', 'answer', 'accepted', 'policy', 'tags', 'rule'];
const checkTask = (task, where) => {
  taskFields.forEach((field) => {
    if (!(field in task)) fail(`${where}: ${task.id || '?'} — нет поля «${field}»`);
  });
  if (!bilingual(task.instruction)) fail(`${where}: ${task.id} — инструкция не на двух языках`);
  if (typeof task.text !== 'string' || !task.text.trim()) fail(`${where}: ${task.id} — пустое условие`);
  if (!task.answer || typeof task.answer.value !== 'string' || !task.answer.value.trim()) {
    fail(`${where}: ${task.id} — нет ответа`);
  }
  if (!Array.isArray(task.accepted) || !task.accepted.length) fail(`${where}: ${task.id} — нет списка допустимых ответов`);
  if (!Array.isArray(task.tags) || !task.tags.length) fail(`${where}: ${task.id} — нет тега ошибки (нужен разбор)`);
  if (task.type === 'choice') {
    if (!Array.isArray(task.options) || task.options.length !== 5) {
      fail(`${where}: ${task.id} — в части с выбором должно быть ровно пять вариантов`);
    } else {
      if (new Set(task.options).size !== task.options.length) fail(`${where}: ${task.id} — варианты повторяются`);
      if (task.options[0] !== task.answer.value) fail(`${where}: ${task.id} — первый вариант не совпадает с ответом`);
    }
  }
  // проверяемый английский текст не должен содержать русского: переводится
  // интерфейс, а не задание.  Исключение — задания «переведите фрагмент»: там
  // русский фрагмент и есть условие, а ответ по-прежнему английский.
  if (task.type !== 'translate' && /[А-Яа-яЁё]/.test(task.text)) {
    fail(`${where}: ${task.id} — русские буквы в проверяемом тексте`);
  }
  if (task.type === 'translate' && !/[А-Яа-яЁё]/.test(task.text)) {
    fail(`${where}: ${task.id} — задание на перевод без русского фрагмента`);
  }
};

const ids = new Set();
[...bank.tasks, ...analogous.tasks].forEach((task) => {
  if (ids.has(task.id)) fail(`id повторяется: ${task.id}`);
  ids.add(task.id);
});
bank.tasks.forEach((task) => checkTask(task, 'bank'));
analogous.tasks.forEach((task) => checkTask(task, 'analogous'));

const variant = bank.tasks.filter((task) => task.year === 2026);
const partA = variant.filter((task) => task.part === 'A');
const partB = variant.filter((task) => task.part === 'B');
if (partA.length !== 18) fail(`вариант 2026: часть A — ${partA.length} заданий, ожидается 18`);
if (partB.length !== 22) fail(`вариант 2026: часть B — ${partB.length} заданий, ожидается 22`);
if (partA.length + partB.length !== 40) fail('вариант 2026: всего должно быть 40 заданий');

/* ------------------------------------------------------ темы, правила, уроки */

const topics = read('topics');
if (!topics.topics || !Object.keys(topics.topics).length) fail('topics.json: нет тем');
if (!topics.order || topics.order.length !== Object.keys(topics.topics).length) {
  fail('topics.json: порядок тем не совпадает со списком тем');
}
if (!topics.counts || !Object.keys(topics.counts).length) fail('topics.json: нет счётчиков по темам');
if (topics.minutes !== undefined && topics.minutes !== 120) fail('topics.json: время варианта должно быть 120 минут');

Object.entries(topics.topics).forEach(([key, entry]) => {
  if (!bilingual(entry)) fail(`topics.json: тема ${key} без названия на двух языках`);
  if (!topics.counts[key]) fail(`topics.json: у темы ${key} нет заданий`);
});
if (!topics.periods || !Array.isArray(topics.periods.released) || !topics.periods.released.includes(2026)) {
  fail('topics.json: 2026 год должен быть помечен как выпущенный');
}
if (!topics.periods.planned || !topics.periods.planned.length) {
  fail('topics.json: нет списка готовящихся вариантов — обещание «пока в работе» потеряется');
}

const rules = read('rules');
if (!Array.isArray(rules.groups) || !rules.groups.length) fail('rules.json: нет разделов справочника');
const ruleIds = new Set();
rules.groups.forEach((group) => {
  // у задания может стоять и ключ раздела (tenses, word_formation), и ключ карточки
  ruleIds.add(group.id);
  if (group.rule) ruleIds.add(group.rule);
  if (!bilingual(group.title)) fail(`rules.json: раздел ${group.id} без названия`);
  if (!Array.isArray(group.items) || !group.items.length) fail(`rules.json: раздел ${group.id} пуст`);
  group.items.forEach((item) => {
    ruleIds.add(item.id);
    if (!bilingual(item.title) || !bilingual(item.formulation)) {
      fail(`rules.json: карточка ${item.id} без формулировки на двух языках`);
    }
    if (!bilingual(item.everyday)) fail(`rules.json: карточка ${item.id} без бытового объяснения`);
  });
});
if (ruleIds.size < 13) fail(`rules.json: карточек ${ruleIds.size}, ожидается не меньше 13 (по темам)`);

const lessons = topics.lessons || {};
const lessonIds = Object.keys(lessons);
if (lessonIds.length < 13) fail(`topics.json: уроков ${lessonIds.length}, ожидается не меньше 13 (по темам)`);
lessonIds.forEach((key) => {
  const lesson = lessons[key];
  if (lesson.id !== key) fail(`topics.json: урок ${key} хранится под чужим ключом ${lesson.id}`);
  if (!bilingual(lesson.title) || !bilingual(lesson.summary)) fail(`урок ${key}: нет названия или краткого содержания`);
  if (!Array.isArray(lesson.sections) || !lesson.sections.length) fail(`урок ${key}: нет разбора`);
  lesson.sections.forEach((section, index) => {
    if (section.kind === 'steps') {
      if (!Array.isArray(section.ru) || !Array.isArray(section.en)) {
        fail(`урок ${key}: шаг ${index} без разбора на двух языках`);
      }
    } else if (!bilingual(section)) {
      fail(`урок ${key}: шаг ${index} без текста на двух языках`);
    }
  });
  if (lesson.figure && !(topics.figures || {})[lesson.figure]) {
    fail(`урок ${key}: схема ${lesson.figure} не существует`);
  }
  if (lesson.rule && !ruleIds.has(lesson.rule) && !rules.groups.some((group) => group.rule === lesson.rule)) {
    fail(`урок ${key}: правило ${lesson.rule} не найдено в справочнике`);
  }
});

/* ------------------------------------------------------------------ схемы */

Object.entries(topics.figures || {}).forEach(([key, figure]) => {
  if (figure.id !== key) fail(`схема ${key}: идентификатор ${figure.id} не совпадает с ключом`);
  if (!['tree', 'timeline', 'flow'].includes(figure.kind)) fail(`схема ${key}: неизвестный вид ${figure.kind}`);
  if (!bilingual(figure.title) || !bilingual(figure.caption)) fail(`схема ${key}: нет подписи на двух языках`);
  if (!Array.isArray(figure.nodes) || figure.nodes.length < 2) fail(`схема ${key}: нужно минимум два узла`);
  if (!Array.isArray(figure.edges) || !figure.edges.length) fail(`схема ${key}: нет связей`);
  const nodes = new Map();
  figure.nodes.forEach((node) => {
    nodes.set(node.id, node);
    if (!bilingual(node.label)) fail(`схема ${key}: узел ${node.id} без подписи на двух языках`);
    if (node.x < 0 || node.y < 0 || node.x + node.w > figure.width || node.y + node.h > figure.height) {
      fail(`схема ${key}: узел ${node.id} выходит за границы`);
    }
  });
  figure.edges.forEach((edge) => {
    if (!nodes.has(edge.from) || !nodes.has(edge.to)) fail(`схема ${key}: связь ведёт в несуществующий узел`);
    if (edge.label && !bilingual(edge.label)) fail(`схема ${key}: подпись связи без перевода`);
  });
});

/* ------------------------------------------------------ типичные ошибки */

const mistakes = read('mistakes');
const errorTags = Object.keys(mistakes.errors || {});
if (errorTags.length < 60) fail(`mistakes.json: диагнозов ${errorTags.length}, ожидается не меньше 60`);
if (!Array.isArray(mistakes.checklist) || mistakes.checklist.length < 3) fail('mistakes.json: нет памятки перед проверкой');
[...bank.tasks, ...analogous.tasks].forEach((task) => {
  task.tags.forEach((tag) => {
    if (!mistakes.errors[tag]) fail(`${task.id}: тег «${tag}» не описан в mistakes.json`);
  });
  if (task.rule && !ruleIds.has(task.rule)) {
    fail(`${task.id}: правило «${task.rule}» отсутствует в справочнике`);
  }
});

/* ------------------------------------------- надписи и чужие предметы */

const strings = read('ui_strings').strings || {};
const usedKeys = new Set();
const scanDirectory = path.join(englishRoot, 'webapp');
fs.readdirSync(scanDirectory).forEach((name) => {
  if (!name.endsWith('.js')) return;
  const source = fs.readFileSync(path.join(scanDirectory, name), 'utf8');
  for (const match of source.matchAll(/\bt\(\s*'([a-z0-9_]+)'/g)) usedKeys.add(match[1]);
});
const missing = [...usedKeys].filter((key) => !(key in strings));
if (missing.length) fail('в ui_strings.json нет надписей, которые просит интерфейс: ' + missing.join(', '));

Object.entries(strings).forEach(([key, value]) => {
  if (!bilingual(value)) fail(`ui_strings.json: надпись ${key} есть не на двух языках`);
  const placeholders = (lang) => ((value[lang].match(/%s/g) || []).length);
  if (placeholders('ru') !== placeholders('en')) fail(`ui_strings.json: ${key}: разное число подстановок %s`);
});
if (!strings.app_name || strings.app_name.ru.indexOf('Английский') < 0) {
  fail('ui_strings.json: app_name не называет предмет (английский язык)');
}
if (!strings.disclaimer || !/не официальн/i.test(strings.disclaimer.ru)) {
  fail('ui_strings.json: нет оговорки «не официальные задания РИКЗ»');
}

const FOREIGN = ['математик', 'mathemat', 'by.ziv.ctmaths', 'ctmathstutor', 'физик', 'physics',
  'by.ziv.ctphysics', 'ctphysicstutor', 'репетитор цт: русский'];
// адрес репозитория содержит слово «mathematics» — он не про предмет приложения
const REPO_URL = /https?:\/\/[^\s"']+/g;
const stripUrls = (text) => text.replace(REPO_URL, '<url>');
const foreignTexts = [stripUrls(JSON.stringify(bank.meta)), JSON.stringify(topics.tools),
  JSON.stringify(topics.types), JSON.stringify(topics.instructions)];
Object.entries(strings).forEach(([key, value]) => foreignTexts.push(key + ' ' + value.ru));
const foreign = FOREIGN.filter((word) => foreignTexts.join('\n').toLowerCase().includes(word));
if (foreign.length) fail('чужой предмет в оформлении: ' + foreign.join(', '));

/* ------------------------------------------------- проверка ответов (JS) */

const sandbox = { console, setTimeout, clearTimeout };
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(englishRoot, 'webapp', 'core.js'), 'utf8'), sandbox,
  { filename: 'english/webapp/core.js' });
if (!sandbox.CT || !sandbox.CT.answer) fail('core.js не предоставляет CT.answer');
else {
  const CT = sandbox.CT;
  [...bank.tasks, ...analogous.tasks].forEach((task) => {
    const graded = CT.answer.check(task, task.answer.value);
    if (!graded.ok) fail(`${task.id}: верный ответ «${task.answer.value}» отвергнут интерфейсом`);
    if (task.policy && task.policy.empty !== 'accept' && CT.answer.check(task, '').ok) {
      fail(`${task.id}: пустой ответ принят, хотя задание этого не разрешало`);
    }
  });
}

if (failures) {
  console.error(`\n✗ Схема английского контента нарушена: ошибок ${failures}`);
  process.exit(1);
}
console.log('✓ английский контент: 40 заданий варианта (18 A + 22 B), правила, уроки, схемы и надписи согласованы');

/* app.js — screens of the CT maths tutor.
 *
 * Screens: home, variant list, task runner (practice / exam / endless practice),
 * results, mistake analysis with analogous tasks, statistics, formula sheet,
 * settings, about.  All rendering is plain DOM work so the same file runs in the
 * Android WebView and in the Windows browser shell.
 */
(function () {
  'use strict';

  const U = CT.util, I = CT.i18n, C = CT.content, S = CT.store, B = CT.bridge, A = CT.answer;
  const AN = CT.analytics, M = CT.math, CH = CT.charts;
  const t = (...args) => I.t(...args);
  const view = () => document.getElementById('view');

  /* ------------------------------------------------------------- helpers -- */

  const OPTION_LETTERS = { ru: ['А', 'Б', 'В', 'Г', 'Д'], en: ['A', 'B', 'C', 'D', 'E'] };

  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach((k) => {
      if (k === 'class') node.className = attrs[k];
      else if (k === 'html') node.innerHTML = attrs[k];
      else if (k === 'text') node.textContent = attrs[k];
      else if (k.slice(0, 2) === 'on') node.addEventListener(k.slice(2), attrs[k]);
      else node.setAttribute(k, attrs[k]);
    });
    (children || []).forEach((c) => node.appendChild(c));
    return node;
  }

  function h(html) { const d = document.createElement('div'); d.innerHTML = html; return d.firstElementChild; }
  const esc = U.escape;

  function taskText(task) { return I.pick(task.text); }
  function taskOptions(task) {
    if (!task.options) return [];
    const list = task.options[I.lang] || task.options.ru || [];
    return list;
  }
  function correctIndex(task) {
    const options = taskOptions(task);
    for (let i = 0; i < options.length; i++) if (A.normalize(options[i]) === A.normalize(task.answer[I.lang] || task.answer.ru)) return i;
    return -1;
  }
  function correctAnswerText(task) { return task.answer[I.lang] || task.answer.ru; }
  function topicTitle(key) { return C.topicTitle(key); }
  function rate(value) { return Math.round((value || 0) * 100); }
  function lang() { return I.lang; }

  function modal(html, opts) {
    const box = document.getElementById('modal-box');
    box.innerHTML = html;
    box.className = 'modal-box ' + ((opts && opts.wide) ? 'wide' : '');
    document.getElementById('modal').classList.remove('hidden');
    const close = box.querySelector('[data-close]');
    if (close) close.addEventListener('click', closeModal);
    return box;
  }
  function closeModal() {
    document.getElementById('modal').classList.add('hidden');
    document.getElementById('modal-box').innerHTML = '';
  }
  CT.closeModal = closeModal;

  function sheet(title, bodyNode, footer) {
    const box = modal(`<div class="sheet">
      <div class="sheet-head"><strong>${esc(title)}</strong>
      <button class="icon-btn" data-close>✕</button></div>
      <div class="sheet-body"></div>
      <div class="sheet-foot"></div></div>`, { wide: true });
    box.querySelector('.sheet-body').appendChild(bodyNode);
    if (footer) box.querySelector('.sheet-foot').appendChild(footer);
    return box;
  }

  /* ------------------------------------------------------- error analysis - */

  function typicalErrors(task) {
    const catalogue = (C.mistakes && C.mistakes.errors) || {};
    const out = [];
    (task.tags || []).forEach((tag) => {
      if (catalogue[tag]) {
        const text = I.pick(catalogue[tag]);
        if (out.indexOf(text) < 0) out.push(text);
      }
    });
    if (!out.length && C.mistakes && C.mistakes.default) out.push(I.pick(C.mistakes.default));
    return out;
  }

  function analysisBlock(task, userAnswer, opts) {
    const options = { showAnalogous: true, ...(opts || {}) };
    const node = el('div', { class: 'analysis' });
    const correct = correctAnswerText(task);
    const isCorrect = A.check(userAnswer, task);
    node.appendChild(h(`<div class="analysis-row ${isCorrect ? 'good' : 'bad'}">
        <div><span class="label">${esc(t('your_answer_fmt', ' '))}</span>
             <strong>${esc(userAnswer || t('no_answer'))}</strong></div>
        <div><span class="label">${esc(t('correct_answer_fmt', ' '))}</span>
             <strong>${esc(correct)}</strong></div>
      </div>`));

    const errors = typicalErrors(task);
    if (errors.length) {
      node.appendChild(h(`<h4>${esc(t('why_wrong'))}</h4>`));
      const ul = el('ul', { class: 'errors' });
      errors.forEach((e) => ul.appendChild(el('li', { text: e })));
      node.appendChild(ul);
    }

    node.appendChild(h(`<h4>${esc(t('correct_solution'))}</h4>`));
    const steps = I.pickList(task.solution) || [];
    const isRussian = lang() === 'ru';
    const otherLang = isRussian ? 'en' : 'ru';
    const list = el('ol', { class: 'steps' });
    steps.forEach((step) => list.appendChild(el('li', { text: step })));
    node.appendChild(list);

    if (S.settings.showEnglishSolutions) {
      const otherSteps = (task.solution && task.solution[otherLang]) || [];
      if (otherSteps.length) {
        node.appendChild(h(`<h4 class="muted-h">${esc(otherLang === 'en' ? 'English solution' : 'Решение (русский)')}</h4>`));
        const other = el('ol', { class: 'steps muted' });
        otherSteps.forEach((step) => other.appendChild(el('li', { text: step })));
        node.appendChild(other);
      }
    }

    const checklist = (C.mistakes && C.mistakes.checklist) || [];
    if (checklist.length) {
      const details = el('details', { class: 'checklist' });
      details.appendChild(el('summary', { text: t('keyboard_help') === 'keyboard_help' ? '' : '' }));
      details.querySelector('summary').textContent = isRussian ? 'Как проверить себя' : 'How to self-check';
      const ul = el('ul', {});
      checklist.forEach((item) => ul.appendChild(el('li', { text: I.pick(item) })));
      details.appendChild(ul);
      node.appendChild(details);
    }

    if (options.showAnalogous) {
      const analogous = C.analogousFor(task, 2);
      if (analogous.length) {
        node.appendChild(h(`<h4>${esc(t('analogous_title'))}</h4>`));
        node.appendChild(h(`<p class="muted">${esc(t('analogous_intro'))}</p>`));
        analogous.forEach((item, i) => node.appendChild(analogousBlock(item, i + 1)));
      }
    }
    return node;
  }

  /** One analogous task: statement + answer box + revealable solution. */
  function analogousBlock(task, index) {
    const wrap = el('div', { class: 'analogous' });
    wrap.appendChild(h(`<div class="analogous-head">${esc(t('analogous_task_fmt', index))} ·
        <span class="muted">${esc(topicTitle(task.topic))}</span></div>`));
    wrap.appendChild(h(`<div class="task-text">${esc(taskText(task))}</div>`));
    const row = el('div', { class: 'answer-row' });
    const input = el('input', { type: 'text', class: 'answer-input', placeholder: t('answer_placeholder'),
      inputmode: 'text', autocapitalize: 'off', autocorrect: 'off' });
    const feedback = el('div', { class: 'feedback' });
    const check = el('button', { class: 'btn', text: t('check_answer') });
    const show = el('button', { class: 'btn ghost', text: t('show_solution') });
    row.appendChild(input); row.appendChild(check); row.appendChild(show);
    wrap.appendChild(row);
    wrap.appendChild(feedback);
    const solution = el('div', { class: 'solution hidden' });
    const steps = el('ol', { class: 'steps' });
    (I.pickList(task.solution) || []).forEach((s) => steps.appendChild(el('li', { text: s })));
    solution.appendChild(steps);
    wrap.appendChild(solution);
    check.addEventListener('click', () => {
      if (A.check(input.value, task)) {
        feedback.className = 'feedback good';
        feedback.textContent = t('answer_correct');
        S.progress.daily[U.today()] = (S.progress.daily[U.today()] || 0) + 1;
        S.saveProgress();
      } else {
        feedback.className = 'feedback bad';
        feedback.textContent = t('answer_incorrect');
        solution.classList.remove('hidden');
      }
    });
    show.addEventListener('click', () => solution.classList.toggle('hidden'));
    return wrap;
  }

  /* ------------------------------------------------------------- home ----- */

  function screenHome() {
    const totals = AN.totals(S.progress);
    const root = el('section', { class: 'screen' });
    root.appendChild(h(`<div class="hero">
        <h1>${esc(t('app_name'))}</h1>
        <p class="muted">${esc(t('app_tagline'))}</p>
        <div class="hero-actions">
          <button class="btn primary" data-go="#/tests">${esc(t('nav_tests'))}</button>
          <button class="btn" data-go="#/exam">${esc(t('nav_exam'))}</button>
          <button class="btn" data-go="#/practice">${esc(t('train_mode'))}</button>
        </div>
      </div>`));

    if (S.session && !S.session.finished) {
      const run = S.session;
      root.appendChild(h(`<div class="card accent">
          <div><strong>${esc(t('in_progress'))}</strong>
            <div class="muted">${esc(runTitle(run))} · ${esc(t('answered_fmt', Object.keys(run.answers || {}).length, (run.order || []).length))}</div></div>
          <button class="btn primary" data-go="#/test">${esc(t('continue_test'))}</button>
        </div>`));
    }

    const weak = AN.weakTopics(S.progress, 3);
    root.appendChild(h(`<div class="grid cards">
        ${statCard(t('tests_taken'), String(totals.tests))}
        ${statCard(t('tasks_solved'), String(totals.solved))}
        ${statCard(t('accuracy'), totals.solved ? rate(totals.rate) + '%' : '—')}
        ${statCard(t('streak_days_fmt', S.progress.streak.current || 0), '🔥')}
      </div>`));

    if (weak.length) {
      const card = el('div', { class: 'card' });
      card.appendChild(h(`<h3>${esc(t('recommended_topics'))}</h3>`));
      weak.forEach((w) => {
        card.appendChild(h(`<div class="rowline">
            <span>${esc(topicTitle(w.topic))}</span>
            <span class="muted">${rate(w.rate)}% · ${esc(t('answered_fmt', w.correct, w.seen))}</span>
            <button class="btn small" data-go="#/practice/${encodeURIComponent(w.topic)}">${esc(t('train_mode'))}</button>
          </div>`));
      });
      root.appendChild(card);
    } else {
      root.appendChild(h(`<div class="card muted">${esc(t('no_data_yet'))}</div>`));
    }

    root.appendChild(contentVersionCard());
    return root;
  }

  function statCard(label, value) {
    return `<div class="card stat"><div class="stat-value">${esc(value)}</div>
      <div class="stat-label">${esc(label)}</div></div>`;
  }

  function contentVersionCard() {
    const version = (C.meta && C.meta.version) || (S.content && S.content.version) || '—';
    return h(`<div class="card">
        <div class="rowline"><span>${esc(t('content_version_fmt', version))}</span>
          <button class="btn small" data-go="#/update">${esc(t('check_updates'))}</button></div>
        <p class="muted small">${esc(t('update_source_note'))}</p>
      </div>`);
  }

  function runTitle(run) {
    if (!run) return '';
    if (run.mode === 'practice') return t('train_mode') + (run.topic ? ' · ' + topicTitle(run.topic) : '');
    if (run.mode === 'exam') return t('exam_mode') + (run.year ? ' · ' + run.year : '');
    return run.year ? t('test_year_fmt', run.year) : t('parts_mix');
  }

  /* ------------------------------------------------------------ tests ----- */

  function screenTests() {
    const root = el('section', { class: 'screen' });
    root.appendChild(h(`<h1>${esc(t('tests_title'))}</h1><p class="muted">${esc(t('tests_subtitle'))}</p>`));
    const list = el('div', { class: 'grid cards' });
    C.years().forEach((year) => {
      const count = C.byYear(year).length;
      const best = AN.bestForTest(S.progress, 'year-' + year);
      list.appendChild(h(`<div class="card test-card">
          <h3>${esc(t('test_year_fmt', year))}</h3>
          <p class="muted small">${esc(t('tests_subtitle'))}</p>
          <p class="muted small">${count} ✓</p>
          <div class="rowline">
            <button class="btn primary" data-start="year-${year}|train">${esc(t('start'))}</button>
            <button class="btn" data-start="year-${year}|exam">${esc(t('nav_exam'))}</button>
          </div>
          ${best ? `<p class="muted small">${esc(t('progress'))}: ${rate(best.rate)}%</p>` : ''}
        </div>`));
    });
    list.appendChild(h(`<div class="card test-card">
        <h3>${esc(t('parts_mix'))}</h3>
        <p class="muted small">${esc(t('tests_subtitle'))}</p>
        <div class="rowline">
          <button class="btn primary" data-start="mixed|train">${esc(t('start'))}</button>
          <button class="btn" data-start="mixed|exam">${esc(t('nav_exam'))}</button>
        </div>
      </div>`));
    root.appendChild(list);
    return root;
  }

  function startTest(testId, mode) {
    let tasks;
    let year = null;
    if (testId === 'mixed') {
      const pool = U.shuffle(C.bank.slice(), Date.now() % 100000);
      tasks = pickBalanced(pool, 30);
    } else {
      year = parseInt(testId.replace('year-', ''), 10);
      tasks = C.byYear(year);
    }
    const order = tasks.map((task) => task.id);
    S.session = {
      testId, mode, year, order, index: 0, answers: {}, flagged: [],
      startedAt: new Date().toISOString(), elapsedMs: 0, finished: false, checked: {},
    };
    S.saveSession();
    B.keepScreenOn(true);
    location.hash = '#/test';
  }

  /** Mixed variant keeps the CT structure: 18 choice + 12 short-answer tasks. */
  function pickBalanced(pool, total) {
    const a = pool.filter((x) => x.part === 'A').slice(0, total - 12);
    const b = pool.filter((x) => x.part === 'B').slice(0, 12);
    const result = a.concat(b);
    for (let i = result.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      const tmp = result[i]; result[i] = result[j]; result[j] = tmp;
    }
    return result;
  }

  function screenExam() {
    const root = el('section', { class: 'screen' });
    root.appendChild(h(`<h1>${esc(t('exam_mode'))}</h1>`));
    root.appendChild(h(`<div class="card"><h3>${esc(t('exam_rules_title'))}</h3>
      <p>${esc(t('exam_rules'))}</p><p class="muted">${esc(t('exam_instructions'))}</p></div>`));
    const list = el('div', { class: 'grid cards' });
    C.years().forEach((year) => {
      list.appendChild(h(`<div class="card"><h3>${esc(t('test_year_fmt', year))}</h3>
        <button class="btn primary" data-start="year-${year}|exam">${esc(t('exam_start'))}</button></div>`));
    });
    list.appendChild(h(`<div class="card"><h3>${esc(t('parts_mix'))}</h3>
      <button class="btn primary" data-start="mixed|exam">${esc(t('exam_start'))}</button></div>`));
    root.appendChild(list);
    return root;
  }

  /* --------------------------------------------------- task runner ------- */

  let timerHandle = null;

  function currentSession() { return S.session; }

  function sessionTasks(run) {
    return (run.order || []).map((id) => C.taskById(id)).filter(Boolean);
  }

  function screenTest() {
    const run = currentSession();
    if (!run) { location.hash = '#/tests'; return el('div'); }
    const tasks = sessionTasks(run);
    if (!tasks.length) { location.hash = '#/tests'; return el('div'); }
    run.index = Math.min(Math.max(run.index || 0, 0), tasks.length - 1);
    const task = tasks[run.index];
    const root = el('section', { class: 'screen test-screen' });

    /* ---- header: counter, timer, tools ---- */
    const head = el('div', { class: 'test-head' });
    head.appendChild(h(`<div class="counter">${esc(t('task_counter_fmt', run.index + 1, tasks.length))}
        <span class="muted small">· ${esc(runTitle(run))}</span></div>`));
    const right = el('div', { class: 'test-head-right' });
    if (run.mode === 'exam') {
      const limitMs = (S.settings.examMinutes || 180) * 60000;
      const spent = elapsed(run);
      const left = Math.max(0, limitMs - spent);
      right.appendChild(h(`<div class="timer" id="timer">${esc(t('time_left_fmt', U.fmtDuration(left)))}</div>`));
    }
    const toolsBtn = el('button', { class: 'icon-btn', title: t('tools_title'), text: '🧰' });
    toolsBtn.addEventListener('click', () => openTools(task));
    right.appendChild(toolsBtn);
    const pause = el('button', { class: 'icon-btn', title: t('pause'), text: '⏸' });
    pause.addEventListener('click', () => { location.hash = '#/tests'; });
    right.appendChild(pause);
    head.appendChild(right);
    root.appendChild(head);

    /* ---- progress bar ---- */
    const answered = Object.keys(run.answers || {}).length;
    root.appendChild(h(`<div class="progress"><div class="progress-bar" style="width:${Math.round(100 * answered / tasks.length)}%"></div></div>
      <div class="muted small">${esc(t('answered_fmt', answered, tasks.length))}</div>`));

    /* ---- task ---- */
    const card = el('div', { class: 'card task-card' });
    card.appendChild(h(`<div class="task-meta">
        <span class="pill">${esc(task.part === 'A' ? t('part_a') : t('part_b'))}</span>
        <span class="pill muted">${esc(topicTitle(task.topic))}</span>
        ${task.year ? `<span class="pill muted">${esc(task.year)}</span>` : ''}
      </div>`));
    card.appendChild(h(`<div class="task-text">${esc(taskText(task))}</div>`));

    const stored = run.answers[task.id];
    if (task.answerType === 'choice') {
      const options = taskOptions(task);
      const box = el('div', { class: 'options' });
      options.forEach((opt, i) => {
        const letter = OPTION_LETTERS[lang()][i] || String(i + 1);
        const selected = stored !== undefined && A.normalize(stored) === A.normalize(opt);
        const btn = h(`<button class="option ${selected ? 'selected' : ''}" data-option="${i}">
            <span class="letter">${letter}</span><span class="value">${esc(opt)}</span></button>`);
        btn.addEventListener('click', () => {
          run.answers[task.id] = opt;
          delete run.checked[task.id];
          S.saveSession();
          render();
        });
        box.appendChild(btn);
      });
      card.appendChild(box);
    } else {
      const input = el('input', {
        type: 'text', class: 'answer-input big', value: stored || '',
        placeholder: t('answer_placeholder'), inputmode: 'text', autocapitalize: 'off', autocorrect: 'off',
      });
      input.addEventListener('input', () => {
        run.answers[task.id] = input.value;
        if (run.mode !== 'exam') delete run.checked[task.id];
        S.saveSession();
      });
      const row = el('div', { class: 'answer-row' });
      row.appendChild(input);
      card.appendChild(row);
      card.appendChild(h(`<p class="muted small">${esc(t('short_hint'))} · ${esc(t('keyboard_help'))}</p>`));
    }

    /* ---- feedback / checking ---- */
    const feedback = el('div', { class: 'feedback' });
    if (run.mode !== 'exam') {
      const actions = el('div', { class: 'rowline wrap' });
      const checkBtn = el('button', { class: 'btn primary', text: t('check_answer') });
      checkBtn.addEventListener('click', () => {
        const answer = run.answers[task.id];
        const ok = A.check(answer, task);
        run.checked[task.id] = ok;
        S.saveSession();
        if (!ok) {
          const box = el('div', { class: 'card analysis-card' });
          box.appendChild(h(`<h3>${esc(t('error_analysis'))}</h3>`));
          box.appendChild(analysisBlock(task, answer || '', { showAnalogous: true }));
          feedback.className = 'feedback';
          feedback.innerHTML = '';
          feedback.appendChild(h(`<div class="banner bad">${esc(t('answer_incorrect'))}</div>`));
          feedback.appendChild(box);
          if (S.settings.autoAdvance === false) feedback.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
          feedback.innerHTML = '';
          feedback.appendChild(h(`<div class="banner good">${esc(t('answer_correct'))}</div>`));
          if (S.settings.autoAdvance) setTimeout(nextTask, 600);
        }
      });
      actions.appendChild(checkBtn);

      const hintBtn = el('button', { class: 'btn ghost', text: t('show_hint') });
      hintBtn.addEventListener('click', () => showHint(task));
      actions.appendChild(hintBtn);

      const formulaBtn = el('button', { class: 'btn ghost', text: t('tool_formula_sheet') });
      formulaBtn.addEventListener('click', () => openTools(task, 'formulas'));
      actions.appendChild(formulaBtn);
      card.appendChild(actions);
      card.appendChild(feedback);
    } else {
      card.appendChild(h(`<p class="muted small">${esc(t('exam_instructions'))}</p>`));
    }

    if (run.flagged && run.flagged.indexOf(task.id) >= 0) {
      card.appendChild(h(`<div class="pill flagged">${esc(t('mark_review'))}</div>`));
    }
    root.appendChild(card);

    /* ---- navigation ---- */
    const nav = el('div', { class: 'test-nav' });
    const prev = el('button', { class: 'btn', text: '‹ ' + t('previous') });
    prev.disabled = run.index === 0;
    prev.addEventListener('click', () => { run.index--; S.saveSession(); render(); });
    const flag = el('button', { class: 'btn ghost', text: '⚑ ' + t('mark_review') });
    flag.addEventListener('click', () => {
      run.flagged = run.flagged || [];
      const at = run.flagged.indexOf(task.id);
      if (at >= 0) run.flagged.splice(at, 1); else run.flagged.push(task.id);
      S.saveSession(); render();
    });
    const next = el('button', { class: 'btn', text: t('next') + ' ›' });
    next.disabled = run.index >= tasks.length - 1;
    next.addEventListener('click', () => { run.index++; S.saveSession(); render(); });
    nav.appendChild(prev); nav.appendChild(flag); nav.appendChild(next);
    const grid = el('button', { class: 'btn ghost', text: '☰' });
    grid.addEventListener('click', () => openTaskGrid(run, tasks));
    nav.appendChild(grid);
    const finish = el('button', { class: 'btn primary', text: t('submit_test') });
    finish.addEventListener('click', confirmFinish);
    nav.appendChild(finish);
    root.appendChild(nav);

    startTimer(run);
    return root;
  }

  function nextTask() {
    const run = currentSession();
    if (!run) return;
    const tasks = sessionTasks(run);
    if (run.index < tasks.length - 1) { run.index++; S.saveSession(); render(); }
  }

  function elapsed(run) {
    const started = new Date(run.startedAt).getTime();
    const base = run.baseElapsedMs || 0;
    return base + (Date.now() - started);
  }

  function startTimer(run) {
    if (timerHandle) { clearInterval(timerHandle); timerHandle = null; }
    if (run.mode !== 'exam') return;
    const limitMs = (S.settings.examMinutes || 180) * 60000;
    timerHandle = setInterval(() => {
      const node = document.getElementById('timer');
      if (!node) return;
      const left = Math.max(0, limitMs - elapsed(run));
      node.textContent = t('time_left_fmt', U.fmtDuration(left));
      node.classList.toggle('danger', left < 5 * 60000);
      if (left <= 0) { clearInterval(timerHandle); finishTest(); }
    }, 1000);
  }

  function openTaskGrid(run, tasks) {
    const body = el('div', { class: 'grid task-grid' });
    tasks.forEach((task, i) => {
      const answered = run.answers[task.id] !== undefined;
      const flagged = (run.flagged || []).indexOf(task.id) >= 0;
      const cls = 'grid-cell' + (answered ? ' answered' : '') + (flagged ? ' flagged' : '')
        + (i === run.index ? ' current' : '');
      const cell = el('button', { class: cls, text: String(i + 1) });
      cell.addEventListener('click', () => { run.index = i; S.saveSession(); closeModal(); render(); });
      body.appendChild(cell);
    });
    sheet(t('tasks_solved'), body, null);
  }

  function showHint(task) {
    const hints = I.pickList(task.hints) || [];
    const box = el('div', {});
    if (!hints.length) box.appendChild(h(`<p>${esc(t('empty_state'))}</p>`));
    hints.forEach((hint, i) => box.appendChild(h(`<div class="hint-card"><strong>${esc(t('hint_fmt', i + 1))}</strong>
        <p>${esc(hint)}</p></div>`)));
    sheet(t('hint'), box, null);
  }

  function confirmFinish() {
    const run = currentSession();
    if (!run) return;
    const tasks = sessionTasks(run);
    const unanswered = tasks.filter((task) => run.answers[task.id] === undefined).length;
    const body = el('div', {});
    body.appendChild(h(`<p>${esc(t('submit_confirm'))}</p>`));
    if (unanswered) body.appendChild(h(`<p class="banner bad">${esc(t('unanswered_warning_fmt', unanswered))}</p>`));
    const footer = el('div', { class: 'rowline' });
    const cancel = el('button', { class: 'btn ghost', text: t('cancel') });
    cancel.addEventListener('click', closeModal);
    const ok = el('button', { class: 'btn primary', text: t('finish') });
    ok.addEventListener('click', () => { closeModal(); finishTest(); });
    footer.appendChild(cancel); footer.appendChild(ok);
    sheet(t('submit_test'), body, footer);
  }

  function finishTest() {
    const run = currentSession();
    if (!run) return;
    const tasks = sessionTasks(run);
    const timeMs = elapsed(run);
    const results = tasks.map((task) => {
      const user = run.answers[task.id];
      const correct = A.check(user, task);
      return {
        taskId: task.id,
        topic: task.topic,
        tags: task.tags || [],
        year: task.year || 0,
        correct,
        user: user === undefined ? '' : user,
        answer: correctAnswerText(task),
      };
    });
    const attempt = {
      id: 'a' + Date.now(),
      testId: run.testId,
      title: runTitle(run),
      mode: run.mode,
      year: run.year || 0,
      date: U.today(),
      finishedAt: new Date().toISOString(),
      timeMs,
      results,
    };
    S.progress.attempts.push(attempt);
    S.progress = AN.recordAttempt(S.progress, attempt);
    S.session = null;
    B.keepScreenOn(false);
    if (timerHandle) { clearInterval(timerHandle); timerHandle = null; }
    S.flush();
    location.hash = '#/results/' + (S.progress.attempts.length - 1);
  }

  /* ---------------------------------------------------------- results ----- */

  function screenResults(index) {
    const attempt = S.progress.attempts[index];
    if (!attempt) return el('div', { class: 'screen', text: t('empty_state') });
    const total = attempt.results.length;
    const correct = attempt.results.filter((r) => r.correct).length;
    const share = total ? correct / total : 0;
    const grade = share >= 0.85 ? t('grade_high') : share >= 0.7 ? t('grade_good')
      : share >= 0.5 ? t('grade_mid') : t('grade_low');
    const root = el('section', { class: 'screen' });
    root.appendChild(h(`<h1>${esc(t('results_title'))}</h1>
      <p class="muted">${esc(attempt.title)} · ${esc(U.fmtDate(attempt.finishedAt))}</p>`));
    root.appendChild(h(`<div class="grid cards">
        ${statCard(t('results_title'), rate(share) + '%')}
        ${statCard(t('points_fmt', ' ').trim() || 'Баллы', String(correct))}
        ${statCard(t('time_spent_fmt', ' ').trim(), U.fmtDuration(attempt.timeMs))}
        ${statCard(t('grade_fmt', ' ').trim(), grade)}
      </div>`));
    root.appendChild(h(`<div class="card"><h3>${esc(t('by_topic'))}</h3>
        <canvas id="topic-chart"></canvas></div>`));
    const mistakes = attempt.results.filter((r) => !r.correct);
    const actions = el('div', { class: 'rowline wrap' });
    if (mistakes.length) {
      const review = el('button', { class: 'btn primary', text: t('review_mistakes') });
      review.addEventListener('click', () => { location.hash = '#/review/' + index; });
      actions.appendChild(review);
    }
    const again = el('button', { class: 'btn', text: t('retry') });
    again.addEventListener('click', () => {
      const testId = attempt.testId.indexOf('practice') === 0 ? 'mixed' : attempt.testId;
      startTest(testId, attempt.mode);
    });
    actions.appendChild(again);
    const list = el('button', { class: 'btn ghost', text: t('back_to_tests') });
    list.addEventListener('click', () => { location.hash = '#/tests'; });
    actions.appendChild(list);
    root.appendChild(actions);

    const taskList = el('div', { class: 'card' });
    taskList.appendChild(h(`<h3>${esc(t('mistakes_title'))}</h3>`));
    attempt.results.forEach((r) => {
      const task = C.taskById(r.taskId);
      const row = el('div', { class: 'rowline' });
      row.appendChild(h(`<span class="${r.correct ? 'good-text' : 'bad-text'}">${r.correct ? '✓' : '✕'}</span>`));
      row.appendChild(h(`<span class="grow">${esc(task ? taskText(task) : r.taskId)}</span>`));
      row.appendChild(h(`<span class="muted small">${esc(r.answer)}</span>`));
      taskList.appendChild(row);
    });
    root.appendChild(taskList);

    const exportBtn = el('button', { class: 'btn ghost', text: t('export_stats') });
    exportBtn.addEventListener('click', exportReport);
    root.appendChild(exportBtn);

    setTimeout(() => {
      const canvas = document.getElementById('topic-chart');
      const byTopic = {};
      attempt.results.forEach((r) => {
        const b = byTopic[r.topic] || (byTopic[r.topic] = { seen: 0, correct: 0 });
        b.seen++; if (r.correct) b.correct++;
      });
      CH.bars(canvas, Object.keys(byTopic).map((k) => ({
        label: topicTitle(k), value: byTopic[k].correct / byTopic[k].seen,
      })));
    }, 30);
    return root;
  }

  /* -------------------------------------------------- mistake analysis ---- */

  function screenReview(index) {
    const attempt = S.progress.attempts[index];
    if (!attempt) return el('div', { class: 'screen', text: t('empty_state') });
    const root = el('section', { class: 'screen' });
    const mistakes = attempt.results.filter((r) => !r.correct);
    root.appendChild(h(`<h1>${esc(t('mistakes_title'))}</h1>`));
    root.appendChild(h(`<p class="muted">${esc(t('mistakes_intro'))}</p>`));
    if (!mistakes.length) {
      root.appendChild(h(`<div class="card banner good">${esc(t('all_mistakes_done'))}</div>`));
      return root;
    }
    root.appendChild(h(`<div class="card muted">${esc(t('mistakes_left_fmt', mistakes.length))}</div>`));
    mistakes.forEach((r) => {
      const task = C.taskById(r.taskId);
      if (!task) return;
      const card = el('div', { class: 'card' });
      card.appendChild(h(`<div class="task-meta"><span class="pill">№${task.n}</span>
        <span class="pill muted">${esc(topicTitle(task.topic))}</span>
        ${task.year ? `<span class="pill muted">${esc(task.year)}</span>` : ''}</div>`));
      card.appendChild(h(`<div class="task-text">${esc(taskText(task))}</div>`));
      card.appendChild(analysisBlock(task, r.user, { showAnalogous: true }));
      const topicBtn = el('button', { class: 'btn small', text: t('repeat_topic_fmt', topicTitle(task.topic)) });
      topicBtn.addEventListener('click', () => { location.hash = '#/practice/' + encodeURIComponent(task.topic); });
      card.appendChild(topicBtn);
      root.appendChild(card);
    });
    return root;
  }

  /* --------------------------------------------------------- statistics --- */

  function screenStats() {
    const root = el('section', { class: 'screen' });
    const totals = AN.totals(S.progress);
    root.appendChild(h(`<h1>${esc(t('stats_title'))}</h1>`));
    root.appendChild(h(`<div class="grid cards">
        ${statCard(t('tests_taken'), String(totals.tests))}
        ${statCard(t('tasks_solved'), String(totals.solved))}
        ${statCard(t('accuracy'), totals.solved ? rate(totals.rate) + '%' : '—')}
        ${statCard(t('avg_time_fmt', ' ').trim(), U.fmtDuration(totals.avgTaskMs))}
      </div>`));
    root.appendChild(h(`<div class="card">
        <div class="rowline"><span>${esc(t('daily_goal_fmt', S.progress.goal || 20))}</span>
        <span class="muted">${esc(String(S.progress.daily[U.today()] || 0))} / ${esc(String(S.progress.goal || 20))}</span></div>
        <div class="progress"><div class="progress-bar" style="width:${Math.min(100, 100 * (S.progress.daily[U.today()] || 0) / (S.progress.goal || 20))}%"></div></div>
        <p class="muted small">${esc(t('best_streak_fmt', S.progress.streak.best || 0))}</p>
      </div>`));

    if (!S.progress.attempts.length) {
      root.appendChild(h(`<div class="card muted">${esc(t('no_data_yet'))}</div>`));
      return root;
    }

    const topicAccuracy = AN.topicAccuracy(S.progress);
    const topics = Object.keys(topicAccuracy).sort((a, b) => topicAccuracy[a].rate - topicAccuracy[b].rate);
    root.appendChild(h(`<div class="card"><h3>${esc(t('by_topic'))}</h3><canvas id="stats-topics"></canvas></div>`));
    const yearAccuracy = AN.yearAccuracy(S.progress);
    root.appendChild(h(`<div class="card"><h3>${esc(t('by_year'))}</h3><canvas id="stats-years"></canvas></div>`));
    const recent = AN.lastAttempts(S.progress, 10);
    const recentCard = el('div', { class: 'card' });
    recentCard.appendChild(h(`<h3>${esc(t('last_tests'))}</h3>`));
    recent.slice().reverse().forEach((a, i) => {
      const total = a.results.length;
      const correct = a.results.filter((r) => r.correct).length;
      const globalIndex = S.progress.attempts.indexOf(a);
      const row = el('div', { class: 'rowline' });
      row.appendChild(h(`<span class="grow">${esc(a.title)}</span>`));
      row.appendChild(h(`<span class="muted small">${esc(U.fmtDate(a.finishedAt))}</span>`));
      row.appendChild(h(`<span class="pill">${rate(total ? correct / total : 0)}%</span>`));
      const open = el('button', { class: 'btn small ghost', text: '→' });
      open.addEventListener('click', () => { location.hash = '#/results/' + globalIndex; });
      row.appendChild(open);
      recentCard.appendChild(row);
    });
    root.appendChild(recentCard);

    const weak = AN.weakTopics(S.progress, 5);
    const strong = AN.strongTopics(S.progress, 5);
    if (weak.length) {
      const card = el('div', { class: 'card' });
      card.appendChild(h(`<h3>${esc(t('weak_topics'))}</h3>`));
      weak.forEach((w) => card.appendChild(h(`<div class="rowline"><span class="grow">${esc(topicTitle(w.topic))}</span>
        <span class="muted">${rate(w.rate)}%</span>
        <button class="btn small" data-go="#/practice/${encodeURIComponent(w.topic)}">${esc(t('train_mode'))}</button></div>`)));
      root.appendChild(card);
    }
    if (strong.length) {
      const card = el('div', { class: 'card' });
      card.appendChild(h(`<h3>${esc(t('strong_topics'))}</h3>`));
      strong.forEach((w) => card.appendChild(h(`<div class="rowline"><span class="grow">${esc(topicTitle(w.topic))}</span>
        <span class="muted">${rate(w.rate)}%</span><span class="pill good-pill">${esc(t('mastered'))}</span></div>`)));
      root.appendChild(card);
    }

    const actions = el('div', { class: 'rowline wrap' });
    const exportBtn = el('button', { class: 'btn', text: t('export_stats') });
    exportBtn.addEventListener('click', exportReport);
    actions.appendChild(exportBtn);
    const reset = el('button', { class: 'btn ghost danger', text: t('reset_stats') });
    reset.addEventListener('click', () => {
      const body = el('div', { html: `<p>${esc(t('reset_confirm'))}</p>` });
      const footer = el('div', { class: 'rowline' });
      const cancel = el('button', { class: 'btn ghost', text: t('cancel') });
      cancel.addEventListener('click', closeModal);
      const ok = el('button', { class: 'btn danger', text: t('yes') });
      ok.addEventListener('click', () => {
        S.progress = AN.emptyProgress();
        S.session = null;
        S.flush(); closeModal(); render();
      });
      footer.appendChild(cancel); footer.appendChild(ok);
      sheet(t('reset_stats'), body, footer);
    });
    actions.appendChild(reset);
    root.appendChild(actions);

    setTimeout(() => {
      CH.bars(document.getElementById('stats-topics'),
        topics.map((k) => ({ label: topicTitle(k), value: topicAccuracy[k].rate })));
      CH.bars(document.getElementById('stats-years'),
        Object.keys(yearAccuracy).sort().map((k) => ({
          label: k === 'gen' ? t('train_mode') : k,
          value: yearAccuracy[k].rate,
          color: k === 'gen' ? '#7c5cff' : undefined,
        })));
    }, 30);
    return root;
  }

  /* ---------------------------------------------------- endless practice -- */

  function screenPractice(topic) {
    const root = el('section', { class: 'screen' });
    if (!topic) {
      root.appendChild(h(`<h1>${esc(t('train_mode'))}</h1><p class="muted">${esc(t('train_subtitle'))}</p>`));
      const list = el('div', { class: 'grid cards' });
      const topics = Object.keys((C.topics && C.topics.topics) || {});
      topics.forEach((key) => {
        const stats = (S.progress.topicStats || {})[key];
        const badge = stats ? `<span class="pill">${rate(stats.correct / stats.seen)}%</span>` : '';
        list.appendChild(h(`<div class="card"><div class="rowline"><span class="grow">${esc(topicTitle(key))}</span>${badge}</div>
          <button class="btn small primary" data-go="#/practice/${encodeURIComponent(key)}">${esc(t('start'))}</button></div>`));
      });
      root.appendChild(list);
      return root;
    }
    const pool = C.analogous.filter((task) => task.topic === topic);
    const tasks = pool.length ? pool : C.analogous;
    const task = tasks[Math.abs((CT.practiceSeed = (CT.practiceSeed || 0) + 1)) % tasks.length];
    root.appendChild(h(`<h1>${esc(topicTitle(topic))}</h1>`));
    const card = el('div', { class: 'card' });
    card.appendChild(h(`<div class="task-meta"><span class="pill">${esc(t('train_mode'))}</span>
      <span class="pill muted">${esc(topicTitle(task.topic))}</span></div>`));
    card.appendChild(h(`<div class="task-text">${esc(taskText(task))}</div>`));
    const row = el('div', { class: 'answer-row' });
    const input = el('input', { type: 'text', class: 'answer-input big', placeholder: t('answer_placeholder') });
    const check = el('button', { class: 'btn primary', text: t('check_answer') });
    row.appendChild(input); row.appendChild(check);
    card.appendChild(row);
    const feedback = el('div', { class: 'feedback' });
    card.appendChild(feedback);
    check.addEventListener('click', () => {
      const ok = A.check(input.value, task);
      S.progress.daily[U.today()] = (S.progress.daily[U.today()] || 0) + 1;
      AN.touchStreak(S.progress, U.today());
      const bucket = S.progress.topicStats[task.topic] || (S.progress.topicStats[task.topic] = { seen: 0, correct: 0 });
      bucket.seen++; if (ok) bucket.correct++;
      S.saveProgress();
      feedback.innerHTML = '';
      if (ok) {
        feedback.appendChild(h(`<div class="banner good">${esc(t('answer_correct'))}</div>`));
      } else {
        feedback.appendChild(h(`<div class="banner bad">${esc(t('answer_incorrect'))}</div>`));
        feedback.appendChild(analysisBlock(task, input.value, { showAnalogous: false }));
      }
    });
    root.appendChild(card);
    const again = el('button', { class: 'btn', text: t('next') });
    again.addEventListener('click', render);
    root.appendChild(again);
    return root;
  }

  /* ------------------------------------------------------------ tools ----- */

  function openTools(task, tab) {
    const body = el('div', { class: 'tools' });
    const tabs = el('div', { class: 'tabs' });
    const panes = el('div', { class: 'tools-body' });
    const defs = [
      { id: 'calc', title: t('tool_calculator'), render: toolCalculator },
      { id: 'formulas', title: t('tool_formula_sheet'), render: () => toolFormulas(task) },
      { id: 'scratch', title: t('tool_scratchpad'), render: toolScratch },
      { id: 'graph', title: t('tool_graph'), render: toolGraph },
    ];
    defs.forEach((def) => {
      const btn = el('button', { class: 'tab' + (def.id === (tab || 'calc') ? ' active' : ''), text: def.title });
      btn.addEventListener('click', () => {
        U.$$('.tab', tabs).forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        panes.innerHTML = '';
        panes.appendChild(def.render());
      });
      tabs.appendChild(btn);
    });
    body.appendChild(tabs);
    panes.appendChild(defs.filter((d) => d.id === (tab || 'calc'))[0].render());
    body.appendChild(panes);
    sheet(t('tools_title'), body, null);
  }

  function toolCalculator() {
    const wrap = el('div', {});
    const input = el('input', { type: 'text', class: 'answer-input big', placeholder: '2*sqrt(3) + 1' });
    const result = el('div', { class: 'calc-result' });
    const history = el('div', { class: 'calc-history' });
    const buttons = el('div', { class: 'calc-keys' });
    const keys = ['7', '8', '9', '/', '4', '5', '6', '*', '1', '2', '3', '-', '0', '.', '√', '+',
      '(', ')', '^', 'π', 'C'];
    keys.forEach((k) => {
      const b = el('button', { class: 'key', text: k });
      b.addEventListener('click', () => {
        if (k === 'C') input.value = '';
        else if (k === '√') input.value += '√(';
        else input.value += k;
        input.focus();
      });
      buttons.appendChild(b);
    });
    const evalNow = () => {
      try {
        const value = M.evaluate(input.value);
        if (!isFinite(value)) throw new Error('not finite');
        result.textContent = String(Math.round(value * 1e10) / 1e10);
        const line = el('div', { class: 'rowline small' });
        line.appendChild(h(`<span class="grow">${esc(input.value)}</span><span>= ${esc(result.textContent)}</span>`));
        history.prepend(line);
        result.className = 'calc-result good';
      } catch (e) {
        result.textContent = t('error_generic');
        result.className = 'calc-result bad';
      }
    };
    input.addEventListener('keydown', (ev) => { if (ev.key === 'Enter') evalNow(); });
    const go = el('button', { class: 'btn primary', text: '=' });
    go.addEventListener('click', evalNow);
    wrap.appendChild(h(`<p class="muted small">${esc(t('calc_expression'))} · ${esc(t('keyboard_help'))}</p>`));
    wrap.appendChild(input);
    wrap.appendChild(result);
    wrap.appendChild(buttons);
    wrap.appendChild(go);
    wrap.appendChild(h(`<p class="muted small">${esc(t('calc_history'))}</p>`));
    wrap.appendChild(history);
    return wrap;
  }

  function toolFormulas(task) {
    const wrap = el('div', {});
    const search = el('input', { type: 'text', class: 'answer-input', placeholder: t('search') });
    const list = el('div', { class: 'formula-list' });
    const renderList = (needle) => {
      list.innerHTML = '';
      C.formulas.forEach((group) => {
        const title = I.pick(group.title);
        const items = (group.items || []).filter((item) => {
          if (!needle) return true;
          const text = (I.pick(item.name) + ' ' + item.formula).toLowerCase();
          return text.indexOf(needle.toLowerCase()) >= 0;
        });
        if (!items.length) return;
        const details = el('details', { class: 'formula-group', open: needle ? 'open' : null });
        details.appendChild(el('summary', { text: title }));
        items.forEach((item) => details.appendChild(h(
          `<div class="formula-item"><div class="formula-name">${esc(I.pick(item.name))}</div>
           <div class="formula-body">${esc(item.formula)}</div></div>`)));
        list.appendChild(details);
      });
      if (!list.children.length) list.appendChild(h(`<p class="muted">${esc(t('empty_state'))}</p>`));
    };
    search.addEventListener('input', () => renderList(search.value));
    renderList('');
    if (task) wrap.appendChild(h(`<p class="muted small">${esc(topicTitle(task.topic))}</p>`));
    wrap.appendChild(search);
    wrap.appendChild(list);
    return wrap;
  }

  function toolScratch() {
    const wrap = el('div', {});
    const area = el('textarea', { class: 'scratch', rows: '12' });
    area.value = (S.settings.scratch || '');
    area.addEventListener('input', () => { S.settings.scratch = area.value; S.saveSettings(); });
    const clear = el('button', { class: 'btn ghost small', text: t('clear') });
    clear.addEventListener('click', () => { area.value = ''; S.settings.scratch = ''; S.saveSettings(); });
    const insert = el('button', { class: 'btn ghost small', text: t('insert_task') === 'insert_task' ? '√ π' : t('insert_task') });
    insert.addEventListener('click', () => { area.value += ' √ π ² '; });
    wrap.appendChild(h(`<p class="muted small">${esc(t('scratch_placeholder'))}</p>`));
    wrap.appendChild(area);
    const row = el('div', { class: 'rowline' });
    row.appendChild(insert); row.appendChild(clear);
    wrap.appendChild(row);
    return wrap;
  }

  function toolGraph() {
    const wrap = el('div', {});
    const input = el('input', { type: 'text', class: 'answer-input', value: (S.settings.graphFn || 'x^2 - 3x + 2') });
    const canvas = el('canvas', { class: 'graph', height: '240' });
    const err = el('div', { class: 'muted small', text: '' });
    const draw = () => {
      let from = parseFloat(fromInput.value);
      let to = parseFloat(toInput.value);
      if (isNaN(from)) from = -5;
      if (isNaN(to)) to = 5;
      try {
        const ok = CH.plot(canvas, input.value, from, to);
        err.textContent = ok ? '' : t('graph_error');
        S.settings.graphFn = input.value;
        S.settings.graphFrom = from;
        S.settings.graphTo = to;
        S.saveSettings();
      } catch (e) {
        err.textContent = t('graph_error') + ': ' + e.message;
      }
    };
    const range = el('div', { class: 'rowline' });
    const fromInput = el('input', { type: 'text', class: 'answer-input small', value: String(S.settings.graphFrom || -5) });
    const toInput = el('input', { type: 'text', class: 'answer-input small', value: String(S.settings.graphTo || 5) });
    range.appendChild(el('span', { text: 'x ∈ [' }));
    range.appendChild(fromInput);
    range.appendChild(el('span', { text: ';' }));
    range.appendChild(toInput);
    range.appendChild(el('span', { text: ']' }));
    const go = el('button', { class: 'btn primary', text: t('graph_plot') });
    go.addEventListener('click', draw);
    input.addEventListener('keydown', (ev) => { if (ev.key === 'Enter') draw(); });
    wrap.appendChild(h(`<p class="muted small">${esc(t('graph_examples'))}</p>`));
    wrap.appendChild(input);
    wrap.appendChild(range);
    wrap.appendChild(go);
    wrap.appendChild(canvas);
    wrap.appendChild(err);
    setTimeout(draw, 30);
    return wrap;
  }

  /* -------------------------------------------------------- update ------- */

  function screenUpdate() {
    const root = el('section', { class: 'screen' });
    root.appendChild(h(`<h1>${esc(t('update_title'))}</h1>`));
    const status = el('div', { class: 'card', text: t('update_checking') });
    root.appendChild(status);
    const current = (C.meta && C.meta.version) || (S.content && S.content.version) || '';
    status.innerHTML = `<p>${esc(t('content_version_fmt', current || '—'))}</p>
      <p class="muted small">${esc(t('update_source_note'))}</p>
      <p class="muted small">${esc(t('update_offline_ok'))}</p>`;
    const actions = el('div', { class: 'rowline wrap' });
    const checkBtn = el('button', { class: 'btn primary', text: t('check_updates') });
    checkBtn.addEventListener('click', async () => {
      checkBtn.disabled = true;
      status.appendChild(h(`<p class="muted">${esc(t('update_checking'))}</p>`));
      const result = await B.checkUpdates(S.settings.baseUrl, current);
      checkBtn.disabled = false;
      if (result.status === 'ok') {
        status.appendChild(h(`<p class="banner good">${esc(t('update_installed_fmt', result.version))} · +${esc(String(result.newTasks || 0))}</p>`));
        C.meta.version = result.version;
      } else if (result.status === 'uptodate') {
        status.appendChild(h(`<p class="banner good">${esc(t('update_none'))}</p>`));
      } else {
        status.appendChild(h(`<p class="banner bad">${esc(t('update_failed'))}</p>
          <p class="muted small">${esc(result.message || '')}</p>`));
      }
    });
    actions.appendChild(checkBtn);
    const folder = el('button', { class: 'btn ghost', text: t('win_open_data_folder') });
    folder.addEventListener('click', () => B.openFolder('data'));
    actions.appendChild(folder);
    const quit = el('button', { class: 'btn ghost', text: t('win_close') });
    quit.addEventListener('click', () => B.quit());
    actions.appendChild(quit);
    root.appendChild(actions);
    return root;
  }

  /* -------------------------------------------------------- settings ----- */

  function screenSettings() {
    const root = el('section', { class: 'screen' });
    root.appendChild(h(`<h1>${esc(t('settings_title'))}</h1>`));

    const langCard = el('div', { class: 'card' });
    langCard.appendChild(h(`<h3>${esc(t('language'))}</h3>`));
    const langRow = el('div', { class: 'rowline wrap' });
    [['ru', t('lang_ru')], ['en', t('lang_en')]].forEach(([code, label]) => {
      const b = el('button', { class: 'btn' + (S.settings.lang === code ? ' primary' : ''), text: label });
      b.addEventListener('click', () => {
        S.settings.lang = code;
        I.setLang(code);
        S.saveSettings();
        render();
      });
      langRow.appendChild(b);
    });
    langCard.appendChild(langRow);
    langCard.appendChild(h(`<p class="muted small">${esc(t('english_mode_hint'))}</p>`));
    const englishToggle = toggleRow(t('bilingual_solutions'), S.settings.showEnglishSolutions, (value) => {
      S.settings.showEnglishSolutions = value; S.saveSettings();
    });
    langCard.appendChild(englishToggle);
    root.appendChild(langCard);

    const themeCard = el('div', { class: 'card' });
    themeCard.appendChild(h(`<h3>${esc(t('theme'))}</h3>`));
    const themeRow = el('div', { class: 'rowline wrap' });
    [['system', t('theme_system')], ['light', t('theme_light')], ['dark', t('theme_dark')]].forEach(([code, label]) => {
      const b = el('button', { class: 'btn' + (S.settings.theme === code ? ' primary' : ''), text: label });
      b.addEventListener('click', () => { S.settings.theme = code; applyTheme(); S.saveSettings(); render(); });
      themeRow.appendChild(b);
    });
    themeCard.appendChild(themeRow);
    themeCard.appendChild(h(`<h3>${esc(t('font_size'))}</h3>`));
    const fontRow = el('div', { class: 'rowline wrap' });
    [['small', t('font_small')], ['normal', t('font_normal')], ['large', t('font_large')]].forEach(([code, label]) => {
      const b = el('button', { class: 'btn' + (S.settings.fontSize === code ? ' primary' : ''), text: label });
      b.addEventListener('click', () => { S.settings.fontSize = code; applyFontSize(); S.saveSettings(); render(); });
      fontRow.appendChild(b);
    });
    themeCard.appendChild(fontRow);
    root.appendChild(themeCard);

    const examCard = el('div', { class: 'card' });
    examCard.appendChild(h(`<h3>${esc(t('nav_exam'))}</h3>`));
    examCard.appendChild(h(`<label class="field"><span>${esc(t('exam_timer_set'))}</span>
      <input type="number" min="10" max="300" step="5" id="exam-minutes" value="${Number(S.settings.examMinutes) || 180}"></label>`));
    examCard.appendChild(toggleRow(t('auto_advance'), S.settings.autoAdvance, (v) => { S.settings.autoAdvance = v; S.saveSettings(); }));
    examCard.appendChild(toggleRow(t('keep_screen_on'), S.settings.keepScreenOn, (v) => { S.settings.keepScreenOn = v; S.saveSettings(); }));
    examCard.appendChild(toggleRow(t('sound'), S.settings.sound, (v) => { S.settings.sound = v; S.saveSettings(); }));
    examCard.appendChild(toggleRow(t('vibration'), S.settings.vibration, (v) => { S.settings.vibration = v; S.saveSettings(); }));
    examCard.appendChild(toggleRow(t('auto_update'), S.settings.autoUpdate, (v) => { S.settings.autoUpdate = v; S.saveSettings(); }));
    root.appendChild(examCard);

    root.appendChild(h(`<div class="card"><div class="rowline"><span class="grow">${esc(t('update_title'))}</span>
      <button class="btn small" data-go="#/update">${esc(t('check_updates'))}</button></div></div>`));
    root.appendChild(h(`<div class="card"><div class="rowline"><span class="grow">${esc(t('about_title'))}</span>
      <button class="btn small" data-go="#/about">→</button></div></div>`));

    const input = root.querySelector('#exam-minutes');
    if (input) input.addEventListener('change', () => {
      const value = Math.max(10, Math.min(300, parseInt(input.value, 10) || 180));
      S.settings.examMinutes = value;
      input.value = value;
      S.saveSettings();
    });
    return root;
  }

  function toggleRow(label, value, onChange) {
    const row = el('div', { class: 'rowline toggle-row' });
    row.appendChild(h(`<span class="grow">${esc(label)}</span>`));
    const btn = el('button', { class: 'switch' + (value ? ' on' : ''), 'aria-pressed': value ? 'true' : 'false' });
    btn.addEventListener('click', () => {
      const next = !btn.classList.contains('on');
      btn.classList.toggle('on', next);
      btn.setAttribute('aria-pressed', next ? 'true' : 'false');
      onChange(next);
    });
    row.appendChild(btn);
    return row;
  }

  function applyTheme() {
    const mode = S.settings.theme || 'system';
    document.body.dataset.theme = mode;
  }
  function applyFontSize() {
    document.body.dataset.font = S.settings.fontSize || 'normal';
  }

  /* ----------------------------------------------------------- about ----- */

  function screenAbout() {
    const root = el('section', { class: 'screen' });
    const version = CT.version;
    const contentVersion = (C.meta && C.meta.version) || '—';
    root.appendChild(h(`<h1>${esc(t('about_title'))}</h1>`));
    root.appendChild(h(`<div class="card">
        <p>${esc(t('about_text'))}</p>
        <p class="muted small">${esc(t('disclaimer'))}</p>
        <p class="muted small">${esc(t('win_about_engine'))}</p>
      </div>`));
    root.appendChild(h(`<div class="card">
        <h3>${esc(t('how_it_works'))}</h3>
        <p class="pre">${esc(t('how_it_works_text'))}</p>
      </div>`));
    const contact = el('div', { class: 'card' });
    contact.appendChild(h(`<h3>${esc(t('developer'))}</h3>`));
    contact.appendChild(h(`<p class="dev-name">${esc(t('author_name'))}</p>`));
    const email = t('contact_email');
    const phone = t('contact_phone');
    const whatsapp = 'https://wa.me/' + phone.replace(/[^0-9]/g, '');
    contact.appendChild(h(`<div class="contacts">
        <a class="contact" href="mailto:${esc(email)}?subject=${encodeURIComponent(t('feedback_subject'))}">
          <span class="contact-icon">✉</span><span>${esc(t('contact_email_label'))}: <strong>${esc(email)}</strong></span></a>
        <a class="contact" href="tel:${esc(phone)}">
          <span class="contact-icon">☎</span><span>${esc(t('contact_phone_label'))}: <strong>${esc(phone)}</strong></span></a>
        <a class="contact" href="${esc(whatsapp)}" target="_blank" rel="noopener">
          <span class="contact-icon">💬</span><span>${esc(t('contact_whatsapp_label'))}: <strong>${esc(phone)}</strong></span></a>
        <a class="contact" href="https://github.com/zigorminsk-debug/mathematics" target="_blank" rel="noopener">
          <span class="contact-icon">⌨</span><span>${esc(t('source_code'))}</span></a>
      </div>`));
    root.appendChild(contact);
    root.appendChild(h(`<div class="card muted small">
        ${esc(t('version_label'))}: ${esc(version)} · ${esc(t('content_version_fmt', contentVersion))}<br>
        ${esc(t('build_label'))}: ${esc((S.app && S.app.build) || 'dev')} · ${esc((S.app && S.app.platform) || 'web')}
      </div>`));
    return root;
  }

  /* ----------------------------------------------------------- report ---- */

  function exportReport() {
    const totals = AN.totals(S.progress);
    const topicAccuracy = AN.topicAccuracy(S.progress);
    const rows = Object.keys(topicAccuracy).map((key) =>
      `<tr><td>${esc(topicTitle(key))}</td><td>${topicAccuracy[key].seen}</td>
       <td>${topicAccuracy[key].correct}</td><td>${rate(topicAccuracy[key].rate)}%</td></tr>`).join('');
    const attempts = S.progress.attempts.slice().reverse().map((a) => {
      const correct = a.results.filter((r) => r.correct).length;
      return `<tr><td>${esc(a.title)}</td><td>${esc(U.fmtDate(a.finishedAt))}</td>
        <td>${correct} / ${a.results.length}</td><td>${rate(a.results.length ? correct / a.results.length : 0)}%</td></tr>`;
    }).join('');
    const html = `<!DOCTYPE html><html lang="${lang()}"><head><meta charset="utf-8">
      <title>${esc(t('stats_title'))}</title>
      <style>body{font-family:system-ui,sans-serif;margin:32px;color:#222}
      table{border-collapse:collapse;margin:16px 0;width:100%}
      td,th{border:1px solid #ccc;padding:6px 10px;text-align:left}
      h1{margin-bottom:4px}</style></head><body>
      <h1>${esc(t('app_name'))}</h1>
      <p>${esc(t('stats_title'))} · ${esc(t('developer'))}: ${esc(t('author_name'))} ·
         ${esc(t('contact_email'))} ${esc(t('contact_phone'))}</p>
      <p>${esc(t('tests_taken'))}: ${totals.tests} · ${esc(t('tasks_solved'))}: ${totals.solved} ·
         ${esc(t('accuracy'))}: ${rate(totals.rate)}%</p>
      <h2>${esc(t('by_topic'))}</h2>
      <table><tr><th>${esc(t('by_topic'))}</th><th>${esc(t('tasks_solved'))}</th>
      <th>${esc(t('correct'))}</th><th>${esc(t('accuracy'))}</th></tr>${rows}</table>
      <h2>${esc(t('last_tests'))}</h2>
      <table><tr><th>${esc(t('tests_title'))}</th><th>${esc(t('time_spent_fmt', ''))}</th>
      <th>${esc(t('score_fmt', '', ''))}</th><th>${esc(t('percent_fmt', ''))}</th></tr>${attempts}</table>
      </body></html>`;
    B.saveReport('progress', html).then((res) => {
      B.notify(res && res.path ? t('win_report_saved_fmt', res.path) : t('export_stats'));
    });
  }

  /* ------------------------------------------------------------ router --- */

  const routes = {
    '#/home': () => screenHome(),
    '#/tests': () => screenTests(),
    '#/exam': () => screenExam(),
    '#/test': () => screenTest(),
    '#/stats': () => screenStats(),
    '#/formulas': () => screenFormulas(),
    '#/settings': () => screenSettings(),
    '#/about': () => screenAbout(),
    '#/update': () => screenUpdate(),
  };

  function screenFormulas() {
    const root = el('section', { class: 'screen' });
    root.appendChild(h(`<h1>${esc(t('nav_formulas'))}</h1>`));
    root.appendChild(toolFormulas(null));
    return root;
  }

  function parseHash() {
    const hash = location.hash || '#/home';
    const parts = hash.split('/').filter(Boolean);
    const name = '#/' + (parts[0] || 'home');
    return { name, parts };
  }

  function render() {
    const route = parseHash();
    const node = document.getElementById('view');
    node.innerHTML = '';
    const container = el('div', { class: 'container' });
    let content;
    try {
      if (route.name === '#/results') content = screenResults(parseInt(route.parts[1], 10));
      else if (route.name === '#/review') content = screenReview(parseInt(route.parts[1], 10));
      else if (route.name === '#/practice') content = screenPractice(route.parts[1] ? decodeURIComponent(route.parts[1]) : null);
      else content = (routes[route.name] || routes['#/home'])();
    } catch (error) {
      content = h(`<div class="card banner bad">${esc(t('error_generic'))}: ${esc(error.message)}</div>`);
    }
    container.appendChild(content);
    node.appendChild(container);
    U.$$('[data-go]').forEach((btn) => {
      if (btn._bound) return;
      btn._bound = true;
      btn.addEventListener('click', () => { location.hash = btn.getAttribute('data-go'); });
    });
    U.$$('[data-start]').forEach((btn) => {
      if (btn._bound) return;
      btn._bound = true;
      btn.addEventListener('click', () => {
        const parts = btn.getAttribute('data-start').split('|');
        startTest(parts[0], parts[1]);
      });
    });
    renderNav();
    window.scrollTo(0, 0);
  }

  function renderNav() {
    const nav = document.getElementById('mainnav');
    const route = parseHash().name;
    const items = [
      ['#/home', '🏠', t('nav_tests')],
      ['#/tests', '📘', t('nav_tests')],
      ['#/practice', '🎯', t('nav_train')],
      ['#/stats', '📈', t('nav_stats')],
      ['#/formulas', 'Σ', t('nav_formulas')],
      ['#/settings', '⚙', t('nav_settings')],
      ['#/about', 'ℹ', t('nav_about')],
    ];
    nav.innerHTML = '';
    items.forEach(([href, icon, label], index) => {
      if (index === 0) return;   // the brand logo links home
      const a = el('a', { href, class: 'nav-item' + (route === href ? ' active' : '') });
      a.innerHTML = `<span class="nav-icon">${icon}</span><span class="nav-label">${esc(label)}</span>`;
      nav.appendChild(a);
    });
  }

  function applyChrome() {
    document.title = t('app_name');
    document.getElementById('brand-name').textContent = t('app_name');
    document.getElementById('brand').addEventListener('click', () => { location.hash = '#/home'; });
    const langBtn = document.getElementById('lang-toggle');
    langBtn.textContent = lang() === 'ru' ? 'EN' : 'RU';
    langBtn.title = t('language');
    langBtn.addEventListener('click', () => {
      S.settings.lang = lang() === 'ru' ? 'en' : 'ru';
      I.setLang(S.settings.lang);
      S.saveSettings();
      applyChrome();
      render();
    });
    const settingsBtn = document.getElementById('btn-settings');
    settingsBtn.addEventListener('click', () => { location.hash = '#/settings'; });
    document.getElementById('footer').innerHTML = `
      <span>${esc(t('developer'))}: <a href="mailto:${esc(t('contact_email'))}">${esc(t('author_name'))}</a> ·
      <a href="mailto:${esc(t('contact_email'))}">${esc(t('contact_email'))}</a> ·
      <a href="tel:${esc(t('contact_phone'))}">${esc(t('contact_phone'))}</a></span>`;
  }

  /* ------------------------------------------------------------- boot ---- */

  async function boot() {
    const loading = document.getElementById('view');
    loading.innerHTML = `<div class="container"><p class="muted">${esc(t('loading'))}</p></div>`;
    try {
      await C.load();
    } catch (error) {
      loading.innerHTML = `<div class="container"><div class="card banner bad">
        ${esc(t('error_generic'))}: ${esc(error.message)}</div></div>`;
      return;
    }
    await S.init();
    I.setLang(S.settings.lang);
    applyTheme();
    applyFontSize();
    applyChrome();
    window.addEventListener('hashchange', render);
    document.getElementById('modal').addEventListener('click', (ev) => {
      if (ev.target.id === 'modal') closeModal();
    });
    if (!location.hash) location.hash = '#/home';
    render();

    if (S.settings.autoUpdate) {
      const current = (C.meta && C.meta.version) || (S.content && S.content.version) || '';
      B.checkUpdates(S.settings.baseUrl, current).then((result) => {
        if (result && result.status === 'ok') {
          B.notify(t('update_installed_fmt', result.version));
        }
      });
    }
    setInterval(() => { S.flush(); if (S.session && !S.session.finished) S.saveSession(); }, 20000);
    window.addEventListener('beforeunload', () => S.flush());
  }

  /* Hardware back button on Android: close the sheet, leave the test, then exit. */
  CT.onAndroidBack = function () {
    const modalNode = document.getElementById('modal');
    if (modalNode && !modalNode.classList.contains('hidden')) { closeModal(); return null; }
    const route = parseHash().name;
    const run = S.session;
    if (run && !run.finished && route === '#/test') { location.hash = '#/tests'; return null; }
    if (route === '#/home') return 'exit';
    location.hash = '#/home';
    return null;
  };

  CT.boot = boot;
  CT.render = render;
  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
    else boot();
  }
})();

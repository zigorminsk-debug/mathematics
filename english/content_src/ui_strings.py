"""content_src/ui_strings.py — надписи интерфейса на двух языках (английский тренажёр).

RU — рабочий язык подготовки к ЦТ, EN — тот же интерфейс по-английски. Важно:
переключатель языка меняет **интерфейс**, но не проверяемый английский текст
задания. Ключи ``*_fmt`` подставляются через ``CT.i18n.t`` — число подстановок
``%s`` обязано совпадать в обеих языках (проверяет сборка контента).

Общие платформенные надписи (меню, темы, статистика, обновления) совпадают с
соседними приложениями: это одна и та же программа. Всё, что говорит о предмете,
проверке ответа и разборе, задано здесь: список ``ENGLISH_WORDING``.
"""

from __future__ import annotations

#: ключи, значение которых задано именно для английского тренажёра
ENGLISH_WORDING = (
    "about_text", "accepted_forms_fmt", "answer_hint", "answer_word_hint",
    "app_name", "app_tagline", "autocheck_hint", "case_hint", "correction_title",
    "disclaimer", "exam_rules_fmt", "feedback_subject", "given_word",
    "instruction_label", "language_note", "periods_note_fmt", "policy_title",
    "policy_article_ignore", "policy_apostrophe_ignore", "policy_case_insensitive",
    "policy_hyphen_significant", "policy_exact", "reason_apostrophe", "reason_article",
    "reason_case", "reason_empty", "reason_exact", "reason_near", "reason_space",
    "reason_stress", "reason_hyphen", "reason_ok", "rule_conditions", "rule_everyday", "rule_examples",
    "rule_formulation", "rule_open", "study_example", "study_plan", "type_extra",
    "type_form", "type_gap", "type_choice", "type_translate", "variant_note",
    "wrong_answer_title",
)

STRINGS = {
    # --- общее -------------------------------------------------------------
    "app_name": {"ru": "Репетитор ЦТ: Английский язык", "en": "CT English Tutor"},
    "app_tagline": {"ru": "Авторские варианты, правила и разбор ошибок офлайн",
                    "en": "Practice variants, rules and mistake analysis offline"},
    "about_text": {
        "ru": "Тренажёр по английскому языку для подготовки к ЦТ: авторские варианты в формате "
              "Английский язык — 18 A + 22 B, 120 минут, справочник правил, разбор ошибок и статистика. "
              "Работает без интернета; проверка ответов полностью офлайн.",
        "en": "An English tutor for CT preparation: authored variants in the exam format "
              "(18 A + 22 B, 120 minutes), a rules reference, mistake analysis and statistics. "
              "Works offline; answer checking is fully offline."},
    "disclaimer": {
        "ru": "Авторские наборы — не официальные задания РИКЗ; их годы лишь метки. Архив исходных сканов выделен отдельно, с источниками и оговорками. Приложение неофициальное.",
        "en": "Authored sets are not official RIKZ tasks; their years are labels. Original scans have a separate archive with sources and qualifications. This is an unofficial app."},
    "language_note": {
        "ru": "Переключатель языка меняет интерфейс; проверяемый английский текст остаётся английским.",
        "en": "The language switch changes the interface; the English text being checked stays English."},
    "home": {"ru": "Главная", "en": "Home"},
    "back": {"ru": "Назад", "en": "Back"},
    "close": {"ru": "Закрыть", "en": "Close"},
    "next": {"ru": "Дальше", "en": "Next"},
    "prev": {"ru": "Назад", "en": "Previous"},
    "finish": {"ru": "Завершить", "en": "Finish"},
    "check": {"ru": "Проверить", "en": "Check"},
    "skip": {"ru": "Пропустить", "en": "Skip"},
    "retry": {"ru": "Повторить", "en": "Retry"},
    "settings": {"ru": "Настройки", "en": "Settings"},
    "language": {"ru": "Язык", "en": "Language"},
    "theme": {"ru": "Тема", "en": "Theme"},
    "theme_light": {"ru": "Светлая", "en": "Light"},
    "theme_dark": {"ru": "Тёмная", "en": "Dark"},
    "theme_auto": {"ru": "Как в системе", "en": "System"},
    "large_text": {"ru": "Крупный шрифт", "en": "Large text"},
    "keep_screen_on": {"ru": "Не гасить экран", "en": "Keep the screen on"},
    "progress": {"ru": "Прогресс", "en": "Progress"},
    "statistics": {"ru": "Статистика", "en": "Statistics"},
    "stat_total_fmt": {"ru": "Отвечено заданий: %s", "en": "Tasks answered: %s"},
    "stat_correct_fmt": {"ru": "Верных: %s%%", "en": "Correct: %s%%"},
    "stat_streak_fmt": {"ru": "Дней подряд: %s", "en": "Days in a row: %s"},
    "stat_by_topic": {"ru": "По темам", "en": "By topic"},
    "stat_empty": {"ru": "Пока нет ответов — начните тренировку.",
                   "en": "No answers yet — start practising."},
    "mistakes": {"ru": "Ошибки", "en": "Mistakes"},
    "mistakes_empty": {"ru": "Ошибок нет — отличная работа.", "en": "No mistakes — well done."},
    "study": {"ru": "Изучить", "en": "Study"},
    "rules": {"ru": "Правила", "en": "Rules"},
    "train": {"ru": "Тренировка", "en": "Practice"},
    "exam": {"ru": "Вариант", "en": "Variant"},
    "topics": {"ru": "Темы", "en": "Topics"},
    "checklist": {"ru": "Памятка перед проверкой", "en": "Checklist before submitting"},
    "figure_zoom": {"ru": "Увеличить", "en": "Zoom in"},
    "figure_reset": {"ru": "Сбросить масштаб", "en": "Reset zoom"},
    "export_report": {"ru": "Сохранить отчёт", "en": "Save report"},
    "report_saved": {"ru": "Отчёт сохранён", "en": "Report saved"},
    "updates_check": {"ru": "Проверить обновления", "en": "Check for updates"},
    "updates_none": {"ru": "Обновлений нет", "en": "No updates"},
    "updates_found_fmt": {"ru": "Доступна версия %s", "en": "Version %s is available"},
    "offline_note": {"ru": "Работает офлайн", "en": "Works offline"},

    # --- экзамен и варианты -------------------------------------------------
    "exam_rules_fmt": {
        "ru": "В варианте %s заданий: часть А — %s, часть В — %s. Время: %s минут.",
        "en": "The variant has %s tasks: part A — %s, part B — %s. Time: %s minutes."},
    "variant_note": {
        "ru": "Авторский набор в современной тренировочной структуре: 18 A + 22 B, 120 минут. Год — метка набора, не архив и не исторический формат ЦТ.",
        "en": "Authored set in the current practice structure: 18 A + 22 B, 120 minutes. The year labels a set, not an exam archive or historical CT format."},
    "part_a": {"ru": "Часть А", "en": "Part A"},
    "part_b": {"ru": "Часть В", "en": "Part B"},
    "part_a_hint": {"ru": "Выберите один из предложенных вариантов.", "en": "Choose one of the offered options."},
    "part_b_hint": {"ru": "Впишите ответ словом.", "en": "Type the answer."},
    "time_left_fmt": {"ru": "Осталось: %s", "en": "Time left: %s"},
    "exam_finished": {"ru": "Вариант завершён", "en": "Variant finished"},
    "score_fmt": {"ru": "Верных ответов: %s из %s", "en": "Correct answers: %s out of %s"},
    "score_parts_fmt": {"ru": "Часть А: %s из %s · Часть В: %s из %s",
                        "en": "Part A: %s of %s · Part B: %s of %s"},
    "review_answers": {"ru": "Разобрать ответы", "en": "Review the answers"},
    "periods_note_fmt": {"ru": "Готовые варианты: %s. Готовятся: %s.",
                         "en": "Released variants: %s. In preparation: %s."},

    # --- задания и проверка -------------------------------------------------
    "task_fmt": {"ru": "Задание %s", "en": "Task %s"},
    "type_choice": {"ru": "Выбор из пяти", "en": "Choice of five"},
    "type_gap": {"ru": "Впишите пропущенное слово", "en": "Type the missing word"},
    "type_form": {"ru": "Образуйте форму слова", "en": "Form the required word"},
    "type_extra": {"ru": "Найдите лишнее слово", "en": "Find the extra word"},
    "type_translate": {"ru": "Переведите фрагмент", "en": "Translate the fragment"},
    "given_word": {"ru": "Дано", "en": "Given"},
    "instruction_label": {"ru": "Инструкция", "en": "Instruction"},
    "answer_saved": {"ru": "Ответ записан — правильность видно после завершения варианта.",
                     "en": "Answer recorded — correctness is shown after the variant is finished."},
    "answer_hint": {"ru": "Впишите ответ", "en": "Type your answer"},
    "answer_word_hint": {"ru": "Одно слово или фраза", "en": "A word or a phrase"},
    "autocheck_hint": {"ru": "Проверяется автоматически, без интернета.",
                       "en": "Checked automatically, without the internet."},
    "accepted_forms_fmt": {"ru": "Принимаются формы: %s", "en": "Accepted forms: %s"},
    "policy_title": {"ru": "Что проверяется", "en": "What is checked"},
    "policy_case_insensitive": {"ru": "регистр букв не важен", "en": "letter case is not checked"},
    "policy_article_ignore": {"ru": "артикль не проверяется", "en": "the article is not checked"},
    "policy_apostrophe_ignore": {"ru": "апостроф можно не ставить", "en": "the apostrophe is optional"},
    "policy_hyphen_significant": {"ru": "дефис значим", "en": "the hyphen matters"},
    "policy_exact": {"ru": "точное совпадение", "en": "exact match"},
    "case_hint": {"ru": "Заглавные буквы здесь важны.", "en": "Capital letters matter here."},
    "correction_title": {"ru": "Разбор", "en": "Explanation"},
    "wrong_answer_title": {"ru": "Почему это ошибка", "en": "Why this is a mistake"},
    "reason_ok": {"ru": "Верно", "en": "Correct"},
    "your_answer_fmt": {"ru": "Ваш ответ: %s", "en": "Your answer: %s"},
    "error_generic": {"ru": "Что-то пошло не так", "en": "Something went wrong"},
    "theory_visual_unavailable": {"ru": "Схема недоступна; пояснение приведено ниже.",
                                  "en": "The diagram is unavailable; the explanation is below."},
    "policy_empty_accept": {"ru": "если слово не нужно, поле остаётся пустым",
                            "en": "if no word is needed, the field stays empty"},
    "reason_empty": {"ru": "Ответ не введён", "en": "No answer entered"},
    "reason_case": {"ru": "Не совпал регистр букв", "en": "The letter case differs"},
    "reason_article": {"ru": "Лишний или пропущенный артикль", "en": "Extra or missing article"},
    "reason_apostrophe": {"ru": "Пропущен апостроф", "en": "The apostrophe is missing"},
    "reason_hyphen": {"ru": "Дефис написан иначе", "en": "The hyphen differs"},
    "reason_space": {"ru": "Пробелы расставлены иначе", "en": "The spacing differs"},
    "reason_stress": {"ru": "Различается только диакритика", "en": "Only the diacritic differs"},
    "reason_near": {"ru": "Почти совпало: другая форма или лишний знак",
                    "en": "A near miss: a different form or an extra sign"},
    "reason_exact": {"ru": "Ответ не совпал", "en": "The answer does not match"},
    "expected_fmt": {"ru": "Ожидалось: %s", "en": "Expected: %s"},
    "rule_open": {"ru": "Открыть правило", "en": "Open the rule"},
    "rule_formulation": {"ru": "Формулировка", "en": "Rule"},
    "rule_conditions": {"ru": "Условия применения", "en": "When it applies"},
    "rule_examples": {"ru": "Примеры", "en": "Examples"},
    "rule_everyday": {"ru": "Бытовое объяснение", "en": "Everyday explanation"},
    "study_plan": {"ru": "Что делать дальше", "en": "What to do next"},
    "study_example": {"ru": "Разобранный пример", "en": "Worked example"},
    "example_correct": {"ru": "Верно", "en": "Correct"},
    "example_wrong": {"ru": "Неверно", "en": "Wrong"},
    "analogous": {"ru": "Однотипные задания", "en": "Analogous exercises"},
    "analogous_hint": {"ru": "То же правило, другие слова из проверенного набора.",
                       "en": "The same rule with other reviewed items."},
    "feedback_subject": {"ru": "Английский язык", "en": "English"},
    "no_tasks": {"ru": "Пока нет заданий по этой теме.", "en": "No tasks for this topic yet."},
    "focus_kept": {"ru": "Фокус и позиция сохраняются при возврате.",
                   "en": "Focus and position are kept when returning."},
}


STRINGS.update({
    "archive_title": {"ru": "Архив исходных вариантов", "en": "Original source archive"},
    "archive_original": {"ru": "Исходная страница", "en": "Original page"},
    "archive_page": {"ru": "Страница", "en": "Page"},
    "archive_zoom": {"ru": "Масштаб", "en": "Zoom"},
    "archive_missing": {"ru": "Исходная страница отсутствует. Обновите приложение, не решайте неполное условие.", "en": "Original page missing. Update the app; do not attempt an incomplete condition."},
    "archive_attribution": {"ru": "Источник — предоставленный сборник по ссылке ниже. Задания и печатные ключи принадлежат исходным правообладателям; приложение добавляет распознавание, проверку и комментарии. Это не официальный продукт РИКЗ.", "en": "Source: the supplied collection linked below. Tasks and printed keys belong to their original rights holders; this app adds transcription, checking and notes. This is not an official RIKZ product."},
    "archive_source": {"ru": "Открыть источник в Drive (нужна сеть)", "en": "Open Drive source (internet required)"},
    "archive_reader_help": {"ru": "Текст условия распознан и приведён выше. Здесь можно сверить его с оригиналом. Найдите указанный номер задания на скане. При необходимости переключите страницу для чтения общего текста. Нумерация вариантов ответа сохранена. Сканы доступны офлайн.", "en": "A checked text transcription is shown above. Use this view to compare it with the original. Find the indicated task number on the scan. Change pages to read the shared passage when needed. Original option numbers are preserved. Scans work offline."},
    "archive_intro": {"ru": "По одному полному варианту № 1 из пяти предоставленных сборников, не все варианты книг. Условия распознаны и сверены со сканами, ответы — с печатными ключами. Это не авторские наборы и не официальный продукт РИКЗ. Разборы и ссылки на правила добавлены приложением.", "en": "One complete variant 1 from each of five supplied collections, not every variant in the books. Conditions are transcribed and checked against scans; answers are checked against printed keys. These are not authored sets and this is not an official RIKZ product. Notes and rule links are added by this app."},
    "archive_variant_one": {"ru": "Только вариант 1; остальная книга не импортирована", "en": "Variant 1 only; the rest of the book is not imported"},
    "archive_year_unverified": {"ru": "2024 — по имени файла. Страница с выходными данными отсутствует, год издания независимо не подтверждён.", "en": "2024 is from the filename. The imprint page is absent; the publication year is not independently verified."},
    "archive_key_reference_fmt": {"ru": "Печатный ключ: PDF-страница %s (номер в книге %s), колонка варианта 1.", "en": "Printed key: PDF page %s (book page %s), variant 1 column."},
    "archive_duration_fmt": {"ru": "Время по инструкции источника: %s минут.", "en": "Time stated by the source instructions: %s minutes."},
    "archive_practice_duration_fmt": {"ru": "Время в скане не указано. Тренировочный таймер: %s минут (меняется в настройках), не утверждение об историческом регламенте.", "en": "The scan does not state a duration. Practice timer: %s minutes (adjustable in settings), not a claim about historical exam rules."},
})

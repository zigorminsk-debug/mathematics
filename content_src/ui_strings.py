"""ui_strings.py — every interface string in Russian and English.

The RU/EN switch changes ONLY these strings and the explanations; checked
Russian material is never translated. Keys ending in ``_fmt`` take ``%s``
arguments (numbered %1$s… in the generated Android resources).
"""
from __future__ import annotations


def s(ru, en):
    return {"ru": ru, "en": en}


STRINGS = {
    # app
    "app_name": s("Репетитор ЦТ: Русский язык", "CT Russian Tutor"),
    "app_tagline": s("Подготовка к ЦЭ/ЦТ по русскому языку (Беларусь): авторские варианты по спецификации 2026 года, "
                     "правила с разбором ошибок", "Preparation for the Belarusian CE/CT in Russian: authored variants on the "
                     "2026 specification and rules with error analysis"),
    "about_title": s("О программе", "About"),
    "about_text": s("Офлайн-тренажёр по русскому языку для ЦЭ и ЦТ (Республика Беларусь): шесть авторских вариантов по "
                    "40 заданий, аналогичные упражнения по каждому правилу, карточки правил с исключениями, бытовыми "
                    "объяснениями и схемами, статистика и отчёты.",
                    "An offline Russian-language trainer for the Belarusian CE and CT: six authored variants of 40 tasks, "
                    "analogous exercises for every rule, rule cards with exceptions, everyday explanations and diagrams, "
                    "statistics and reports."),
    "about_spec_fmt": s("Структура вариантов сверена со спецификацией: %s (проверено %s).",
                        "The variant structure follows the specification: %s (checked %s)."),
    "developer": s("Разработчик", "Developer"),
    "developer_name": s("Захаревич Игорь", "Zakharevich Igor"),
    "contacts_hint": s("Сообщите об ошибке в задании или предложите правило — ответим.",
                       "Report a mistake in a task or suggest a rule — we will answer."),
    "feedback_subject": s("Репетитор ЦТ: Русский язык — отзыв", "CT Russian Tutor — feedback"),
    "source_code": s("Исходный код", "Source code"),
    "version_fmt": s("Версия приложения %s · банк %s", "App version %s · content %s"),
    "authored_task": s("авторское задание, не материал РИКЗ", "authored task, not a RIKZ material"),
    # navigation
    "nav_home": s("Главная", "Home"), "nav_tests": s("Варианты", "Variants"), "nav_exam": s("Экзамен", "Exam"),
    "nav_practice": s("Тренировка", "Practice"), "nav_study": s("Изучение", "Study"), "nav_rules": s("Правила", "Rules"),
    "nav_stats": s("Статистика", "Statistics"), "nav_tools": s("Инструменты", "Tools"), "nav_about": s("О программе", "About"),
    "nav_settings": s("Настройки", "Settings"),
    # common
    "cancel": s("Отмена", "Cancel"), "yes": s("Да", "Yes"), "close": s("Закрыть", "Close"), "clear": s("Очистить", "Clear"),
    "confirmation": s("Подтверждение", "Confirmation"), "prev": s("Назад", "Back"), "next": s("Далее", "Next"),
    "language": s("Язык / Language", "Language / Язык"),
    "language_hint": s("Переключается только интерфейс и пояснения. Русские тексты, слова и предложения заданий не "
                       "переводятся — они и есть объект проверки.", "Only the interface and explanations switch. Russian "
                       "texts, words and sentences of the tasks are never translated — they are what is being checked."),
    "no_data_yet": s("Пока нет данных — решите несколько заданий.", "No data yet — solve a few tasks."),
    "nothing_found": s("Ничего не найдено.", "Nothing found."),
    "error_generic": s("Что-то пошло не так. Вернитесь на главную и попробуйте снова.",
                       "Something went wrong. Go back home and try again."),
    "content_unavailable": s("Банк заданий не загрузился (или не относится к этому предмету). Переустановите обновление "
                             "или сообщите разработчику.", "The task bank did not load (or belongs to another subject). "
                             "Reinstall the update or contact the developer."),
    # home and stats
    "stat_tests": s("Пройдено вариантов", "Variants done"), "stat_tasks": s("Решено заданий", "Tasks solved"),
    "stat_accuracy": s("Точность", "Accuracy"), "stat_streak": s("Дней подряд", "Day streak"),
    "stat_minutes": s("Минут занятий", "Minutes of study"), "stat_time": s("Время", "Time"),
    "minutes_short": s("мин", "min"), "daily_goal": s("Цель дня", "Daily goal"),
    "daily_goal_fmt": s("Сегодня решено %s из %s", "Solved today: %s of %s"),
    "goal_done": s("Цель дня выполнена! Так держать.", "Daily goal reached! Keep going."),
    "weak_rules": s("Правила, которые стоит повторить", "Rules to revise"),
    "resume_title": s("Незавершённый прогон", "Unfinished run"),
    "resume_text": s("«%s»: задание %s из %s", "«%s»: task %s of %s"), "resume": s("Продолжить", "Resume"),
    "discard": s("Сбросить", "Discard"), "discard_confirm": s("Сбросить незавершённый прогон? Ответы будут потеряны.",
                                                              "Discard the unfinished run? Its answers will be lost."),
    "by_topic": s("По областям программы", "By syllabus area"), "by_topic_attempt": s("Результат по областям", "Result by area"),
    "by_year": s("По вариантам", "By variant"), "daily_activity": s("Активность по дням", "Daily activity"),
    "last_attempts": s("Последние попытки", "Recent attempts"), "reset_progress": s("Сбросить статистику", "Reset statistics"),
    "reset_confirm": s("Удалить всю статистику этого приложения? Настройки сохранятся.",
                       "Delete all statistics of this app? Settings are kept."),
    "progress_reset": s("Статистика сброшена", "Statistics reset"),
    "topic_stats_fmt": s("Верно: %s · заданий: %s", "Correct: %s · tasks: %s"),
    "tasks_count_fmt": s("%s заданий", "%s tasks"), "rules_count_fmt": s("Правил: %s", "Rules: %s"),
    # variants and exam
    "tests_intro": s("Шесть авторских вариантов по структуре спецификации РИКЗ 2026 года. Экзамен — с таймером и проверкой в "
                     "конце; тренировка — с разбором каждого ответа.", "Six authored variants on the structure of the 2026 "
                     "RIKZ specification. Exam: timer and checking at the end; practice: analysis after every answer."),
    "variant_title_fmt": s("Вариант %s (авторский)", "Variant %s (authored)"),
    "variant_parts_fmt": s("Часть A — %s заданий, часть B — %s", "Part A — %s tasks, part B — %s"),
    "exam_structure_fmt": s("Структура ЦЭ/ЦТ 2026: %s заданий (часть A — %s, часть B — %s), %s минут. В части A верных "
                            "ответов несколько.", "CE/CT 2026 structure: %s tasks (part A — %s, part B — %s), %s minutes. "
                            "Part A has several correct answers."),
    "start_exam": s("Экзамен", "Exam"), "start_train": s("Тренировка", "Practice"),
    "exam_rules_fmt": s("Экзамен длится %s минут. Ответы проверяются только после завершения; подсказки недоступны.",
                        "The exam lasts %s minutes. Answers are checked at the end; hints are unavailable."),
    "choose_variant": s("Выберите вариант:", "Choose a variant:"),
    "mixed_exam": s("Смешанный вариант (по одному заданию на каждую позицию)", "Mixed variant (one task per position)"),
    "mixed_exam_title": s("Смешанный вариант", "Mixed variant"),
    "task_of_fmt": s("Задание %s из %s", "Task %s of %s"), "level_fmt": s("уровень %s", "level %s"),
    "exercise_short": s("Упр.", "Ex."), "marked": s("Отмечено", "Marked"), "mark": s("Отметить", "Mark"),
    "task_grid": s("Все задания", "All tasks"), "task_grid_help": s("Зелёный — верно, красный — неверно, серый — есть ответ.",
                                                                    "Green — correct, red — wrong, grey — answered."),
    "finish_test": s("Завершить", "Finish"), "finish_confirm": s("Завершить прогон и посмотреть результат?",
                                                                 "Finish and see the result?"),
    "unanswered_warning_fmt": s("Без ответа заданий: %s. Всё равно завершить?", "Unanswered tasks: %s. Finish anyway?"),
    "time_is_up": s("Время вышло — работа завершена.", "Time is up — the work is finished."),
    "tool_hint": s("Подсказка", "Hint"), "hints": s("Подсказки", "Hints"),
    "tool_rules": s("Поиск правила", "Find a rule"), "tool_scratch": s("Черновик", "Scratchpad"),
    "tool_memos": s("Памятки", "Memos"), "tools_intro": s("Справочные инструменты: поиск по правилам, памятки и черновик.",
                                                          "Reference tools: rule search, memos and a scratchpad."),
    "scratch_placeholder": s("Записи сохраняются для каждого задания.", "Notes are kept per task."),
    "insert_stress": s("Вставить знак ударения", "Insert a stress mark"),
    # answering
    "answer_label": s("Ответ", "Answer"), "check_answer": s("Проверить", "Check"),
    "answer_correct": s("Верно!", "Correct!"), "answer_incorrect": s("Неверно — смотрите разбор и правило ниже.",
                                                                     "Wrong — see the analysis and the rule below."),
    "multi_hint": s("Выберите все верные варианты: лишний выбор так же ошибочен, как пропуск.",
                    "Choose all correct options: an extra choice is as wrong as a missing one."),
    "numbers_label": s("Номера (порядок не важен)", "Numbers (order does not matter)"),
    "sequence_label": s("Последовательность (порядок важен)", "Sequence (order matters)"),
    "numbers_placeholder": s("Например: 135", "For example: 135"),
    "numbers_hint": s("Нажмите номера или введите их цифрами; порядок не важен, повторять номер нельзя.",
                      "Tap the numbers or type them; order does not matter, no repeats."),
    "sequence_hint": s("Нажимайте номера в нужном порядке; порядок — часть ответа.", "Tap the numbers in order; order matters."),
    "reset_order": s("Сбросить", "Reset"),
    "word_placeholder": s("Ответ — точно, как в норме", "Answer exactly as the norm requires"),
    "word_hint": s("Пробел, дефис, буква ё и знаки — часть ответа. Без точки в конце.",
                   "Spaces, hyphens, ё and marks are part of the answer. No final period."),
    "integer_placeholder": s("Число", "Number"), "integer_hint": s("Запишите целое число цифрами.", "Write a whole number."),
    "stress_label": s("Буквы слова", "Letters of the word"),
    "stress_placeholder": s("Или введите слово с заглавной ударной гласной: звонИт", "Or type it with a capital stressed vowel"),
    "stress_hint": s("Нажмите на ударную гласную. Можно ввести слово, выделив ударную гласную заглавной буквой.",
                     "Tap the stressed vowel, or type the word with that vowel capitalised."),
    "stress_vowel_fmt": s("Гласная «%s», буква %s", "Vowel «%s», letter %s"),
    "match_hint": s("Для каждой буквы выберите номер; ответ запишется как А1Б2…", "Pick a number for each letter (А1Б2…)."),
    "match_select_fmt": s("Номер для %s", "Number for %s"),
    # analysis
    "your_answer": s("Ваш ответ", "Your answer"), "correct_answer": s("Правильный ответ", "Correct answer"),
    "also_accepted_fmt": s("Также принимается (обоснованно): %s", "Also accepted (justified): %s"),
    "misjudged_fmt": s("Ошибка в вариантах: %s", "Mistaken options: %s"),
    "why_wrong": s("Типичная ошибка", "Typical error"), "solution": s("Разбор", "Analysis"),
    "error_analysis": s("Разбор ошибки", "Error analysis"), "show_solution": s("Показать разбор", "Show analysis"),
    "analogous_title": s("Аналогичные упражнения на это правило", "Analogous exercises on this rule"),
    "analogous_hint": s("Решите похожие задания, чтобы закрепить именно это правило.",
                        "Solve similar tasks to consolidate this very rule."),
    "analogous_task_fmt": s("Упражнение %s", "Exercise %s"), "no_analogous": s("Аналогичных упражнений не нашлось.",
                                                                                "No analogous exercises found."),
    "study_rules_title": s("Повторите правило", "Revise the rule"), "study_open": s("Открыть область", "Open the area"),
    "rule_drill": s("Тренировать это правило", "Drill this rule"), "rule_drill_fmt": s("Правило: %s", "Rule: %s"),
    # results
    "result_title": s("Результат", "Result"), "percent_correct": s("верных ответов", "correct answers"),
    "score_fmt": s("Верно %s из %s", "Correct: %s of %s"), "part_a_fmt": s("Часть A: %s из %s", "Part A: %s of %s"),
    "part_b_fmt": s("Часть B: %s из %s", "Part B: %s of %s"), "time_spent_fmt": s("Время: %s", "Time: %s"),
    "score_note": s("Тренажёр считает верные задания. Официальный перевод первичных баллов в тестовые здесь не "
                    "имитируется.", "The tutor counts correct tasks. Official conversion of primary to test scores is not "
                    "simulated."),
    "review_mistakes_fmt": s("Разобрать ошибки (%s)", "Review mistakes (%s)"),
    "reinforce": s("Закрепить: аналогичные упражнения", "Consolidate: analogous exercises"),
    "reinforce_title": s("Закрепление ошибок", "Consolidation"), "to_tests": s("К вариантам", "To variants"),
    "mistakes_title": s("Разбор ошибок", "Mistakes"), "no_mistakes": s("Ошибок нет — отлично!", "No mistakes — great!"),
    "mistakes_intro_fmt": s("Ошибок: %s. У каждой — разбор, правило и упражнения.", "Mistakes: %s. Each has an analysis, a rule "
                            "and exercises."),
    "repeat_rules": s("План повторения: правила", "Revision plan: rules"),
    # practice and study
    "practice_intro": s("Выберите область программы: задания вариантов и аналогичные упражнения идут вперемешку.",
                        "Choose a syllabus area: variant tasks and analogous exercises are mixed."),
    "study_index_intro": s("Области программы ЦЭ/ЦТ и правила в каждой из них.", "CE/CT syllabus areas and their rules."),
    "study_topic_fmt": s("Изучение: %s", "Study: %s"),
    "study_intro": s("Каждое правило открывается карточкой: формулировка, исключения, бытовое объяснение, примеры, схемы и "
                     "источники.", "Each rule opens a card: formulation, exceptions, everyday explanation, examples, "
                     "diagrams and sources."),
    "study_points": s("Правила области", "Rules of the area"), "study_examples": s("Примеры заданий", "Example tasks"),
    "study_practice": s("Тренировать область", "Practise this area"), "return_to_task": s("Вернуться к заданию", "Back to the task"),
    # rules
    "rules_intro": s("Справочник правил: поиск по названию, формулировке и примерам. Карточка открывается из изучения, "
                     "разбора ошибок и этого экрана.", "Rule reference: search by name, formulation and examples."),
    "search_rule": s("Поиск правила: «тоже», «Н/НН», «тире»…", "Search: «тоже», «Н/НН», «тире»…"),
    "theory_open": s("Открыть правило", "Open the rule"), "rule_statement": s("Правило", "Rule"),
    "rule_exceptions": s("Исключения и границы применения", "Exceptions and limits"),
    "theory_everyday": s("Простыми словами", "In plain words"), "rule_examples": s("Примеры", "Examples"),
    "rule_correct": s("Верно", "Correct"), "rule_wrong": s("Ошибочно → правильно", "Wrong → correct"),
    "rule_steps": s("Как рассуждать", "How to reason"), "theory_visuals": s("Схемы и таблицы", "Diagrams and tables"),
    "rule_sources": s("Нормативные источники", "Normative sources"), "checked_on_fmt": s("сверено %s", "checked %s"),
    "tree_yes": s("Да", "Yes"), "tree_no": s("Нет", "No"),
    "theory_enlarge": s("Увеличить схему", "Enlarge"), "theory_zoom_in": s("Увеличить", "Zoom in"),
    "theory_zoom_out": s("Уменьшить", "Zoom out"), "theory_zoom_reset": s("По размеру", "Fit"),
    "theory_zoom_fmt": s("Масштаб %s", "Zoom %s"), "theory_pan_hint": s("Схему можно двигать пальцем или стрелками.",
                                                                        "Pan the diagram with a finger or the arrow keys."),
    "theory_visual_unavailable": s("Схема недоступна; описание приведено в подписи.", "Diagram unavailable; see the caption."),
    # settings
    "exam_settings": s("Экзамен и цель", "Exam and goal"), "exam_minutes": s("Длительность экзамена, минут", "Exam length, minutes"),
    "theme": s("Оформление", "Appearance"), "theme_system": s("Как в системе", "System"), "theme_light": s("Светлое", "Light"),
    "theme_dark": s("Тёмное", "Dark"), "font_size": s("Размер текста", "Text size"), "font_small": s("Мелкий", "Small"),
    "font_normal": s("Обычный", "Normal"), "font_large": s("Крупный", "Large"), "font_huge": s("Очень крупный", "Extra large"),
    "interface_settings": s("Интерфейс", "Interface"),
    "auto_advance": s("Переходить к следующему заданию после верного ответа", "Go to the next task after a correct answer"),
    "auto_advance_hint": s("Только в тренировке.", "Practice mode only."), "vibration": s("Вибрация", "Vibration"),
    "keep_screen_on": s("Не гасить экран во время теста", "Keep the screen on during a test"),
    "auto_update": s("Обновлять банк автоматически", "Update the bank automatically"),
    "auto_update_hint": s("Только проверенные выпуски этого предмета; статистика не затрагивается.",
                          "Only verified releases of this subject; statistics are never touched."),
    "data_settings": s("Данные", "Data"),
    "data_hint": s("Статистика и настройки хранятся только на этом устройстве, отдельно от других репетиторов.",
                   "Statistics and settings stay on this device, separate from other tutors."),
    "open_data_folder": s("Открыть папку данных", "Open the data folder"), "opened_folder": s("Папка открыта", "Folder opened"),
    "open_folder_failed": s("Не удалось открыть папку", "Could not open the folder"),
    "updates": s("Обновления банка", "Content updates"),
    "updates_channel": s("Канал обновлений — только выпуски «russian-v…» этого репозитория с проверенными контрольными суммами.",
                         "Update channel: only «russian-v…» releases of this repository with verified checksums."),
    "check_updates": s("Проверить обновления", "Check for updates"), "checking_updates": s("Проверка…", "Checking…"),
    "update_uptodate": s("Установлена последняя версия банка.", "The latest content is installed."),
    "update_success_fmt": s("Банк обновлён до %s", "Content updated to %s"),
    "update_failed": s("Не удалось обновить (нет сети или выпуск не прошёл проверку). Работаем на встроенном банке.",
                       "Update failed (offline or the release failed verification). The built-in bank keeps working."),
    "content_version_fmt": s("Версия банка: %s", "Content version: %s"),
    # report
    "export_report": s("Сохранить отчёт", "Save report"), "report_title": s("Отчёт о подготовке: русский язык",
                                                                            "Progress report: Russian"),
    "report_saved": s("Отчёт сохранён", "Report saved"), "report_saved_fmt": s("Отчёт сохранён: %s", "Report saved: %s"),
    "report_failed": s("Не удалось сохранить отчёт", "Could not save the report"),
    "report_rules": s("Правила", "Rules"), "topic": s("Область", "Area"), "rule_col": s("Правило", "Rule"),
    "correct_col": s("Верно", "Correct"), "percent_col": s("%", "%"), "tasks_col": s("Заданий", "Tasks"),
    "variant_col": s("Вариант", "Variant"), "date_col": s("Дата", "Date"), "time_col": s("Время", "Time"),
}


def payload() -> dict:
    for key, entry in STRINGS.items():
        if set(entry) != {"ru", "en"} or not all(isinstance(entry[lang], str) and entry[lang].strip() for lang in entry):
            raise ValueError(f"ui string {key} needs RU and EN")
        if entry["ru"].count("%s") != entry["en"].count("%s"):
            raise ValueError(f"ui string {key}: placeholders differ between RU and EN")
        if "%s" in entry["ru"] and not key.endswith("_fmt") and key != "resume_text":
            raise ValueError(f"ui string {key} takes arguments, so its key must end with _fmt")
    return dict(STRINGS)

package by.ziv.ctenglish

import org.json.JSONObject
import java.text.Normalizer

/**
 * Проверка английского ответа — точный порт `english/content_src/policy.py`.
 *
 * Три реализации обязаны совпадать до буквы:
 *
 * 1. `english/content_src/policy.py` — эталон: им проверяется авторский банк
 *    при сборке контента;
 * 2. `english/webapp/core.js` → `CT.answer` — проверка ответа ученика в WebView
 *    (и в Android, и в Windows-сборке);
 * 3. этот файл — проверка ответа на устройстве в нативной части.
 *
 * Общие векторы (`assets/content/answer_vectors.json`, он же
 * `app/src/test/resources/answer_vectors.json`) прогоняются всеми тремя, поэтому
 * «Python принял, а телефон нет» технически невозможно.
 *
 * Задание само объявляет свою политику проверки (`policy`), потому что в
 * английских упражнениях пробел, дефис, апостроф, артикль и регистр часто и есть
 * ответ:
 *
 * * `case` — `insensitive` (по умолчанию) | `sensitive`;
 * * `article` — `checked` (по умолчанию) | `ignored`;
 * * `apostrophe` — `ignore` (по умолчанию) | `required`;
 * * `hyphen` — `significant` (по умолчанию) | `ignore`;
 * * `space` — `significant` (по умолчанию) | `collapse`;
 * * `stress` — `significant` (по умолчанию) | `ignore`;
 * * `empty` — `reject` (по умолчанию) | `accept` (верный ответ — пустое поле).
 *
 * Причина отказа — часть контракта: `empty`, `article`, `case`, `apostrophe`,
 * `hyphen`, `space`, `stress`, `near`, `exact` — интерфейс показывает по ней
 * объяснение и ведёт к правилу для разбора.
 */
object AnswerChecker {

    const val NOTHING = "—"

    /** Значения политики по умолчанию — как в policy.py. */
    val DEFAULT_POLICY: Map<String, String> = linkedMapOf(
        "case" to "insensitive",
        "article" to "checked",
        "apostrophe" to "ignore",
        "hyphen" to "significant",
        "space" to "significant",
        "stress" to "significant",
        "empty" to "reject",
    )

    /** Порядок ключей одинаков во всех трёх реализациях (для читаемых diff'ов). */
    val POLICY_KEYS: List<String> = listOf("case", "article", "apostrophe", "hyphen", "space", "stress", "empty")

    val ALLOWED: Map<String, List<String>> = mapOf(
        "case" to listOf("insensitive", "sensitive"),
        "article" to listOf("checked", "ignored"),
        "apostrophe" to listOf("ignore", "required"),
        "hyphen" to listOf("significant", "ignore"),
        "space" to listOf("significant", "collapse"),
        "stress" to listOf("significant", "ignore"),
        "empty" to listOf("reject", "accept"),
    )

    private val APOSTROPHES = Regex("[\\u2019\\u02bc\\u2018'`]")
    private val DASHES = Regex("[\\u2010\\u2011\\u2012\\u2013\\u2014\\u2212]")
    private val ARTICLES = setOf("a", "an", "the")
    private val COMBINING = Regex("[\\u0300-\\u036f\\u00b4\\u02ca\\u02c7\\u02d8]")

    /** Вердикт: принят ли ответ и (если нет) почему. */
    data class Verdict(val ok: Boolean, val reason: String) {
        companion object {
            val OK = Verdict(true, "ok")
        }
    }

    /** Политика задания с подставленными значениями по умолчанию. */
    fun policyFor(task: JSONObject): Map<String, String> {
        val policy = LinkedHashMap(DEFAULT_POLICY)
        val declared = task.optJSONObject("policy") ?: JSONObject()
        for (key in POLICY_KEYS) {
            if (!declared.has(key)) continue
            val value = declared.optString(key, "")
            require(ALLOWED.getValue(key).contains(value)) {
                "политика $key=$value недопустима для задания ${task.optString("id")}"
            }
            policy[key] = value
        }
        for (key in declared.keys()) {
            require(POLICY_KEYS.contains(key)) {
                "неизвестный ключ политики: $key (задание ${task.optString("id")})"
            }
        }
        return policy
    }

    /** Привести ответ к сравнимому виду только по разрешённым правилам. */
    fun normalize(text: String?, policy: Map<String, String>): String {
        var value = (text ?: "").replace('\u00a0', ' ')
        value = if (policy["hyphen"] == "significant") DASHES.replace(value, "-") else DASHES.replace(value, "")
        if (policy["hyphen"] != "significant") value = value.replace("-", "")
        value = if (policy["apostrophe"] == "required") APOSTROPHES.replace(value, "'")
        else APOSTROPHES.replace(value, "")
        if (policy["stress"] == "ignore") value = withoutDiacritics(value)
        if (policy["space"] == "collapse") value = value.replace(Regex("\\s+"), " ")
        value = value.trim()
        // регистр снимается ДО артиклей: иначе «The» не распознаётся как артикль
        if (policy["case"] == "insensitive") value = value.lowercase()
        if (policy["article"] == "ignored") {
            // удаление артикля может оставить лишний пробел — схлопываем всегда:
            // это следствие нормализации, а не расстановка пробелов учеником
            value = dropArticles(value).replace(Regex("\\s+"), " ").trim()
        }
        return value
    }

    /**
     * Сравнить ввод с допустимыми ответами задания.
     *
     * Порядок причин отказа — часть контракта (его повторяют Python и JavaScript):
     * empty → case → apostrophe → hyphen → space → article → stress → near → exact.
     */
    fun check(task: JSONObject, typed: String?): Verdict {
        val policy = policyFor(task)
        val accepted = mutableListOf<String>()
        val answer = task.optJSONObject("answer")?.optString("value", "") ?: ""
        if (answer.isNotEmpty()) accepted.add(answer)
        val alternatives = task.optJSONArray("accepted")
        if (alternatives != null) {
            for (index in 0 until alternatives.length()) {
                val value = alternatives.optString(index, "")
                if (value.isNotEmpty()) accepted.add(value)
            }
        }
        require(accepted.isNotEmpty()) { "у задания ${task.optString("id")} нет допустимого ответа" }

        val gotRaw = (typed ?: "").trim()
        val got = normalize(gotRaw, policy)
        if (got.isEmpty()) {
            // «ничего не нужно» — законный ответ задания, объявившего empty: accept
            return if (policy["empty"] == "accept") Verdict(true, "ok")
            else Verdict(false, "empty")
        }
        // задание, где пропуск должен остаться пустым: любое слово — уже ошибка
        if (accepted.size == 1 && accepted[0] == NOTHING) {
            val tokens = tokens(got)
            val reason = if (withoutArticles(tokens) != tokens) "article" else "exact"
            return Verdict(false, reason)
        }

        val norms = accepted.map { normalize(it, policy) }
        if (norms.contains(got)) return Verdict(true, "ok")

        for (index in accepted.indices) {
            val norm = norms[index]
            if (policy["case"] == "sensitive" && got != norm && got.lowercase() == norm.lowercase()) {
                return Verdict(false, "case")
            }
            if (policy["apostrophe"] == "required" && got.replace("'", "") == norm.replace("'", "")) {
                return Verdict(false, "apostrophe")
            }
            if (policy["hyphen"] == "significant" &&
                (norm.replace("-", " ") == got || norm.replace("-", "") == got)
            ) {
                return Verdict(false, "hyphen")
            }
            if (policy["space"] == "significant" && collapse(got) == collapse(norm)) {
                return Verdict(false, "space")
            }
            if (withoutArticles(tokens(norm)) == withoutArticles(tokens(got)) && got != norm) {
                return Verdict(false, "article")
            }
            if (policy["stress"] == "significant" && withoutDiacritics(got) == withoutDiacritics(norm)) {
                return Verdict(false, "stress")
            }
            if (near(got, norm)) return Verdict(false, "near")
        }
        return Verdict(false, "exact")
    }

    /** Короткая человеческая расшифровка политики (для интерфейса и отчёта). */
    fun describePolicy(policy: Map<String, String>): String {
        val parts = mutableListOf<String>()
        if (policy["case"] == "sensitive") parts.add("регистр букв важен")
        if (policy["article"] == "ignored") parts.add("артикль не проверяется")
        if (policy["apostrophe"] == "required") parts.add("апостроф обязателен")
        if (policy["hyphen"] == "ignore") parts.add("дефис не проверяется")
        if (policy["space"] == "collapse") parts.add("пробелы можно схлопывать")
        if (policy["stress"] == "ignore") parts.add("диакритика не проверяется")
        if (policy["empty"] == "accept") parts.add("если ничего не нужно, поле остаётся пустым")
        return if (parts.isEmpty()) "точное совпадение" else parts.joinToString("; ")
    }

    private fun withoutDiacritics(value: String): String =
        COMBINING.replace(Normalizer.normalize(value, Normalizer.Form.NFD), "")

    private fun collapse(value: String): String = value.replace(" ", "").replace("\t", "")

    private fun tokens(value: String): List<String> =
        value.split(Regex("[ \t]+")).filter { it.isNotEmpty() }

    private fun withoutArticles(tokens: List<String>): List<String> =
        tokens.filter { !ARTICLES.contains(it) }

    private fun dropArticles(value: String): String =
        Regex("(^|\\s)(?:a|an|the)(?=\\s|$)").replace(value) { match -> match.groupValues[1] }

    /** «Почти совпало»: другая форма слова или лишний/пропущенный знак. */
    private fun near(got: String, expected: String): Boolean {
        val a = letters(got)
        val b = letters(expected)
        if (a.isEmpty() || b.isEmpty()) return false
        if (a.contains(b) || b.contains(a)) return true
        var common = 0
        for (index in 0 until minOf(a.length, b.length)) {
            if (a[index] != b[index]) break
            common++
        }
        return common >= 3 && kotlin.math.abs(a.length - b.length) <= 2
    }

    private fun letters(value: String): String =
        value.lowercase().replace(Regex("[^a-z0-9]"), "")
}

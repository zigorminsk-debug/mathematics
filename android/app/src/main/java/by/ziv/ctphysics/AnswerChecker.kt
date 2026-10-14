package by.ziv.ctphysics

import java.util.Locale
import org.json.JSONArray
import org.json.JSONObject

/**
 * Проверка ответа на задание по физике — Kotlin-версия того же алгоритма, что
 * выполняют Python (`content_src/quantities.py`) при авторской сборке банка и
 * JavaScript (`webapp/core.js` → `CT.answer`) в интерфейсе.
 *
 * Ответ на задание части B — это **физическая величина**: число и, если нужно,
 * единица. Поэтому проверка состоит из шагов:
 *
 * 1. разбор записи ученика на число и единицу (`splitNumberUnit`);
 * 2. разбор единицы по таблице `UnitTable.JSON` (генерируется из Python);
 * 3. сравнение размерности с ожидаемой (`dimension`), причины отказа —
 *    `dimension`, `unit`, `missing_unit`;
 * 4. сравнение значения с допуском: `tolerance` (абсолютный, относительный или
 *    по границе округления `rounding`), плюс список `accept`;
 * 5. для части A (выбор варианта) — сравнение канонических записей, число без
 *    единицы правильным не считается.
 *
 * Примеры из задания: `36 км/ч` и `10 м/с` — один и тот же ответ;
 * `10 Н` вместо `10 кг` — ошибка размерности, а не «неточность».
 *
 * Результат проверки — пара «верно/нет» и причина отказа, ровно как в JS
 * (`grade`), чтобы Android-тесты сверяли вердикты всех трёх реализаций на общих
 * векторах `answer_vectors.json` и `tests/unit_vectors.json`.
 */
object AnswerChecker {

    private val MINUS = Regex("[\\u2212\\u2013\\u2014\\u2015]")
    private val SUPERSCRIPT = mapOf(
        '\u2070' to '0', '\u00b9' to '1', '\u00b2' to '2', '\u00b3' to '3', '\u2074' to '4',
        '\u2075' to '5', '\u2076' to '6', '\u2077' to '7', '\u2078' to '8', '\u2079' to '9',
        '\u207b' to '-',
    )
    private val SUPERSCRIPT_RUN = Regex("[\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079\u207b]+")
    private val TEN_WITH_SUPERSCRIPT =
        Regex("10([\\u2070\\u00b9\\u00b2\\u00b3\\u2074\\u2075\\u2076\\u2077\\u2078\\u2079\\u207b]+)")
    private val POWER_OF_TEN = Regex("^10\\^(?:\\(([+-]?[0-9]+)\\)|([+-]?[0-9]+))$")
    private val PLAIN_NUMBER = Regex("^[-+]?[0-9]+(?:\\.[0-9]+)?$")
    private val FALLBACK_SPLIT = Regex("^([^A-Za-z\\u0410-\\u044f\\u0401\\u0451\\u00b5\\u03bc\\u00b0]+)\\s*(.*)$")
    private val FRACTION =
        Regex("^([+-]?[0-9]+(?:[.,][0-9]+)?)/([+-]?[0-9]+(?:[.,][0-9]+)?)$")
    private val SCIENTIFIC =
        Regex("^([+-]?[0-9]+(?:[.,][0-9]+)?)(?:\\*10(?:\\^|\\*\\*)?\\(?([+-]?[0-9]+)\\)?|e([+-]?[0-9]+))$")

    /** Разобранная единица: показатели степеней, множитель к СИ и смещение. */
    data class Unit(
        val symbol: String,
        val ru: String,
        val en: String,
        val dim: List<Int>,
        val factor: Double,
        val offset: Double,
        val prefixable: Boolean,
    )

    /** Результат проверки ответа ученика. */
    data class Verdict(val ok: Boolean, val reason: String) {
        companion object {
            val EMPTY = Verdict(false, "empty")
            val VALUE = Verdict(false, "value")
            val DIMENSION = Verdict(false, "dimension")
            val UNIT = Verdict(false, "unit")
            val MISSING_UNIT = Verdict(false, "missing_unit")
            val OK = Verdict(true, "")
        }
    }

    private val table: JSONObject by lazy { JSONObject(UnitTable.JSON) }
    private val units: List<JSONObject> by lazy {
        val array = table.getJSONArray("units")
        (0 until array.length()).map { array.getJSONObject(it) }
    }
    private val prefixes: List<JSONObject> by lazy {
        val array = table.getJSONArray("prefixes")
        (0 until array.length()).map { array.getJSONObject(it) }
    }
    private val byExact: Map<String, JSONObject> by lazy {
        val map = LinkedHashMap<String, JSONObject>()
        for (unit in units) {
            for (name in names(unit)) {
                if (!map.containsKey(name.trim())) map[name.trim()] = unit
            }
        }
        map
    }
    private val byAlias: Map<String, JSONObject> by lazy {
        val map = LinkedHashMap<String, JSONObject>()
        for (unit in units) {
            for (name in names(unit)) {
                val trimmed = name.trim()
                // однобуквенные латинские обозначения не сравниваем без регистра:
                // «J» — джоуль по обозначению, «j» — не единица вовсе
                if (trimmed.length == 1 && trimmed[0].isLetter() && trimmed[0].code < 128) continue
                val key = aliasKey(trimmed)
                if (key.isNotEmpty() && !map.containsKey(key)) map[key] = unit
            }
        }
        map
    }

    /* ------------------------------------------------------------ единицы --- */

    private fun names(unit: JSONObject): List<String> {
        val list = mutableListOf<String>()
        for (key in listOf("s", "ru", "en")) {
            val value = unit.optString(key)
            if (value.isNotEmpty()) list.add(value)
        }
        unit.optJSONArray("a")?.let { array ->
            for (index in 0 until array.length()) list.add(array.optString(index))
        }
        return list
    }

    private fun aliasKey(name: String): String =
        name.trim().lowercase(Locale.ROOT)
            .replace(" ", "").replace("^", "").replace("·", "").replace("*", "")

    /** Единица по точному обозначению или синониму, без приставок. */
    private fun baseLookup(name: String): JSONObject? {
        val trimmed = name.trim()
        if (trimmed.isEmpty()) return null
        byExact[trimmed]?.let { return it }
        byAlias[aliasKey(trimmed)]?.let { return it }
        if (trimmed.length == 1 && trimmed[0].lowercaseChar() in 'a'..'z') {
            // «н»/«n» без регистра: n → Н; «t» остаётся тонной, «T» — тесла
            byExact[trimmed.uppercase(Locale.ROOT)]?.let { return it }
        }
        return null
    }

    private fun unitFactor(unit: JSONObject): Double = unit.optString("f", "1").toDoubleOrNull() ?: 1.0

    private fun unitOffset(unit: JSONObject): Double = unit.optDouble("o", 0.0)

    private fun dimOf(unit: JSONObject): List<Int> {
        val array = unit.optJSONArray("dim") ?: return List(7) { 0 }
        return (0 until array.length()).map { array.optInt(it) }
    }

    private data class Prefixed(
        val symbol: String,
        val ru: String,
        val en: String,
        val dim: List<Int>,
        val factor: Double,
        val offset: Double,
    )

    /** «кило + ватт»: только приставка + единица, не «мкг» (это не микрокилограмм). */
    private fun prefixed(name: String): Prefixed? {
        for (prefix in prefixes) {
            val ru = prefix.optString("ru")
            val latin = prefix.optString("la")
            val factor = prefix.optString("f").toDoubleOrNull() ?: continue
            for (prefixText in setOf(ru, latin)) {
                if (prefixText.isEmpty() || !name.startsWith(prefixText) ||
                    name.length == prefixText.length) continue
                val base = baseLookup(name.substring(prefixText.length)) ?: continue
                if (!base.optBoolean("p", false) || unitOffset(base) != 0.0) continue
                if (base.optString("s") == "kg") continue
                return Prefixed(
                    symbol = latin + base.optString("s"),
                    ru = ru + base.optString("ru"),
                    en = latin + base.optString("en"),
                    dim = dimOf(base),
                    factor = factor * unitFactor(base),
                    offset = 0.0,
                )
            }
        }
        return null
    }

    /** Полная единица: сначала точное обозначение, потом «приставка + единица». */
    private fun lookupUnit(name: String): Unit? {
        baseLookup(name)?.let { base ->
            return Unit(base.optString("s"), base.optString("ru"), base.optString("en"),
                dimOf(base), unitFactor(base), unitOffset(base), base.optBoolean("p", false))
        }
        prefixed(name)?.let { return Unit(it.symbol, it.ru, it.en, it.dim, it.factor, it.offset, true) }
        return null
    }

    /** Разобрать единицу («м/с²», «кг·м/с²», «36 км/ч» → «км/ч»). Ошибка → null. */
    fun unitOf(text: String?): Unit? {
        val raw = (text ?: "").trim()
        if (raw.isEmpty()) return null
        val expression = toExpression(raw)
        if (expression.isEmpty()) return null
        if (expression == "1") {
            return Unit("1", "", "", List(7) { 0 }, 1.0, 0.0, false)
        }
        val tokens = tokenizeUnits(expression) ?: return null
        val parsed = try {
            val parser = UnitParser(tokens)
            val result = parser.parse()
            if (result == null) null else result
        } catch (error: Exception) {
            null
        } ?: return null
        if (tokens.size == 1) {
            lookupUnit(tokens[0])?.let { return it }
        }
        return Unit(raw, raw, raw, parsed.first, parsed.second, parsed.third, false)
    }

    private fun toExpression(text: String): String {
        val builder = StringBuilder()
        var index = 0
        while (index < text.length) {
            val character = text[index]
            if (character in SUPERSCRIPT) {
                builder.append('^').append('(')
                while (index < text.length && text[index] in SUPERSCRIPT) {
                    builder.append(SUPERSCRIPT[text[index]]!!)
                    index++
                }
                builder.append(')')
                continue
            }
            when (character) {
                '\u00b7', '\u2219', '\u00d7', '\u22c5' -> builder.append('*')
                else -> builder.append(character)
            }
            index++
        }
        return builder.toString().filter { !it.isWhitespace() && it != '\u00a0' }
    }

    private fun isUnitCharacter(character: Char): Boolean =
        character.isLetterOrDigit() || character in "._\u00b0\u03a9\u00b5\u03bc"

    /** Токенизатор единиц: Python `_tokenize` (буквы, цифры, «.», операторы). */
    private fun tokenizeUnits(expression: String): List<String>? {
        val tokens = mutableListOf<String>()
        var index = 0
        while (index < expression.length) {
            val character = expression[index]
            if (character in "*/^()") {
                tokens.add(character.toString())
                index++
                continue
            }
            if (character.isDigit() || character == '.') {
                var end = index
                while (end < expression.length && (expression[end].isDigit() || expression[end] == '.')) end++
                tokens.add(expression.substring(index, end))
                index = end
                continue
            }
            if (character == '-') {
                tokens.add("-")
                index++
                continue
            }
            var end = index
            while (end < expression.length && isUnitCharacter(expression[end])) end++
            if (end == index) return null
            tokens.add(expression.substring(index, end))
            index = end
        }
        return if (tokens.isEmpty()) null else tokens
    }

    /** Разбор единицы: произведение, деление, степени, «1» как безразмерная. */
    private class UnitParser(private val tokens: List<String>) {

        private var position = 0

        /** (размерность, множитель, смещение) или null, если запись неверна. */
        fun parse(): Triple<List<Int>, Double, Double>? {
            val node = expression() ?: return null
            return if (position != tokens.size) null else node
        }

        private fun peek(): String? = if (position < tokens.size) tokens[position] else null

        private fun next(): String? = if (position < tokens.size) tokens[position++] else null

        private fun expression(): Triple<List<Int>, Double, Double>? {
            var node = term() ?: return null
            while (true) {
                val token = peek()
                if (token != "*" && token != "/") return node
                next()
                val right = term() ?: return null
                node = combine(node, right, token == "*")
            }
        }

        private fun term(): Triple<List<Int>, Double, Double>? {
            var node = atom() ?: return null
            if (peek() == "^") {
                next()
                var wrapped = false
                if (peek() == "(") {
                    next()
                    wrapped = true
                }
                var sign = 1
                if (peek() == "-") {
                    next()
                    sign = -1
                } else if (peek() == "+") {
                    next()
                }
                val exponent = next() ?: return null
                val power = exponent.toIntOrNull() ?: return null
                if (wrapped && next() != ")") return null
                val value = sign * power
                node = Triple(node.first.map { it * value },
                    Math.pow(node.second, value.toDouble()),
                    if (value == 1) node.third else 0.0)
            }
            return node
        }

        private fun atom(): Triple<List<Int>, Double, Double>? {
            val token = next() ?: return null
            if (token == "(") {
                val inner = expression() ?: return null
                return if (next() == ")") inner else null
            }
            if (token == "1") return Triple(List(7) { 0 }, 1.0, 0.0)
            if (token.isNotEmpty() && token.all { it.isDigit() || it == '.' }) return null
            val unit = lookupUnit(token) ?: return null
            return Triple(unit.dim, unit.factor, unit.offset)
        }

        private fun combine(
            left: Triple<List<Int>, Double, Double>,
            right: Triple<List<Int>, Double, Double>,
            multiply: Boolean,
        ): Triple<List<Int>, Double, Double> {
            val dim = left.first.indices.map { index ->
                if (multiply) left.first[index] + right.first[index]
                else left.first[index] - right.first[index]
            }
            val factor = if (multiply) left.second * right.second else left.second / right.second
            return Triple(dim, factor, 0.0)
        }
    }

    /* ------------------------------------------------------------- числа ---- */

    /** «12», «12,5», «−3,5», «1/2», «1e-3», «1,5·10⁻³», «3·10⁵» → Double | null. */
    fun number(text: String?): Double? {
        if (text == null) return null
        var s = text.trim()
        if (s.isEmpty()) return null
        s = s.replace("\u00a0", "").replace(" ", "")
        s = MINUS.replace(s, "-")
        // «10⁻³» — степень десяти: надстрочник имеет смысл только после «10»
        s = TEN_WITH_SUPERSCRIPT.replace(s) { match ->
            "10^(" + match.groupValues[1].map { SUPERSCRIPT[it] ?: it }.joinToString("") + ")"
        }
        s = s.replace("\u22c5", "*").replace("\u2219", "*")
            .replace("\u00d7", "*").replace("·", "*")
        SCIENTIFIC.find(s)?.let { match ->
            val mantissa = match.groupValues[1].replace(',', '.').toDoubleOrNull()
            val exponent = (match.groupValues[2].ifEmpty { match.groupValues[3] }).toDoubleOrNull()
            if (mantissa != null && exponent != null) return mantissa * Math.pow(10.0, exponent)
            return null
        }
        POWER_OF_TEN.find(s)?.let { match ->
            return Math.pow(10.0, (match.groupValues[1].ifEmpty { match.groupValues[2] }).toDouble())
        }
        FRACTION.find(s)?.let { match ->
            // обыкновенная дробь: «1/2» = 0,5; деление на ноль — не число
            val numerator = match.groupValues[1].replace(',', '.').toDoubleOrNull()
            val denominator = match.groupValues[2].replace(',', '.').toDoubleOrNull()
            if (numerator == null || denominator == null || denominator == 0.0) return null
            return numerator / denominator
        }
        val plain = s.replace(',', '.')
        if (!PLAIN_NUMBER.matches(plain)) return null
        return plain.toDoubleOrNull()
    }

    /** Число и единица отдельно: «10 м/с» → (10, «м/с»), «0,5» → (0.5, null).
     *
     * Разбор идёт справа налево: берётся самая длинная числовая часть, а всё,
     * что за ней, обязано оказаться единицей. Так «0,05» не превращается в
     * «0» плюс «,05», а «10 000 Па» — в «10» плюс «000 Па».
     */
    fun splitNumberUnit(text: String?): Pair<Double?, String?> {
        val raw = (text ?: "").trim()
        if (raw.isEmpty()) return null to null
        for (index in raw.length downTo 1) {
            val head = raw.substring(0, index).trim()
            val tail = raw.substring(index).trim()
            if (head.isEmpty()) continue
            val value = number(head) ?: continue
            if (tail.isEmpty() || unitOf(tail) != null) return value to tail.ifEmpty { null }
        }
        val fallback = FALLBACK_SPLIT.find(raw)
        if (fallback != null) {
            val value = number(fallback.groupValues[1].trim())
            if (value != null && fallback.groupValues[2].trim().isNotEmpty()) {
                return value to fallback.groupValues[2].trim()
            }
        }
        return null to null
    }

    /* ------------------------------------------------- проверка ответа ----- */

    /** Канонические записи правильного ответа: `accept` и сам ответ из `spec`. */
    private fun accepted(spec: JSONObject): List<String> {
        val list = mutableListOf<String>()
        fun add(value: String?) {
            val normalized = normalize(value)
            if (normalized.isNotEmpty() && !list.contains(normalized)) list.add(normalized)
        }
        spec.optJSONArray("accept")?.let { array ->
            for (index in 0 until array.length()) add(array.optString(index))
        }
        val answer = spec.opt("answerValue")
        if (answer != null && answer != JSONObject.NULL) add(answer.toString())
        val answerObject = spec.optJSONObject("answer")
        if (answerObject != null) {
            add(answerObject.optString("ru"))
            add(answerObject.optString("en"))
        }
        return list
    }

    /** Допуск по `tolerance` / `rounding` (как в JS и Python). */
    private fun tolerance(spec: JSONObject, expected: Double): Double {
        val tolerance = spec.optJSONObject("tolerance")
        if (tolerance != null) {
            val value = tolerance.optString("value").toDoubleOrNull() ?: 0.0
            return when (tolerance.optString("kind", "absolute")) {
                "relative" -> Math.abs(expected) * value
                "rounding" -> value
                else -> value
            }
        }
        val rounding = spec.opt("rounding")
        if (rounding != null && rounding != JSONObject.NULL) {
            val digits = rounding.toString().toIntOrNull()
            if (digits != null) {
                // граница округления: |ответ − точное| ≤ 5·10^-(знаков+1)
                return 5 * Math.pow(10.0, -(digits + 1).toDouble())
            }
        }
        return 0.0
    }

    private fun expectedValue(spec: JSONObject): Double? =
        number(spec.opt("answerValue")?.toString())

    private fun expectedDimension(spec: JSONObject): List<Int>? {
        // как в JS: подпись размерности главнее единицы записи ответа —
        // спека «dimension: m» обязана отвергнуть ответ в м/с
        val dimension = spec.optString("dimension")
        if (dimension.isNotEmpty()) {
            unitOf(dimension)?.let { return it.dim }
        }
        val unit = spec.optString("unit")
        if (unit.isEmpty()) return null
        return unitOf(unit)?.dim
    }

    private fun sameDim(left: List<Int>, right: List<Int>): Boolean =
        left.size == right.size && left.indices.all { left[it] == right[it] }

    /** Проверить ответ ученика против спецификации задания. */
    fun grade(userAnswer: String?, spec: JSONObject): Verdict {
        if (normalize(userAnswer).isEmpty()) return Verdict.EMPTY
        val answerType = spec.optString("answerType", "quantity")
        val acceptedList = accepted(spec)

        if (answerType == "choice" || spec.optBoolean("choiceOnly", false)) {
            val user = normalize(userAnswer)
            return if (acceptedList.contains(user)) Verdict.OK else Verdict.VALUE
        }

        val (value, unitText) = splitNumberUnit(userAnswer)
        // как в Python/JS: неразобранная запись — это «пусто», а не «неверное
        // значение»: ученик либо ничего осмысленного не ввёл, либо число
        // записано так, что приложение его не поняло
        if (value == null) return Verdict.EMPTY
        val expected = expectedValue(spec) ?: return Verdict.VALUE

        val parsed = if (unitText == null) null else unitOf(unitText)
        if (unitText != null && parsed == null) return Verdict.UNIT

        val expectedDimension = expectedDimension(spec)
        var candidate = value
        if (parsed != null) {
            if (expectedDimension != null && !sameDim(parsed.dim, expectedDimension)) {
                return Verdict.DIMENSION
            }
            // к СИ: 36 км/ч → 10 м/с, °C → К
            val expectedUnit = unitOf(spec.optString("unit"))
            if (expectedUnit != null && !sameDim(parsed.dim, expectedUnit.dim)) {
                return Verdict.DIMENSION
            }
            val expectedFactor = expectedUnit?.factor ?: 1.0
            candidate = (value * parsed.factor + parsed.offset - (expectedUnit?.offset ?: 0.0)) /
                expectedFactor
        } else {
            val policy = spec.optString("unitPolicy", "named")
            if (policy == "required") return Verdict.MISSING_UNIT
        }

        val allowed = tolerance(spec, expected)
        if (Math.abs(candidate - expected) <= allowed + 1e-9 * Math.abs(expected)) return Verdict.OK

        for (variant in acceptedList) {
            val other = number(variant) ?: continue
            if (Math.abs(candidate - other) <= tolerance(spec, other) +
                1e-9 * Math.abs(other)) return Verdict.OK
        }
        return Verdict.VALUE
    }

    /** Удобная обёртка: верно ли отвечено (задания банка хранят `spec`). */
    fun check(userAnswer: String?, task: JSONObject): Boolean {
        val spec = task.optJSONObject("spec") ?: task
        return grade(userAnswer, spec).ok
    }

    /** Каноническая запись: регистр, запятая, пробелы, «ответ:», буква варианта.
     *
     * Ровно то же преобразование делают Python (`_normalize_choice`) и
     * JavaScript (`A.normalize`): «б) 2,5 м» и «ответ: 2.5м» — одна и та же
     * запись, иначе выбор варианта в части A зависел бы от реализации.
     */
    fun normalize(value: String?): String {
        if (value.isNullOrEmpty()) return ""
        var text = value.trim().lowercase(Locale.ROOT)
        text = text.replace("\u00a0", " ")
        text = MINUS.replace(text, "-")
        text = text.replace("\u00d7", "*").replace("\u22c5", "*").replace("·", "*")
        text = text.replace("х", "x")
        text = Regex("^(ответ|answer)\\s*[:.=]?\\s*").replace(text, "")
        text = Regex("^\\s*[a-zа-я]\\s*[).:]\\s*").replace(text, "")
        text = text.replace(',', '.')
        text = text.filter { !it.isWhitespace() }
        if (text.endsWith(".")) text = text.dropLast(1)
        return text
    }

    /** Число-ответ «как есть» — только значение, без единицы. */
    fun value(text: String?): Double? = splitNumberUnit(text).first

    /** Единица ответа в виде канонического обозначения (для статистики). */
    fun unitSymbol(text: String?): String? {
        val raw = (text ?: "").trim()
        if (raw.isEmpty()) return null
        return unitOf(raw)?.symbol
    }

    /** Все обозначения единиц: используется тестами для самопроверки таблицы. */
    fun unitCount(): Int = units.size

    /** Разобранные единицы из `spec` — например, для подсказок в интерфейсе. */
    fun dimensionSignature(dim: List<Int>): String =
        JSONArray(dim).toString()
}

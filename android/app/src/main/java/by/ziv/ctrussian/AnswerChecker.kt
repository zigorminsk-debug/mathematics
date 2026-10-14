package by.ziv.ctrussian

import org.json.JSONArray
import org.json.JSONObject
import java.text.Normalizer

/**
 * Kotlin port of the subject answer checker (content_src/checker.py and
 * webapp/core.js implement the same contract; AnswerCheckerTest grades the
 * shared vectors with all three).
 *
 * Nothing is removed implicitly: a space, a hyphen, ё, a capital letter or a
 * stress mark is often the answer itself. Each task carries an explicit check
 * object with its type, order and normalisation policy.
 */
object AnswerChecker {
    const val WHITESPACE = "\t\n\u000b\u000c\r \u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005" +
        "\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000"
    private const val VOWELS = "аеёиоуыэюя"
    private const val ACUTE = '\u0301'
    private const val GRAVE = '\u0300'
    private val DIGITS = Regex("[0-9]+")
    private val SEPARATORS = Regex("[ ,;]+")
    private val MATCH_SHAPE = Regex("(?:[А-ЯЁ][0-9]{1,2})+")
    private val MATCH_PAIR = Regex("([А-ЯЁ])([0-9]{1,2})")

    fun nfc(text: String): String = Normalizer.normalize(text, Normalizer.Form.NFC)

    /** Trim the ends; a run of whitespace becomes ONE space (a significant space is never deleted). */
    fun squeeze(text: String): String {
        val out = StringBuilder()
        var pending = false
        for (ch in text) {
            if (WHITESPACE.indexOf(ch) >= 0) {
                pending = true
                continue
            }
            if (pending && out.isNotEmpty()) out.append(' ')
            pending = false
            out.append(ch)
        }
        return out.toString()
    }

    private fun number(token: String): Int? {
        if (!DIGITS.matches(token) || (token.length > 1 && token[0] == '0')) return null
        return token.toIntOrNull()
    }

    /** Numbers 1..max in input order, or null; duplicates are invalid, never de-duplicated. */
    fun parseNumbers(raw: String, max: Int): List<Int>? {
        val text = squeeze(nfc(raw))
        if (text.isEmpty()) return null
        var tokens = text.split(SEPARATORS).filter { it.isNotEmpty() }
        if (tokens.isEmpty()) return null
        if (tokens.size == 1 && max <= 9 && tokens[0].length > 1) {
            if (!DIGITS.matches(tokens[0])) return null
            tokens = tokens[0].map { it.toString() }
        }
        val values = ArrayList<Int>()
        for (token in tokens) {
            if (max <= 9 && token.length != 1) return null
            val value = number(token) ?: return null
            if (value < 1 || value > max || values.contains(value)) return null
            values.add(value)
        }
        return values
    }

    fun foldWord(text: String, spec: JSONObject): String {
        var value = nfc(text)
        if (spec.optString("hyphen") == "typographic") value = value.replace('\u2010', '-').replace('\u2011', '-')
        value = squeeze(value)
        if (spec.optString("case") == "insensitive") value = value.lowercase()
        if (spec.optString("yo") == "e-equals-yo") value = value.replace('ё', 'е').replace('Ё', 'Е')
        return value
    }

    fun parseStress(raw: String, word: String): Int? {
        val text = squeeze(nfc(raw))
        if (text.isEmpty() || text.contains(' ') || text.indexOf(GRAVE) >= 0) return null
        val marks = text.count { it == ACUTE }
        if (marks > 1) return null
        if (marks == 1) {
            val position = text.indexOf(ACUTE) - 1
            val base = text.replace(ACUTE.toString(), "")
            if (position < 0 || base.lowercase() != word || VOWELS.indexOf(base[position].lowercaseChar()) < 0) return null
            return position
        }
        val capitals = text.indices.filter { text[it] != text[it].lowercaseChar() }
        if (capitals.size != 1) return null
        val position = capitals[0]
        if (text.lowercase() != word || VOWELS.indexOf(text[position].lowercaseChar()) < 0) return null
        return position
    }

    fun parseMatch(raw: String, labels: List<String>, right: Int): Map<String, Int>? {
        var text = squeeze(nfc(raw)).uppercase()
        for (separator in listOf(" ", ",", ";", "-", ":")) text = text.replace(separator, "")
        if (text.isEmpty() || !MATCH_SHAPE.matches(text)) return null
        val pairs = LinkedHashMap<String, Int>()
        for (found in MATCH_PAIR.findAll(text)) {
            val label = found.groupValues[1]
            val value = number(found.groupValues[2]) ?: return null
            if (label !in labels || pairs.containsKey(label) || value < 1 || value > right) return null
            pairs[label] = value
        }
        return if (pairs.keys == labels.toSet()) pairs else null
    }

    private fun ints(array: JSONArray?): List<Int> =
        if (array == null) emptyList() else (0 until array.length()).map { array.getInt(it) }

    private fun strings(array: JSONArray?): List<String> =
        if (array == null) emptyList() else (0 until array.length()).map { array.getString(it) }

    /** Grade one answer against a check object; never throws for user input, unknown types fail closed. */
    fun check(user: String?, spec: JSONObject): Boolean = try {
        grade(user ?: "", spec)
    } catch (error: org.json.JSONException) {
        false
    }

    private fun grade(raw: String, spec: JSONObject): Boolean {
        return when (spec.optString("type")) {
            "multi" -> parseNumbers(raw, spec.getInt("options"))?.sorted() == ints(spec.getJSONArray("answer"))
            "single" -> parseNumbers(raw, spec.getInt("options")) == listOf(spec.getInt("answer"))
            "numbers" -> {
                val values = parseNumbers(raw, spec.getInt("max")) ?: return false
                val answer = ints(spec.getJSONArray("answer"))
                if (spec.getString("order") == "ordered") values == answer else values.sorted() == answer
            }
            "word" -> {
                val normalized = nfc(raw)
                if (normalized.indexOf(ACUTE) >= 0 || normalized.indexOf(GRAVE) >= 0) return false
                val got = foldWord(raw, spec)
                if (got.isEmpty()) return false
                (listOf(spec.getString("answer")) + strings(spec.optJSONArray("accept"))).any { foldWord(it, spec) == got }
            }
            "stress" -> parseStress(raw, spec.getString("word")) == spec.getInt("answer")
            "match" -> {
                val labels = strings(spec.getJSONArray("labels"))
                val pairs = parseMatch(raw, labels, spec.getInt("right")) ?: return false
                val answer = spec.getJSONObject("answer")
                labels.all { pairs[it] == answer.getInt(it) }
            }
            "integer" -> number(squeeze(nfc(raw))) == spec.getInt("answer")
            else -> false
        }
    }
}

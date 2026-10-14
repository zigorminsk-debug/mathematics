package by.ziv.ctmaths

import org.json.JSONObject
import java.util.Locale

/**
 * Kotlin port of the portable answer checker.
 *
 * The live interface grades answers with the JavaScript implementation
 * (``webapp/core.js`` → ``CT.answer``); this Kotlin copy exists so the same
 * algorithm is available to native code (reports, exports, future widgets) and,
 * most importantly, so the Android unit tests can assert that all three
 * implementations — Python (authoring), JavaScript (UI) and Kotlin (native) —
 * return identical verdicts for the shared vectors in ``answer_vectors.json``.
 */
object AnswerChecker {

    private val MINUS = Regex("[−–—‒\u2212]")
    private val SPACES = Regex("[\\s\u00a0\u2009\u202f]")

    fun normalize(value: String?): String {
        if (value.isNullOrEmpty()) return ""
        var s = value.replace(MINUS, "-").replace(SPACES, "").lowercase(Locale.ROOT)
        s = s.replace(Regex("^(ответ|answer)[:=]"), "")
        s = s.replace(Regex("^[a-zа-я]="), "")
        if (s.endsWith(".")) s = s.dropLast(1)
        return s.replace("*", "·").replace("pi", "π")
    }

    /** Parses exact values and decimals, fractions included; null when not numeric. */
    fun toNumber(value: String?): Double? {
        val s = normalize(value)
        if (s.isEmpty()) return null
        if (s.contains('/')) {
            val parts = s.split('/')
            if (parts.size != 2) return null
            val a = toNumber(parts[0]) ?: return null
            val b = toNumber(parts[1]) ?: return null
            if (b == 0.0) return null
            return a / b
        }
        if (!Regex("^[-+]?(\\d+([.,]\\d*)?|[.,]\\d+)$").matches(s)) return null
        return s.replace(',', '.').toDoubleOrNull()
    }

    private fun accepted(task: JSONObject): List<String> {
        val result = mutableListOf<String>()
        val array = task.optJSONArray("accept")
        if (array != null) {
            for (i in 0 until array.length()) {
                normalize(array.optString(i)).takeIf { it.isNotEmpty() }?.let { result.add(it) }
            }
        }
        val answer = task.opt("answer")
        when (answer) {
            is String -> normalize(answer).takeIf { it.isNotEmpty() }?.let { result.add(it) }
            is JSONObject -> {
                listOf("ru", "en").forEach { key ->
                    normalize(answer.optString(key)).takeIf { it.isNotEmpty() }?.let { result.add(it) }
                }
            }
        }
        return result
    }

    fun check(userAnswer: String?, task: JSONObject): Boolean {
        val user = normalize(userAnswer)
        if (user.isEmpty()) return false
        val variants = accepted(task)
        if (variants.contains(user)) return true
        if (task.optString("answerType") == "choice") return false
        val value = toNumber(user) ?: return false
        for (variant in variants) {
            val other = toNumber(variant) ?: continue
            if (Math.abs(value - other) < 1e-9) return true
        }
        for (variant in variants) {
            val other = toNumber(variant) ?: continue
            // hand-written decimal approximations such as 0,833 for 5/6
            if (Math.abs(value - other) < 5e-4) return true
        }
        return false
    }
}

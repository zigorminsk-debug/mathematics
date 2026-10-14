package by.ziv.ctrussian

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Parity: the shared vectors (content_src/vectors.py → answer_vectors.json,
 * copied into the test resources by tools/sync_assets.py) must be graded
 * identically by Kotlin, JavaScript and Python. Expected values are authored
 * by hand, never computed by a checker.
 */
class AnswerCheckerTest {

    private fun cases(): JSONArray {
        val stream = javaClass.classLoader!!.getResourceAsStream("answer_vectors.json")
            ?: error("answer_vectors.json is missing from the test resources")
        val root = JSONObject(stream.bufferedReader().use { it.readText() })
        assertEquals(2, root.getInt("schema"))
        return root.getJSONArray("cases")
    }

    @Test
    fun `shared vectors are graded identically`() {
        val vectors = cases()
        assertTrue("expected a substantial vector corpus", vectors.length() >= 100)
        for (i in 0 until vectors.length()) {
            val vector = vectors.getJSONObject(i)
            val actual = AnswerChecker.check(vector.getString("user"), vector.getJSONObject("check"))
            assertEquals("${vector.getString("id")} ${vector.getString("why")} (${vector.getString("user")})",
                vector.getBoolean("expect"), actual)
        }
    }

    private fun word(answer: String, yo: String = "strict", hyphen: String = "typographic") = JSONObject()
        .put("type", "word").put("scoring", "exact").put("order", "n/a").put("answer", answer)
        .put("accept", JSONArray()).put("case", "insensitive").put("yo", yo).put("hyphen", hyphen)

    @Test
    fun `significant spaces and hyphens are never erased`() {
        assertTrue(AnswerChecker.check("так же", word("так же")))
        assertFalse(AnswerChecker.check("также", word("так же")))
        assertFalse(AnswerChecker.check("то же", word("тоже")))
        assertTrue(AnswerChecker.check("по\u2011новому", word("по-новому")))
        assertFalse(AnswerChecker.check("по\u2013новому", word("по-новому")))
        assertFalse(AnswerChecker.check("по новому", word("по-новому")))
    }

    @Test
    fun `yo and stress marks follow the explicit policy`() {
        assertFalse(AnswerChecker.check("елка", word("ёлка")))
        assertTrue(AnswerChecker.check("решенный", word("решённый", yo = "e-equals-yo")))
        assertFalse(AnswerChecker.check("за\u0301мок", word("замок")))
        val stress = JSONObject().put("type", "stress").put("scoring", "exact").put("order", "n/a")
            .put("word", "звонит").put("answer", 4).put("display", "звони\u0301т")
        assertTrue(AnswerChecker.check("звони\u0301т", stress))
        assertTrue(AnswerChecker.check("звонИт", stress))
        assertFalse(AnswerChecker.check("зво\u0301нит", stress))
    }

    @Test
    fun `extra selection never matches the correct subset`() {
        val multi = JSONObject().put("type", "multi").put("scoring", "exact").put("order", "unordered")
            .put("options", 5).put("answer", JSONArray(listOf(1, 3)))
        assertTrue(AnswerChecker.check("31", multi))
        assertFalse(AnswerChecker.check("134", multi))
        assertFalse(AnswerChecker.check("1", multi))
        assertFalse(AnswerChecker.check("113", multi))
    }

    @Test
    fun `ordered sequences keep their order`() {
        val seq = JSONObject().put("type", "numbers").put("scoring", "exact").put("order", "ordered")
            .put("max", 5).put("answer", JSONArray(listOf(2, 1, 3, 5, 4)))
        assertTrue(AnswerChecker.check("2 1 3 5 4", seq))
        assertFalse(AnswerChecker.check("12345", seq))
    }

    @Test
    fun `unknown check types fail closed`() {
        assertFalse(AnswerChecker.check("x", JSONObject().put("type", "formula").put("answer", "x")))
    }
}

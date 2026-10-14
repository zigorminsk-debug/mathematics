package by.ziv.ctmaths

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Parity test: the shared vectors produced by ``tools/build_content.py`` must be
 * graded identically by the Kotlin implementation, the JavaScript interface and
 * the Python authoring toolchain.
 *
 * The vector file is copied into the test resources by ``tools/sync_assets.py``.
 */
class AnswerCheckerTest {

    private fun loadVectors(): JSONArray {
        val stream = javaClass.classLoader!!.getResourceAsStream("answer_vectors.json")
            ?: error("answer_vectors.json is missing from the test resources")
        val text = stream.bufferedReader().use { it.readText() }
        return JSONObject(text).getJSONArray("cases")
    }

    @Test
    fun `shared vectors are graded identically`() {
        val vectors = loadVectors()
        assertTrue("expected a non-empty vector set", vectors.length() > 0)
        for (i in 0 until vectors.length()) {
            val vector = vectors.getJSONObject(i)
            val task = JSONObject().apply {
                put("accept", vector.optJSONArray("accept") ?: JSONArray())
                put("answerType", vector.optString("answerType", "short"))
            }
            val expected = vector.getBoolean("expect")
            val actual = AnswerChecker.check(vector.getString("user"), task)
            assertEquals("vector #$i (${vector.getString("user")})", expected, actual)
        }
    }

    @Test
    fun `decimals and fractions are equivalent`() {
        val task = JSONObject().put("accept", JSONArray(listOf("4/5"))).put("answerType", "short")
        assertTrue(AnswerChecker.check("0,8", task))
        assertTrue(AnswerChecker.check("0.80", task))
        assertTrue(AnswerChecker.check("8/10", task))
        assertFalse(AnswerChecker.check("0,81", task))
    }

    @Test
    fun `prefixes and dashes are ignored`() {
        val task = JSONObject().put("accept", JSONArray(listOf("-7"))).put("answerType", "short")
        assertTrue(AnswerChecker.check("x = −7", task))
        assertTrue(AnswerChecker.check("Ответ: -7", task))
        assertFalse(AnswerChecker.check("", task))
    }

    @Test
    fun `choice tasks never accept a lucky number`() {
        val task = JSONObject().put("accept", JSONArray(listOf("4"))).put("answerType", "choice")
        assertTrue(AnswerChecker.check("4", task))
        assertFalse(AnswerChecker.check("8/2", task))
    }

    @Test
    fun `exact radicals are compared as strings`() {
        val task = JSONObject().put("accept", JSONArray(listOf("6√2"))).put("answerType", "short")
        assertTrue(AnswerChecker.check(" 6√2 ", task))
        assertFalse(AnswerChecker.check("6√3", task))
    }

    @Test
    fun `whole numbers are never rounded`() {
        val task = JSONObject().put("accept", JSONArray(listOf("1000"))).put("answerType", "short")
        assertTrue(AnswerChecker.check("1000", task))
        assertTrue(AnswerChecker.check("1 000", task))
        assertTrue(AnswerChecker.check("12.", JSONObject().put("accept", JSONArray(listOf("12")))))
        assertFalse(AnswerChecker.check("1000,5", task))
        assertFalse(AnswerChecker.check("999,6", task))
    }

    @Test
    fun `hand-written decimals pass for fractions`() {
        val task = JSONObject().put("accept", JSONArray(listOf("5/6"))).put("answerType", "short")
        assertTrue(AnswerChecker.check("0,833", task))
        assertFalse(AnswerChecker.check("0,8", task))
    }

    @Test
    fun `expressions with roots and pi are evaluated`() {
        val root = JSONObject().put("accept", JSONArray(listOf("√2/2"))).put("answerType", "short")
        assertTrue(AnswerChecker.check("0,707", root))
        assertFalse(AnswerChecker.check("0,7", root))
        val pi = JSONObject().put("accept", JSONArray(listOf("2π"))).put("answerType", "short")
        assertTrue(AnswerChecker.check("6,28", pi))
        assertTrue(AnswerChecker.check("2π", pi))
        assertFalse(AnswerChecker.check("6,2", pi))
    }

    @Test
    fun `expression evaluator follows the shared grammar`() {
        assertEquals(14.0, AnswerChecker.value("2(3+4)")!!, 1e-9)
        assertEquals(10.0, AnswerChecker.value("sqrt(6^2+8^2)")!!, 1e-9)
        assertEquals(512.0, AnswerChecker.value("2^3^2")!!, 1e-9)
        assertEquals(8.485281374238571, AnswerChecker.value("6sqrt2")!!, 1e-9)
        assertEquals(0.5, AnswerChecker.value(".5")!!, 1e-9)
        assertEquals(null, AnswerChecker.value("2 +"))
        assertEquals(null, AnswerChecker.value("sqrt"))
    }
}

package by.ziv.ctenglish

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Проверка английских ответов на устройстве обязана совпадать с Python
 * (`english/content_src/policy.py`) и JavaScript (`english/webapp/core.js`).
 *
 * Тест прогоняет **общие векторы** (`answer_vectors.json`) и все задания банка с
 * однотипными: верный ответ обязан приниматься, пустой ввод — только там, где
 * задание это объявило (`empty: accept`), а причина отказа должна совпадать с
 * ожидаемой. Те же файлы читают `english/tests/answer_parity.js` и сборка
 * контента, поэтому расхождение ловится до публикации.
 */
class AnswerCheckerTest {

    private fun resource(name: String): JSONObject {
        val stream = javaClass.classLoader!!.getResourceAsStream(name)
            ?: error("нет тестового ресурса $name — запустите english/tools/build_content.py && tools/sync_assets.py")
        return JSONObject(stream.bufferedReader(Charsets.UTF_8).readText())
    }

    private fun tasks(name: String): JSONArray = resource(name).getJSONArray("tasks")

    @Test
    fun `все годовые наборы 2021–2026 включены в банк`() {
        val bank = tasks("bank.json")
        assertEquals(305, bank.length())
        val annual = (0 until bank.length()).map { bank.getJSONObject(it) }
            .filter { it.has("year") }
        assertEquals((2021..2026).toSet(), annual.map { it.getInt("year") }.toSet())
        assertEquals(240, annual.map { it.getString("text") }.toSet().size)
        for (year in 2021..2026) {
            val variant = annual.filter { it.getInt("year") == year }
            assertEquals("год $year", 40, variant.size)
            for ((part, count) in listOf("A" to 18, "B" to 22)) {
                val section = variant.filter { it.getString("part") == part }
                assertEquals((1..count).toList(), section.map { it.getInt("n") }.sorted())
                for (task in section) {
                    assertEquals("authored", task.getString("source"))
                    assertEquals("en-$year-$part${task.getInt("n")}", task.getString("id"))
                }
            }
        }
    }

    @Test
    fun `векторы ответов совпадают с эталоном`() {
        val cases = resource("answer_vectors.json").getJSONArray("cases")
        assertTrue("векторы не должны быть пустыми", cases.length() > 0)
        var checked = 0
        for (index in 0 until cases.length()) {
            val vector = cases.getJSONObject(index)
            val task = vector.getJSONObject("task")
            val typed = vector.optString("typed", "")
            val expect = vector.getBoolean("expect")
            val reason = vector.optString("reason", "")
            val verdict = AnswerChecker.check(task, typed)
            assertEquals("вектор ${vector.optString("id")}: «$typed»", expect, verdict.ok)
            if (!expect) {
                assertEquals("вектор ${vector.optString("id")}: причина", reason, verdict.reason)
            }
            checked++
        }
        assertTrue("проверено векторов: $checked", checked >= 400)
    }

    @Test
    fun `верные ответы банка принимаются, лишнее — нет`() {
        for (name in listOf("bank.json", "analogous.json")) {
            val tasks = tasks(name)
            assertTrue("$name пуст", tasks.length() > 0)
            for (index in 0 until tasks.length()) {
                val task = tasks.getJSONObject(index)
                val id = task.getString("id")
                val policy = AnswerChecker.policyFor(task)
                val answer = task.getJSONObject("answer").getString("value")
                assertTrue("$id: верный ответ «$answer» отвергнут", AnswerChecker.check(task, answer).ok)
                if (policy["case"] == "insensitive") {
                    assertTrue("$id: ответ не принят в верхнем регистре",
                        AnswerChecker.check(task, answer.uppercase()).ok)
                }
                task.optJSONArray("accepted")?.let { accepted ->
                    for (alternative in 0 until accepted.length()) {
                        val value = accepted.getString(alternative)
                        if (value == AnswerChecker.NOTHING || value == answer) continue
                        assertTrue("$id: допустимая форма «$value» отвергнута",
                            AnswerChecker.check(task, value).ok)
                    }
                }
                if (policy["empty"] == "reject") {
                    assertFalse("$id: пустой ввод принят без разрешения задания",
                        AnswerChecker.check(task, "   ").ok)
                }
                assertFalse("$id: случайный текст принят как верный ответ",
                    AnswerChecker.check(task, "zzz qqq").ok)
            }
        }
    }

    @Test
    fun `причины отказа объясняют, что именно не совпало`() {
        val articleTask = JSONObject(
            """{"id": "t1", "answer": {"value": "the piano"}}"""
        )
        assertEquals("article", AnswerChecker.check(articleTask, "piano").reason)
        assertEquals("empty", AnswerChecker.check(articleTask, "   ").reason)
        assertEquals("ok", AnswerChecker.check(articleTask, "THE PIANO").reason)

        val sensitive = JSONObject(
            """{"id": "t2", "answer": {"value": "English"}, "policy": {"case": "sensitive"}}"""
        )
        assertEquals("case", AnswerChecker.check(sensitive, "english").reason)
        assertTrue(AnswerChecker.check(sensitive, "English").ok)

        val apostrophe = JSONObject(
            """{"id": "t3", "answer": {"value": "don't"}, "policy": {"apostrophe": "required"}}"""
        )
        assertEquals("apostrophe", AnswerChecker.check(apostrophe, "dont").reason)
        assertTrue(AnswerChecker.check(apostrophe, "don\u2019t").ok)

        val hyphen = JSONObject("""{"id": "t4", "answer": {"value": "well-known"}}""")
        assertEquals("hyphen", AnswerChecker.check(hyphen, "wellknown").reason)
        // пробел вместо дефиса — та же ошибка дефиса (порядок причин в контракте)
        assertEquals("hyphen", AnswerChecker.check(hyphen, "well known").reason)

        val space = JSONObject("""{"id": "t5", "answer": {"value": "a lot of"}}""")
        assertEquals("space", AnswerChecker.check(space, "alot of").reason)

        val stress = JSONObject("""{"id": "t6", "answer": {"value": "caf\u00e9"}}""")
        assertEquals("stress", AnswerChecker.check(stress, "cafe").reason)

        val near = JSONObject("""{"id": "t7", "answer": {"value": "has lived"}}""")
        assertEquals("near", AnswerChecker.check(near, "lived").reason)
        assertEquals("exact", AnswerChecker.check(near, "zzz qqq").reason)
    }

    @Test
    fun `задание может требовать пустое поле`() {
        val nothing = JSONObject(
            """{"id": "t8", "answer": {"value": "—"}, "policy": {"empty": "accept"}}"""
        )
        assertTrue(AnswerChecker.check(nothing, "   ").ok)
        assertTrue(AnswerChecker.check(nothing, "").ok)
        val extra = AnswerChecker.check(nothing, "the")
        assertFalse(extra.ok)
        assertEquals("article", extra.reason)
        assertFalse(AnswerChecker.check(nothing, "quickly").ok)
    }

    @Test
    fun `допускается только объявленная политика`() {
        val broken = JSONObject(
            """{"id": "t9", "answer": {"value": "x"}, "policy": {"article": "ignore"}}"""
        )
        var threw = false
        try {
            AnswerChecker.check(broken, "x")
        } catch (error: IllegalArgumentException) {
            threw = true
        }
        assertTrue("policy.py принимает только checked | ignored для article", threw)

        val defaults = AnswerChecker.policyFor(JSONObject("""{"id": "t10", "answer": {"value": "x"}}"""))
        assertEquals("significant", defaults["space"])
        assertEquals("reject", defaults["empty"])
    }

    @Test
    fun `политика описывается словами для интерфейса`() {
        val described = AnswerChecker.describePolicy(AnswerChecker.DEFAULT_POLICY)
        assertEquals("точное совпадение", described)
        val withOptions = AnswerChecker.policyFor(JSONObject(
            """{"id": "t11", "answer": {"value": "x"},
                "policy": {"article": "ignored", "apostrophe": "required", "empty": "accept"}}"""
        ))
        val text = AnswerChecker.describePolicy(withOptions)
        assertTrue(text.contains("артикль"));
        assertTrue(text.contains("апостроф"));
        assertTrue(text.contains("пустым"))
    }
}

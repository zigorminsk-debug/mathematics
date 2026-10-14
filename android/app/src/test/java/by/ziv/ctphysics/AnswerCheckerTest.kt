package by.ziv.ctphysics

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Паритет проверки ответа: общие векторы, которые создаёт
 * `tools/build_content.py`, обязаны оцениваться одинаково в Python
 * (`content_src/quantities.py`), JavaScript (`webapp/core.js` → `CT.answer`) и
 * Kotlin (этот модуль). Вектора и банк копируются в тестовые ресурсы
 * (`tools/sync_assets.py`), поэтому тест видит ровно тот контент, что поедет в
 * релиз.
 *
 * Проверяются не только «верно/неверно», но и причина отказа
 * (`empty | unit | dimension | missing_unit | value`): без неё приложение не
 * сможет объяснить ученику, что именно он сделал не так.
 */
class AnswerCheckerTest {

    private fun resource(name: String): String =
        javaClass.classLoader!!.getResourceAsStream(name)?.bufferedReader()?.use { it.readText() }
            ?: error("$name отсутствует в тестовых ресурсах — запустите tools/sync_assets.py")

    private fun vectors(): JSONArray = JSONObject(resource("answer_vectors.json")).getJSONArray("cases")

    private fun unitVectors(): JSONArray = JSONObject(resource("unit_vectors.json")).getJSONArray("units")

    private fun tasks(name: String): JSONArray = JSONObject(resource(name)).getJSONArray("tasks")

    /* --------------------------------------------------- векторы ответов --- */

    @Test
    fun `shared vectors are graded identically`() {
        val cases = vectors()
        assertTrue("набор векторов пуст", cases.length() > 0)
        var checked = 0
        for (index in 0 until cases.length()) {
            val vector = cases.getJSONObject(index)
            val spec = vector.getJSONObject("spec")
            val items = vector.getJSONArray("cases")
            for (item in 0 until items.length()) {
                val entry = items.getJSONObject(item)
                val verdict = AnswerChecker.grade(entry.getString("input"), spec)
                assertEquals(
                    "вектор ${vector.getString("id")}: ${entry.getString("input")}",
                    entry.getBoolean("ok"), verdict.ok,
                )
                val reason = entry.optString("reason", "")
                if (!entry.getBoolean("ok") && reason.isNotEmpty()) {
                    assertEquals(
                        "вектор ${vector.getString("id")}: причина отказа для " +
                            entry.getString("input"),
                        reason, verdict.reason,
                    )
                }
                checked += 1
            }
        }
        assertTrue("проверено мало векторов: $checked", checked >= 40)
    }

    /* ----------------------------------------------------- таблица единиц --- */

    @Test
    fun `unit table matches the python reference`() {
        val units = unitVectors()
        var good = 0
        var bad = 0
        for (index in 0 until units.length()) {
            val vector = units.getJSONObject(index)
            val input = vector.getString("input")
            val parsed = AnswerChecker.unitOf(input)
            if (!vector.getBoolean("ok")) {
                assertNull("единица $input не должна разбираться", parsed)
                bad += 1
                continue
            }
            assertNotNull("единица $input не разобрана", parsed)
            good += 1
            val expectedDim = vector.getJSONArray("dim")
            val actualDim = parsed!!.dim
            assertEquals("размерность $input", expectedDim.length(), actualDim.size)
            for (axis in 0 until expectedDim.length()) {
                assertEquals("размерность $input[$axis]", expectedDim.getInt(axis), actualDim[axis])
            }
            val factor = vector.getString("factor").toDouble()
            assertEquals("множитель $input", factor, parsed.factor, 1e-9 * maxOf(1.0, Math.abs(factor)))
            assertEquals("смещение $input", vector.optDouble("offset", 0.0), parsed.offset, 1e-9)
        }
        assertTrue("в эталоне мало единиц: $good", good >= 60)
        assertTrue("в эталоне нет заведомо неверных единиц: $bad", bad > 0)
    }

    /** Единица без таблицы не выдумывается: «кг/с²» разбирается, «абракадабра» — нет. */
    @Test
    fun `unknown units are rejected`() {
        assertNull(AnswerChecker.unitOf("килограммометр"))
        assertNull(AnswerChecker.unitOf("???"))
        assertNotNull(AnswerChecker.unitOf("м/с²"))
    }

    /* --------------------------------------------- реальный банк и приёмка --- */

    @Test
    fun `every verified bank answer is accepted and distractors are refused`() {
        val tasks = tasks("bank.json")
        assertEquals("в банке должно быть 180 заданий", 180, tasks.length())
        var quantity = 0
        for (index in 0 until tasks.length()) {
            val task = tasks.getJSONObject(index)
            val answer = task.getJSONObject("answer").getString("ru")
            val id = task.getString("id")
            assertTrue("$id: сохранённый верный ответ «$answer» отвергнут",
                AnswerChecker.check(answer, task))
            if (task.getString("answerType") == "choice") {
                val options = task.getJSONObject("options").getJSONArray("ru")
                var wrong = 0
                for (option in 0 until options.length()) {
                    val text = options.getString(option)
                    if (AnswerChecker.normalize(text) == AnswerChecker.normalize(answer)) continue
                    wrong += 1
                    assertFalse("$id: неверный вариант «$text» принят",
                        AnswerChecker.check(text, task))
                }
                assertEquals("$id: в части A должно быть 4 неверных варианта", 4, wrong)
            } else {
                quantity += 1
                val spec = task.getJSONObject("spec")
                if (spec.optString("unitPolicy") == "required") {
                    assertFalse("$id: ответ без единицы принят при unitPolicy=required",
                        AnswerChecker.check(spec.getString("answerValue"), task))
                }
                // спека, объявляющая длину в метрах, не должна принимать ответ
                // в единицах самой задачи («17 м/с») — так же считает Python/JS
                if (spec.optString("dimension") != "m") {
                    val foreign = JSONObject(spec.toString()).put("dimension", "m")
                    assertFalse("$id: чужая размерность принята проверкой",
                        AnswerChecker.grade("${spec.getString("answerValue")} м", foreign).ok)
                }
            }
        }
        assertEquals("в банке должны быть задания-величины", 120, quantity)
    }

    @Test
    fun `generated practice tasks accept only their own answer`() {
        val tasks = tasks("analogous.json")
        assertTrue("нет аналогичных заданий", tasks.length() > 0)
        for (index in 0 until tasks.length()) {
            val task = tasks.getJSONObject(index)
            val id = task.getString("id")
            val answer = task.getJSONObject("answer").getString("ru")
            assertTrue("$id: верный ответ «$answer» отвергнут", AnswerChecker.check(answer, task))
            val value = task.getJSONObject("spec").getString("answerValue").toDouble()
            assertFalse("$id: удвоенный ответ принят", AnswerChecker.check((value * 2).toString(), task))
        }
    }

    /* --------------------------------------------- поведение по-человечески --- */

    @Test
    fun `fractions, decimals and comma decimals are the same answer`() {
        val spec = JSONObject()
            .put("answerType", "number")
            .put("answerValue", "0.5")
            .put("dimension", "1")
            .put("unitPolicy", "named")
        assertTrue(AnswerChecker.check("1/2", spec))
        assertTrue(AnswerChecker.check("0,5", spec))
        assertTrue(AnswerChecker.check("0.50", spec))
        assertTrue(AnswerChecker.check("5·10⁻¹", spec))
        assertFalse(AnswerChecker.check("3/4", spec))
        assertFalse(AnswerChecker.check("1/0", spec))
    }

    @Test
    fun `prefix conversion of 36 km per hour is ten metres per second`() {
        val spec = JSONObject()
            .put("answerType", "number")
            .put("answerValue", "10")
            .put("dimension", "m/s")
            .put("unit", "м/с")
            .put("unitPolicy", "named")
            .put("tolerance", JSONObject().put("kind", "absolute").put("value", "0.5"))
        assertTrue(AnswerChecker.check("36 км/ч", spec))
        assertTrue(AnswerChecker.check("10 м/с", spec))
        assertFalse(AnswerChecker.check("36", spec))
        assertFalse(AnswerChecker.check("10 км/ч", spec))
    }

    /** Неверная единица — это ошибка размерности, а не «неточность». */
    @Test
    fun `ten newtons are not ten kilograms`() {
        val spec = JSONObject()
            .put("answerType", "number")
            .put("answerValue", "10")
            .put("dimension", "kg")
            .put("unit", "кг")
            .put("unitPolicy", "named")
        assertEquals("dimension", AnswerChecker.grade("10 Н", spec).reason)
        assertEquals("", AnswerChecker.grade("10 кг", spec).reason)
    }

    @Test
    fun `missing unit is reported when the task demands one`() {
        val required = JSONObject()
            .put("answerType", "number")
            .put("answerValue", "5")
            .put("dimension", "m")
            .put("unit", "м")
            .put("unitPolicy", "required")
        assertEquals("missing_unit", AnswerChecker.grade("5", required).reason)
        assertTrue(AnswerChecker.grade("5 м", required).ok)
        val named = JSONObject(required.toString()).put("unitPolicy", "named")
        assertTrue(AnswerChecker.grade("5", named).ok)
    }

    @Test
    fun `empty and unparsable answers are never accepted`() {
        val spec = JSONObject()
            .put("answerType", "number")
            .put("answerValue", "12")
            .put("dimension", "1")
        // неразобранная запись — «пусто»: приложение просит ввести число,
        // а не сообщает «неверно» (так же ведут себя Python и JavaScript)
        assertEquals("empty", AnswerChecker.grade("", spec).reason)
        assertEquals("empty", AnswerChecker.grade("   ", spec).reason)
        assertEquals("empty", AnswerChecker.grade("двенадцать", spec).reason)
        assertEquals("empty", AnswerChecker.grade("1/0", spec).reason)
        assertEquals("value", AnswerChecker.grade("13", spec).reason)
    }

    /** Часть A сравнивает канонические записи: «4» выбирается, «8/2» — нет. */
    @Test
    fun `choice tasks never accept a lucky equivalent`() {
        val spec = JSONObject()
            .put("answerType", "choice")
            .put("accept", JSONArray(listOf("4")))
        assertTrue(AnswerChecker.check("4", spec))
        assertFalse(AnswerChecker.check("8/2", spec))
        assertFalse(AnswerChecker.check("", spec))
    }

    @Test
    fun `the unit table is present and non-trivial`() {
        assertTrue("таблица единиц не загрузилась", AnswerChecker.unitCount() >= 30)
    }
}

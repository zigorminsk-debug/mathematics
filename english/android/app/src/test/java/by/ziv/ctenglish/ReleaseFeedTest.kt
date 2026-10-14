package by.ziv.ctenglish

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Канал обновления английского: приложение обязано искать **свои** выпуски и
 * отвергать чужой банк.
 *
 * Проверяется чистый разбор ответа Releases API, без сети и без Android:
 *  — общий `/releases/latest` (там математика) не используется никогда;
 *  — выпуски математики и черновики не выбираются;
 *  — берётся самая новая версия английского, а не первая в списке;
 *  — манифест другого предмета не ставится поверх банка английского.
 */
class ReleaseFeedTest {

    private fun release(tag: String, draft: Boolean = false, prerelease: Boolean = false) =
        """{"tag_name":"$tag","draft":$draft,"prerelease":$prerelease}"""

    @Test
    fun `the feed is version specific and never the repository latest`() {
        val base = ReleaseFeed.downloadBase("english-v2026.10.1")
        assertEquals(
            "https://github.com/zigorminsk-debug/mathematics/releases/download/english-v2026.10.1",
            base,
        )
        assertFalse("общий latest отдаёт математику", base.contains("/latest/"))
        assertFalse(ReleaseFeed.RELEASES_API.contains("/releases/latest"))
    }

    @Test
    fun `only English releases are picked`() {
        val payload = "[" + listOf(
            release("v2026.10.8"),                       // математика — не наша семья тегов
            release("english-v2026.10.1"),
            release("russian-v2026.1.0"),
        ).joinToString(",") + "]"
        assertEquals("english-v2026.10.1", ReleaseFeed.newestTag(payload))
    }

    @Test
    fun `the newest English version wins regardless of order`() {
        val payload = "[" + listOf(
            release("english-v2026.10.3"),
            release("english-v2026.9.0"),
            release("english-v2026.10.1"),
            release("english-v2027.1.0", draft = true),      // черновик не публикуется
            release("english-v2026.12.0", prerelease = true), // предвыпуск не публикуется
        ).joinToString(",") + "]"
        assertEquals("english-v2026.10.3", ReleaseFeed.newestTag(payload))
    }

    @Test
    fun `versions are compared numerically not lexicographically`() {
        val payload = "[" + listOf(release("english-v2026.9.12"), release("english-v2026.10.0"))
            .joinToString(",") + "]"
        assertEquals("english-v2026.10.0", ReleaseFeed.newestTag(payload))
    }

    @Test
    fun `no English release means no feed`() {
        assertNull(ReleaseFeed.newestTag("[]"))
        assertNull(ReleaseFeed.newestTag("""[{"tag_name":"v2026.10.8","draft":false}]"""))
        assertNull(ReleaseFeed.newestTag("""[{"tag_name":"english-vnext"}]"""))
        assertNull("сломанный ответ не должен открывать какое-то обновление",
            ReleaseFeed.feedFrom("not json at all"))
    }

    @Test
    fun `the feed points at the resolved release`() {
        assertEquals(
            "https://github.com/zigorminsk-debug/mathematics/releases/download/english-v2026.10.2",
            ReleaseFeed.feedFrom("[" + release("english-v2026.10.2") + "]"),
        )
    }

    @Test
    fun `a foreign subject manifest is refused`() {
        assertTrue(ReleaseFeed.manifestMatches("english", "by.ziv.ctenglish"))
        assertTrue("debug-сборка ставит тот же банк",
            ReleaseFeed.manifestMatches("english", "by.ziv.ctenglish.debug"))
        assertFalse("банк математики не должен попасть в приложение по английскому языку",
            ReleaseFeed.manifestMatches("mathematics", "by.ziv.ctmaths"))
        assertFalse(ReleaseFeed.manifestMatches("english", "by.ziv.ctmaths"))
        assertFalse(ReleaseFeed.manifestMatches("", ""))
        assertFalse(ReleaseFeed.manifestMatches("english", "by.ziv.ctrussian"))
    }
}

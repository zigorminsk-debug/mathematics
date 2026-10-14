package by.ziv.ctphysics

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Канал обновления физики: приложение обязано искать **свои** выпуски и
 * отвергать чужой банк.
 *
 * Проверяется чистый разбор ответа Releases API, без сети и без Android:
 *  — общий `/releases/latest` (там математика) не используется никогда;
 *  — выпуски математики и черновики не выбираются;
 *  — берётся самая новая версия физики, а не первая в списке;
 *  — манифест другого предмета не ставится поверх банка физики.
 */
class ReleaseFeedTest {

    private fun release(tag: String, draft: Boolean = false, prerelease: Boolean = false) =
        """{"tag_name":"$tag","draft":$draft,"prerelease":$prerelease}"""

    @Test
    fun `the feed is version specific and never the repository latest`() {
        val base = ReleaseFeed.downloadBase("physics-v2026.10.1")
        assertEquals(
            "https://github.com/zigorminsk-debug/mathematics/releases/download/physics-v2026.10.1",
            base,
        )
        assertFalse("общий latest отдаёт математику", base.contains("/latest/"))
        assertFalse(ReleaseFeed.RELEASES_API.contains("/releases/latest"))
    }

    @Test
    fun `only physics releases are picked`() {
        val payload = "[" + listOf(
            release("v2026.10.8"),                       // математика — не наша семья тегов
            release("physics-v2026.10.1"),
            release("russian-v2026.1.0"),
        ).joinToString(",") + "]"
        assertEquals("physics-v2026.10.1", ReleaseFeed.newestTag(payload))
    }

    @Test
    fun `the newest physics version wins regardless of order`() {
        val payload = "[" + listOf(
            release("physics-v2026.10.3"),
            release("physics-v2026.9.0"),
            release("physics-v2026.10.1"),
            release("physics-v2027.1.0", draft = true),      // черновик не публикуется
            release("physics-v2026.12.0", prerelease = true), // предвыпуск не публикуется
        ).joinToString(",") + "]"
        assertEquals("physics-v2026.10.3", ReleaseFeed.newestTag(payload))
    }

    @Test
    fun `versions are compared numerically not lexicographically`() {
        val payload = "[" + listOf(release("physics-v2026.9.12"), release("physics-v2026.10.0"))
            .joinToString(",") + "]"
        assertEquals("physics-v2026.10.0", ReleaseFeed.newestTag(payload))
    }

    @Test
    fun `no physics release means no feed`() {
        assertNull(ReleaseFeed.newestTag("[]"))
        assertNull(ReleaseFeed.newestTag("""[{"tag_name":"v2026.10.8","draft":false}]"""))
        assertNull(ReleaseFeed.newestTag("""[{"tag_name":"physics-vnext"}]"""))
        assertNull("сломанный ответ не должен открывать какое-то обновление",
            ReleaseFeed.feedFrom("not json at all"))
    }

    @Test
    fun `the feed points at the resolved release`() {
        assertEquals(
            "https://github.com/zigorminsk-debug/mathematics/releases/download/physics-v2026.10.2",
            ReleaseFeed.feedFrom("[" + release("physics-v2026.10.2") + "]"),
        )
    }

    @Test
    fun `a foreign subject manifest is refused`() {
        assertTrue(ReleaseFeed.manifestMatches("physics", "by.ziv.ctphysics"))
        assertTrue("debug-сборка ставит тот же банк",
            ReleaseFeed.manifestMatches("physics", "by.ziv.ctphysics.debug"))
        assertFalse("банк математики не должен попасть в приложение по физике",
            ReleaseFeed.manifestMatches("mathematics", "by.ziv.ctmaths"))
        assertFalse(ReleaseFeed.manifestMatches("physics", "by.ziv.ctmaths"))
        assertFalse(ReleaseFeed.manifestMatches("", ""))
        assertFalse(ReleaseFeed.manifestMatches("physics", "by.ziv.ctrussian"))
    }
}

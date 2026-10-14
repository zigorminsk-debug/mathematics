package by.ziv.ctrussian

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** The subject update channel must never pick the mathematics (or any foreign) release. */
class UpdateFeedTest {

    private fun release(tag: String, draft: Boolean = false, prerelease: Boolean = false,
                        assets: Collection<String> = UpdateFeed.RELEASE_FILES, state: String = "uploaded"): JSONObject {
        val list = JSONArray()
        assets.forEach { list.put(JSONObject().put("name", it).put("state", state)) }
        return JSONObject().put("tag_name", tag).put("draft", draft).put("prerelease", prerelease).put("assets", list)
    }

    private val mathAssets = listOf(
        "analogous.json", "answer_vectors.json", "app-release.apk", "bank.json", "CTMathsTutor-amd64.exe",
        "CTMathsTutor-arm64.exe", "formulas.json", "mistakes.json", "release-info.json", "SHA256SUMS.txt",
        "topics.json", "ui_strings.json", "version.json",
    )

    @Test
    fun `math latest and sibling families are ignored`() {
        val page = JSONArray()
            .put(release("v2026.10.8", assets = mathAssets))
            .put(release("physics-v2026.10.3"))
            .put(release("russian-v2026.10.1"))
        assertEquals(UpdateFeed.Candidate("russian-v2026.10.1", "2026.10.1"), UpdateFeed.select(listOf(page)))
        assertNull(UpdateFeed.select(listOf(JSONArray().put(release("v2026.10.8", assets = mathAssets)))))
    }

    @Test
    fun `drafts, prereleases, non-canonical tags and incomplete inventories are excluded`() {
        val page = JSONArray()
            .put(release("russian-v2026.10.9", draft = true))
            .put(release("russian-v2026.10.8", prerelease = true))
            .put(release("russian-v2026.10.07"))
            .put(release("russian-v2026.10.6", assets = UpdateFeed.RELEASE_FILES - "CTRussianTutor-arm64.exe"))
            .put(release("russian-v2026.10.5", assets = UpdateFeed.RELEASE_FILES + "app-debug.apk"))
            .put(release("russian-v2026.10.4", state = "starter"))
            .put(release("russian-v2026.10.2"))
        assertEquals("russian-v2026.10.2", UpdateFeed.select(listOf(page))?.tag)
    }

    @Test
    fun `the highest canonical version wins across pages, not the order`() {
        val first = JSONArray().put(release("russian-v2026.9.12")).put(release("russian-v2026.11.0"))
        val second = JSONArray().put(release("russian-v2026.10.99"))
        assertEquals("2026.11.0", UpdateFeed.select(listOf(second, first))?.version)
        val full = JSONArray()
        repeat(UpdateFeed.PAGE_SIZE) { full.put(JSONObject()) }
        assertTrue(UpdateFeed.hasMore(full, 1))
        assertFalse(UpdateFeed.hasMore(first, 1))
        assertFalse(UpdateFeed.hasMore(full, UpdateFeed.MAX_PAGES))
    }

    @Test
    fun `download urls are tag specific, never releases-latest`() {
        val base = UpdateFeed.downloadBase("russian-v2026.10.1")
        assertEquals("https://github.com/zigorminsk-debug/mathematics/releases/download/russian-v2026.10.1", base)
        assertFalse(base.contains("latest"))
        assertTrue(UpdateFeed.apiPage(2).endsWith("releases?per_page=100&page=2"))
    }

    private fun manifest(subject: String = "russian", pkg: String = "by.ziv.ctrussian"): JSONObject {
        val files = JSONObject()
        UpdateFeed.CONTENT_FILES.forEach { files.put(it, JSONObject().put("sha256", "a".repeat(64)).put("bytes", 10)) }
        return JSONObject().put("subject", subject).put("package", pkg).put("schema", 2).put("contentProtocol", 2)
            .put("contentVersion", "2026.10.1").put("tag", "russian-v2026.10.1").put("files", files)
    }

    @Test
    fun `manifest gate rejects foreign subject, package, schema and inventory`() {
        val candidate = UpdateFeed.Candidate("russian-v2026.10.1", "2026.10.1")
        assertNull(UpdateFeed.manifestError(manifest(), candidate))
        assertNotNull(UpdateFeed.manifestError(manifest(subject = "mathematics"), candidate))
        assertNotNull(UpdateFeed.manifestError(manifest(pkg = "by.ziv.ctmaths"), candidate))
        assertNotNull(UpdateFeed.manifestError(manifest().put("schema", 1), candidate))
        assertNotNull(UpdateFeed.manifestError(manifest().put("tag", "v2026.10.8"), candidate))
        assertNotNull(UpdateFeed.manifestError(manifest(), UpdateFeed.Candidate("russian-v2026.10.2", "2026.10.2")))
        val extra = manifest()
        extra.getJSONObject("files").put("formulas.json", JSONObject().put("sha256", "b".repeat(64)).put("bytes", 1))
        assertNotNull(UpdateFeed.manifestError(extra, candidate))
        val broken = manifest()
        broken.getJSONObject("files").getJSONObject("bank.json").put("sha256", "XYZ")
        assertNotNull(UpdateFeed.manifestError(broken, candidate))
    }

    @Test
    fun `a mathematics bank or overlay is rejected`() {
        val russian = JSONObject().put("meta", JSONObject().put("subject", "russian").put("package", "by.ziv.ctrussian"))
        val maths = JSONObject().put("meta", JSONObject().put("subject", "mathematics").put("package", "by.ziv.ctmaths"))
        assertNull(UpdateFeed.bankError(russian))
        assertNotNull(UpdateFeed.bankError(maths))
        assertNotNull(UpdateFeed.bankError(JSONObject().put("meta", JSONObject().put("contentVersion", "2026.10.8"))))
        assertNull(UpdateFeed.overlayError(manifest()))
        assertNotNull(UpdateFeed.overlayError(manifest(subject = "mathematics")))
        assertNotNull(UpdateFeed.overlayError(null))
    }
}

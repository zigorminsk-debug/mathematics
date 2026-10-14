package by.ziv.ctrussian

import org.json.JSONArray
import org.json.JSONObject

/**
 * Subject-scoped update channel of «Репетитор ЦТ: Русский язык».
 *
 * GitHub's repository-wide `releases/latest` belongs to the mathematics tutor,
 * so this client never uses it. It pages through the Releases API, keeps only
 * published (non-draft, non-prerelease) releases of the `russian-v` family
 * with a canonical version and the complete expected inventory, chooses the
 * highest version (not the newest date) and downloads every file from that
 * release's tag-specific URL. The manifest and the banks must name this
 * subject and package before anything is written.
 */
internal object UpdateFeed {
    const val SUBJECT = "russian"
    const val PACKAGE = "by.ziv.ctrussian"
    const val TAG_PREFIX = "russian-v"
    const val PROTOCOL = 2
    const val SCHEMA = 2
    const val REPOSITORY = "zigorminsk-debug/mathematics"
    const val PAGE_SIZE = 100
    const val MAX_PAGES = 10

    val CONTENT_FILES = setOf(
        "bank.json", "analogous.json", "topics.json", "rules.json", "ui_strings.json", "mistakes.json",
        "answer_vectors.json",
    )
    val RELEASE_FILES = CONTENT_FILES + setOf(
        "version.json", "release-info.json", "SHA256SUMS.txt", "app-release.apk",
        "CTRussianTutor-amd64.exe", "CTRussianTutor-arm64.exe",
    )

    private val TAG = Regex("russian-v(20[0-9]{2})\\.([1-9]|1[0-2])\\.(0|[1-9][0-9]?)")
    private val SHA256 = Regex("[0-9a-f]{64}")

    data class Candidate(val tag: String, val version: String)

    fun apiPage(page: Int): String =
        "https://api.github.com/repos/$REPOSITORY/releases?per_page=$PAGE_SIZE&page=$page"

    fun downloadBase(tag: String): String = "https://github.com/$REPOSITORY/releases/download/$tag"

    /** "russian-v2026.10.1" → "2026.10.1"; non-canonical or foreign tags → null. */
    fun versionOf(tag: String): String? {
        val match = TAG.matchEntire(tag) ?: return null
        return match.groupValues.drop(1).joinToString(".")
    }

    fun code(version: String): Long {
        val parts = version.split(".").map { it.toLong() }
        return parts[0] * 10000 + parts[1] * 100 + parts[2]
    }

    /** True when a release lists exactly the expected uploaded assets (incomplete or foreign inventory → false). */
    fun completeInventory(release: JSONObject): Boolean {
        val assets = release.optJSONArray("assets") ?: return false
        val names = HashSet<String>()
        for (index in 0 until assets.length()) {
            val asset = assets.optJSONObject(index) ?: return false
            if (asset.optString("state", "uploaded") != "uploaded") return false
            names.add(asset.optString("name"))
        }
        return names == RELEASE_FILES && assets.length() == RELEASE_FILES.size
    }

    /** The newest stable release of THIS subject across all fetched pages, or null. */
    fun select(pages: List<JSONArray>): Candidate? {
        var best: Candidate? = null
        for (page in pages) {
            for (index in 0 until page.length()) {
                val release = page.optJSONObject(index) ?: continue
                if (release.optBoolean("draft", true) || release.optBoolean("prerelease", true)) continue
                val tag = release.optString("tag_name")
                val version = versionOf(tag) ?: continue
                if (!completeInventory(release)) continue
                if (best == null || code(version) > code(best.version)) best = Candidate(tag, version)
            }
        }
        return best
    }

    /** Should another API page be requested after this one? */
    fun hasMore(page: JSONArray, number: Int): Boolean = page.length() >= PAGE_SIZE && number < MAX_PAGES

    /** Manifest gate before any content file is downloaded. Returns an error or null. */
    fun manifestError(manifest: JSONObject, expected: Candidate?): String? {
        if (manifest.optString("subject") != SUBJECT) return "manifest belongs to another subject"
        if (manifest.optString("package") != PACKAGE) return "manifest belongs to another package"
        if (manifest.optInt("schema", -1) != SCHEMA || manifest.optInt("contentProtocol", -1) != PROTOCOL) {
            return "unsupported manifest schema"
        }
        val version = manifest.optString("contentVersion")
        if (!ContentVersions.isValid(version)) return "manifest has no valid contentVersion"
        if (expected != null) {
            if (version != expected.version) return "manifest version differs from the release tag"
            if (manifest.optString("tag") != expected.tag) return "manifest tag differs from the release"
        }
        val files = manifest.optJSONObject("files") ?: return "manifest has no files"
        val names = HashSet<String>()
        val keys = files.keys()
        while (keys.hasNext()) names.add(keys.next())
        if (names != CONTENT_FILES) return "manifest must list exactly the content files"
        for (name in names) {
            val meta = files.optJSONObject(name) ?: return "file $name has no metadata"
            if (!SHA256.matches(meta.optString("sha256"))) return "file $name has no SHA-256"
            if (meta.optLong("bytes", 0) <= 0) return "file $name has no size"
        }
        return null
    }

    /** A downloaded bank must name this subject and package (a mathematics bank is rejected). */
    fun bankError(bank: JSONObject): String? {
        val meta = bank.optJSONObject("meta") ?: return "bank has no metadata"
        if (meta.optString("subject") != SUBJECT || meta.optString("package") != PACKAGE) return "foreign bank rejected"
        return null
    }

    /** Overlay version.json written by this app: valid only for this subject and package. */
    fun overlayError(manifest: JSONObject?): String? {
        if (manifest == null) return "no overlay manifest"
        if (manifest.optString("subject") != SUBJECT || manifest.optString("package") != PACKAGE) return "foreign overlay"
        if (!ContentVersions.isValid(manifest.optString("contentVersion"))) return "overlay version unknown"
        return null
    }
}

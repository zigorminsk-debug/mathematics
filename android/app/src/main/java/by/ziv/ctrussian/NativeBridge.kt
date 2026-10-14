package by.ziv.ctrussian

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.VibratorManager
import android.util.Log
import android.view.WindowManager
import android.webkit.JavascriptInterface
import android.widget.Toast
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.Executors

/**
 * ``window.CTNative`` — the native side of the shared web interface.
 *
 * Storage layout (private to the app, survives updates):
 *
 * ```
 * filesDir/data/<key>.json          progress, settings, session blobs
 * filesDir/content/<name>.json      verified content pack of THIS subject (russian-v… release)
 * getExternalFilesDir/reports/       exported progress reports (HTML)
 * ```
 *
 * The same method names are implemented by the Windows backend through HTTP
 * (see windows/main.go), which is what allows one single web application to run
 * on both platforms.
 */
class NativeBridge(
    private val activity: Activity,
    private val evaluateJavascript: (String) -> Unit
) {

    private val dataDir = File(activity.filesDir, "data").apply { mkdirs() }
    private val contentBackup = File(activity.filesDir, "content.previous")
    private val contentDir = File(activity.filesDir, "content").apply {
        // Recover if the process stopped between the two directory renames.
        if (!exists() && contentBackup.exists()) contentBackup.renameTo(this)
        mkdirs()
    }
    private val contentLock = Any()
    private val updateExecutor = Executors.newSingleThreadExecutor()
    private val mainHandler = Handler(Looper.getMainLooper())
    private val keyPattern = Regex("^[a-zA-Z0-9_-]{1,32}$")

    /* ------------------------------------------------------------- storage */

    @JavascriptInterface
    fun getState(): String {
        val app = JSONObject().apply {
            put("version", BuildConfig.VERSION_NAME)
            put("build", BuildConfig.VERSION_CODE.toString())
            put("os", "Android ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})")
            put("platform", "android")
            put("shell", "webview")
            put("dataDir", dataDir.absolutePath)
            put("contentDir", contentDir.absolutePath)
            put("reportsDir", File(activity.getExternalFilesDir(null), "reports").absolutePath)
            put("repo", "https://github.com/${UpdateFeed.REPOSITORY}")
            put("subject", UpdateFeed.SUBJECT)
            put("package", BuildConfig.APPLICATION_ID)
            put("email", "ziv@csl.by")
            put("phone", "+3753371412")
            put("developer", JSONObject().apply {
                put("name", "Zakharevich Igor (Захаревич Игорь)")
                put("email", "ziv@csl.by")
                put("phone", "+3753371412")
            })
        }
        val blobs = JSONObject()
        listOf("progress", "settings", "history", "session").forEach { key ->
            readBlob(key)?.let { blobs.put(key, it) }
        }
        val content = JSONObject().apply {
            put("version", installedContentVersion())
            put("overlay", File(contentDir, "bank.json").exists() && overlayIsCurrent())
            put("channel", UpdateFeed.TAG_PREFIX)
        }
        return JSONObject().apply {
            put("app", app)
            put("content", content)
            put("blobs", blobs)
        }.toString()
    }

    @JavascriptInterface
    fun loadBlob(key: String): String? = readBlob(key)

    @JavascriptInterface
    fun saveBlob(key: String, json: String) {
        if (!keyPattern.matches(key)) return
        try {
            JSONObject(json) // the payload must be valid JSON
            File(dataDir, "$key.json").writeText(json)
        } catch (error: Exception) {
            Log.w(TAG, "saveBlob($key) rejected: ${error.message}")
        }
    }

    /**
     * Content of a bank: a downloaded pack wins over the embedded asset only
     * when it is not older than the pack inside the APK. Otherwise a bank
     * downloaded by a previous installation would shadow a newer APK forever
     * (the new variant would never appear after an in-place update).
     */
    @JavascriptInterface
    fun getContent(name: String): String? = synchronized(contentLock) {
        if (!keyPattern.matches(name)) return@synchronized null
        val overlay = File(contentDir, "$name.json")
        if (overlay.exists() && overlayIsCurrent()) {
            try {
                return@synchronized overlay.readText()
            } catch (ignored: IOException) {
                // Fall back to the embedded file rather than returning null.
            }
        }
        try {
            activity.assets.open("webapp/content/$name.json").bufferedReader().use { it.readText() }
        } catch (error: IOException) {
            null
        }
    }

    /* -------------------------------------------------------------- update */

    /** Asynchronous bridge: an offline check must not block the WebView UI. */
    @JavascriptInterface
    fun checkUpdatesAsync(feedOverride: String, currentVersion: String, requestId: String) {
        if (!keyPattern.matches(requestId)) return
        updateExecutor.execute {
            val response = checkUpdates(feedOverride, currentVersion)
            mainHandler.post {
                if (!activity.isFinishing && !activity.isDestroyed) {
                    // quote both arguments; response is data, never executable JS
                    evaluateJavascript("window.CT && window.CT.bridge.onUpdateResult(" +
                        JSONObject.quote(requestId) + "," + JSONObject.quote(response) + ");")
                }
            }
        }
    }

    /**
     * Downloads a newer content pack of THIS subject only. The release is chosen
     * through the paginated Releases API (russian-v family, stable, canonical
     * version, complete inventory) — never the repository-wide latest, which
     * belongs to the mathematics tutor. Every file comes from the tag-specific
     * URL and must match the manifest SHA-256/size; manifest and banks must name
     * subject «russian» and package by.ziv.ctrussian. Progress is never touched.
     * A non-empty [feedOverride] (tests, a local feed) skips only the selection.
     */
    @Synchronized
    @JavascriptInterface
    fun checkUpdates(feedOverride: String, currentVersion: String): String {
        val installedVersion = installedContentVersion()
        val current = if (ContentVersions.compare(currentVersion, installedVersion) > 0) currentVersion else installedVersion
        var staged: File? = null
        return try {
            val candidate: UpdateFeed.Candidate?
            val base: String
            if (feedOverride.isNotBlank()) {
                candidate = null
                base = feedOverride.trim().trimEnd('/')
            } else {
                val found = resolveRelease()
                    ?: return result("uptodate", current, 0, "no published release of this subject yet")
                if (ContentVersions.compare(found.version, current) <= 0) {
                    return result("uptodate", current, 0, "content is up to date")
                }
                candidate = found
                base = UpdateFeed.downloadBase(found.tag)
            }
            if (!base.startsWith("https://")) throw IllegalArgumentException("update feed must use HTTPS")
            val manifest = httpGet("$base/version.json")
            val manifestJson = JSONObject(manifest.toString(Charsets.UTF_8))
            UpdateFeed.manifestError(manifestJson, candidate)?.let { return result("error", current, 0, it) }
            val version = manifestJson.getString("contentVersion")
            // A new APK can be ahead of the newest release; never downgrade its bank.
            if (ContentVersions.compare(version, current) <= 0) {
                return result("uptodate", current, 0, "content is up to date")
            }
            val files = manifestJson.getJSONObject("files")
            val pack = File.createTempFile("content-update-", "", activity.filesDir)
            staged = pack
            if (!pack.delete() || !pack.mkdir()) throw IOException("cannot create staging directory")
            var count = 0
            for (fileName in UpdateFeed.CONTENT_FILES.sorted()) {
                val meta = files.getJSONObject(fileName)
                val expected = meta.getString("sha256").lowercase(Locale.ROOT)
                val body = httpGet("$base/$fileName")
                if (sha256(body) != expected || meta.optLong("bytes") != body.size.toLong()) {
                    return result("error", current, 0, "checksum or size mismatch for $fileName")
                }
                val parsed = JSONObject(body.toString(Charsets.UTF_8)) // reject a truncated/invalid file
                if (fileName == "bank.json" || fileName == "analogous.json") {
                    UpdateFeed.bankError(parsed)?.let { return result("error", current, 0, it) }
                }
                File(pack, fileName).writeBytes(body)
                count++
            }
            File(pack, "version.json").writeBytes(manifest)
            // Commit only the fully verified pack: no mixture of old and new content.
            synchronized(contentLock) {
                if (contentBackup.exists() && !contentBackup.deleteRecursively()) throw IOException("cannot clear backup")
                if (contentDir.exists() && !contentDir.renameTo(contentBackup)) throw IOException("cannot back up content")
                if (!pack.renameTo(contentDir)) {
                    contentBackup.renameTo(contentDir)
                    throw IOException("cannot install content")
                }
                contentBackup.deleteRecursively()
            }
            result("updated", version, count, "installed $count content files")
        } catch (error: IOException) {
            result("offline", current, 0, error.message ?: "network unavailable")
        } catch (error: Exception) {
            result("error", current, 0, error.message ?: "unexpected error")
        } finally {
            staged?.deleteRecursively()
        }
    }

    /** Page through the Releases API and pick the newest verified release of this subject. */
    private fun resolveRelease(): UpdateFeed.Candidate? {
        val pages = ArrayList<JSONArray>()
        var number = 1
        while (true) {
            val page = JSONArray(httpGet(UpdateFeed.apiPage(number), json = true).toString(Charsets.UTF_8))
            pages.add(page)
            if (!UpdateFeed.hasMore(page, number)) break
            number++
        }
        return UpdateFeed.select(pages)
    }

    private fun result(status: String, version: String, installed: Int, message: String): String {
        val count = try {
            JSONObject(getContent("bank") ?: "{}").optJSONArray("tasks")?.length() ?: 0
        } catch (error: Exception) {
            0
        }
        return JSONObject().apply {
            put("status", status)
            put("version", version)
            put("newTasks", count)
            put("installed", installed)
            put("message", message)
        }.toString()
    }

    private fun httpGet(url: String, json: Boolean = false): ByteArray {
        val connection = (URL(url).openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            connectTimeout = 15000
            readTimeout = 30000
            setRequestProperty("User-Agent", "CTRussianTutor/${BuildConfig.VERSION_NAME}")
            if (json) setRequestProperty("Accept", "application/vnd.github+json")
            instanceFollowRedirects = true
        }
        try {
            if (connection.responseCode !in 200..299) {
                throw IOException("HTTP ${connection.responseCode} for $url")
            }
            return connection.inputStream.use { input ->
                val bytes = ByteArrayOutputStream()
                val buffer = ByteArray(8192)
                while (true) {
                    val length = input.read(buffer)
                    if (length < 0) break
                    if (bytes.size() + length > 32 * 1024 * 1024) throw IOException("content file too large")
                    bytes.write(buffer, 0, length)
                }
                bytes.toByteArray()
            }
        } finally {
            connection.disconnect()
        }
    }

    private fun sha256(bytes: ByteArray): String =
        MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }

    /* -------------------------------------------------------- ui utilities */

    @JavascriptInterface
    fun openExternal(url: String) {
        mainHandler.post {
            try {
                activity.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
            } catch (error: Exception) {
                Toast.makeText(activity, url, Toast.LENGTH_LONG).show()
            }
        }
    }

    @JavascriptInterface
    fun toast(message: String) {
        mainHandler.post { Toast.makeText(activity, message, Toast.LENGTH_SHORT).show() }
    }

    @JavascriptInterface
    fun quit() {
        mainHandler.post { activity.finish() }
    }

    @JavascriptInterface
    fun saveReport(name: String, html: String): String {
        val dir = File(activity.getExternalFilesDir(null), "reports").apply { mkdirs() }
        val stamp = SimpleDateFormat("yyyyMMdd-HHmmss", Locale.US).format(Date())
        val clean = name.replace(Regex("[^a-zA-Z0-9_-]+"), "_").take(60).ifBlank { "progress" }
        val file = File(dir, "${clean}_$stamp.html")
        return try {
            file.writeText(html)
            JSONObject().put("path", file.absolutePath).toString()
        } catch (error: IOException) {
            JSONObject().put("path", "").put("error", error.message ?: "").toString()
        }
    }

    /** Открыть папку средствами системы; если некому — показать путь (ничего не теряется). */
    @JavascriptInterface
    fun openFolder(which: String): String {
        val target = when (which) {
            "content" -> contentDir
            "reports" -> File(activity.getExternalFilesDir(null), "reports").apply { mkdirs() }
            else -> dataDir
        }
        mainHandler.post {
            val shown = try {
                val intent = Intent(Intent.ACTION_VIEW).apply {
                    setDataAndType(Uri.parse("file://" + target.absolutePath), "resource/folder")
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                }
                activity.startActivity(intent)
                true
            } catch (error: Exception) {
                false
            }
            if (!shown) {
                // На телефоне проводника для приватной папки обычно нет — показываем путь.
                Toast.makeText(activity, target.absolutePath, Toast.LENGTH_LONG).show()
            }
        }
        return JSONObject().put("ok", true).put("path", target.absolutePath).toString()
    }

    /** Короткая вибрация как отклик на верный/неверный ответ (если включена в настройках). */
    @JavascriptInterface
    fun vibrate(milliseconds: Int) {
        mainHandler.post {
            try {
                val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    (activity.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager).defaultVibrator
                } else {
                    @Suppress("DEPRECATION")
                    activity.getSystemService(Context.VIBRATOR_SERVICE) as android.os.Vibrator
                }
                @Suppress("DEPRECATION")
                vibrator.vibrate(milliseconds.coerceIn(5, 200).toLong())
            } catch (error: Exception) {
                Log.w(TAG, "vibrate failed: ${error.message}")
            }
        }
    }

    @JavascriptInterface
    fun setKeepScreenOn(enabled: Boolean) {
        mainHandler.post {
            if (enabled) {
                activity.window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            } else {
                activity.window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            }
        }
    }

    fun applyKeepScreenOnFromSettings() {
        val settings = readBlob("settings") ?: return
        try {
            setKeepScreenOn(JSONObject(settings).optBoolean("keepScreenOn", true))
        } catch (ignored: Exception) {
            setKeepScreenOn(true)
        }
    }

    fun shutdown() { updateExecutor.shutdownNow() }

    /* ------------------------------------------------------------ private */

    private fun readBlob(key: String): String? {
        if (!keyPattern.matches(key)) return null
        val file = File(dataDir, "$key.json")
        if (!file.exists()) return null
        return try {
            file.readText()
        } catch (error: IOException) {
            null
        }
    }

    private fun installedContentVersion(): String {
        if (overlayIsCurrent()) overlayContentVersion()?.let { return it }
        return embeddedContentVersion() ?: "unknown"
    }

    private fun overlayManifest(): JSONObject? {
        val manifest = File(contentDir, "version.json")
        if (!manifest.exists()) return null
        return try {
            JSONObject(manifest.readText())
        } catch (ignored: Exception) {
            null
        }
    }

    /**
     * A downloaded pack may shadow the embedded bank only if it belongs to this
     * subject/package and is not older than the bank inside the APK. A foreign
     * or stale overlay is ignored (the embedded content is served instead).
     */
    private fun overlayIsCurrent(): Boolean {
        val manifest = overlayManifest()
        if (UpdateFeed.overlayError(manifest) != null) return false
        val overlay = manifest!!.optString("contentVersion")
        val embedded = embeddedContentVersion() ?: return true
        return ContentVersions.compare(overlay, embedded) >= 0
    }

    private fun overlayContentVersion(): String? =
        overlayManifest()?.optString("contentVersion")?.takeIf { ContentVersions.isValid(it) }

    private fun embeddedContentVersion(): String? {
        return try {
            val text = activity.assets.open("webapp/content/version.json")
                .bufferedReader().use { it.readText() }
            JSONObject(text).optString("contentVersion").takeIf { it.isNotBlank() }
        } catch (error: Exception) {
            null
        }
    }

    companion object {
        private const val TAG = "CTRussianBridge"
    }
}


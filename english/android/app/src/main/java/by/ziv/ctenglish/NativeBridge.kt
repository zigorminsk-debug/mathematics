package by.ziv.ctenglish

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
 * filesDir/content/<name>.json      content packs downloaded on top of the assets
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
            put("repo", "https://github.com/zigorminsk-debug/mathematics")
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

    /**
     * Downloads a newer content pack (version.json + task banks) from the
     * subject-scoped feed, verifies every SHA-256 and installs it over the
     * embedded bank. The student's progress is never touched.
     *
     * Пустой ``baseUrl`` означает «реши сам»: адрес берётся из Releases API по
     * последнему выпуску английского ([ReleaseFeed]). Общий `/releases/latest`
     * репозитория содержит математику и не используется никогда.
     */
    /** Asynchronous bridge: an offline check must not block the WebView UI. */
    @JavascriptInterface
    fun checkUpdatesAsync(baseUrl: String, currentVersion: String, requestId: String) {
        if (!keyPattern.matches(requestId)) return
        updateExecutor.execute {
            val response = checkUpdates(baseUrl, currentVersion)
            mainHandler.post {
                if (!activity.isFinishing && !activity.isDestroyed) {
                    // quote both arguments; response is data, never executable JS
                    evaluateJavascript("window.CT && window.CT.bridge.onUpdateResult(" +
                        JSONObject.quote(requestId) + "," + JSONObject.quote(response) + ");")
                }
            }
        }
    }

    @Synchronized
    @JavascriptInterface
    fun checkUpdates(baseUrl: String, currentVersion: String): String {
        val requested = baseUrl.ifBlank { resolveUpdateBase() ?: "" }
        val base = requested.trimEnd('/')
        val installedVersion = installedContentVersion()
        val current = if (ContentVersions.compare(currentVersion, installedVersion) > 0) {
            currentVersion
        } else installedVersion
        var staged: File? = null
        return try {
            if (base.isEmpty()) throw IOException("no published English release found")
            if (!base.startsWith("https://")) throw IllegalArgumentException("update feed must use HTTPS")
            if (!base.startsWith(ReleaseFeed.downloadBase(""))) {
                throw IllegalArgumentException("update feed must belong to this subject's releases")
            }
            val manifest = httpGet("$base/version.json")
            val manifestJson = JSONObject(manifest.toString(Charsets.UTF_8))
            // Чужой предмет отвергается целиком: банк математики не должен
            // попасть ни в кэш, ни в интерфейс английского.
            if (!ReleaseFeed.manifestMatches(manifestJson.optString("subject"),
                    manifestJson.optString("package"))) {
                return result("error", current, 0, "manifest belongs to another subject")
            }
            val version = manifestJson.optString("contentVersion")
            if (!ContentVersions.isValid(version)) {
                return result("error", current, 0, "manifest has no valid contentVersion")
            }
            // A new APK can be ahead of releases/latest; never downgrade its bank.
            if (ContentVersions.compare(version, current) <= 0) {
                return result("uptodate", current, 0, "content is up to date")
            }
            val files = manifestJson.optJSONObject("files")
                ?: return result("error", current, 0, "manifest has no files")
            if (!files.has("bank.json")) return result("error", current, 0, "manifest has no bank")
            val pack = File.createTempFile("content-update-", "", activity.filesDir)
            staged = pack
            if (!pack.delete() || !pack.mkdir()) throw IOException("cannot create staging directory")
            val names = files.keys()
            var count = 0
            while (names.hasNext()) {
                val fileName = names.next()
                val stem = fileName.removeSuffix(".json")
                if (!fileName.endsWith(".json") || fileName == "version.json" || !keyPattern.matches(stem)) {
                    throw IllegalArgumentException("invalid content file name")
                }
                val meta = files.optJSONObject(fileName) ?: throw IllegalArgumentException("file has no metadata")
                val expected = meta.optString("sha256").lowercase(Locale.ROOT)
                if (!expected.matches(Regex("[0-9a-f]{64}"))) throw IllegalArgumentException("missing checksum")
                val body = httpGet("$base/$fileName")
                if (sha256(body) != expected || (meta.has("bytes") && meta.optLong("bytes") != body.size.toLong())) {
                    return result("error", current, 0, "checksum or size mismatch for $fileName")
                }
                JSONObject(body.toString(Charsets.UTF_8)) // reject a truncated/invalid bank
                File(pack, fileName).writeBytes(body)
                count++
            }
            File(pack, "version.json").writeBytes(manifest)
            // Commit only the fully verified pack. Neither network failures nor a
            // bad last checksum may leave a mixture of old and new content.
            synchronized(contentLock) {
                if (contentBackup.exists() && !contentBackup.deleteRecursively()) throw IOException("cannot clear backup")
                if (!contentDir.renameTo(contentBackup)) throw IOException("cannot back up content")
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

    /** Последний опубликованный выпуск английского (через Releases API). */
    private fun resolveUpdateBase(): String? = try {
        ReleaseFeed.feedFrom(httpGet(ReleaseFeed.RELEASES_API).toString(Charsets.UTF_8))
    } catch (error: Exception) {
        Log.w(TAG, "cannot resolve the English release feed: ${error.message}")
        null
    }

    private fun httpGet(url: String): ByteArray {
        val connection = (URL(url).openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            connectTimeout = 15000
            readTimeout = 30000
            setRequestProperty("User-Agent", "CTEnglishTutor/${BuildConfig.VERSION_NAME}")
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
        if (overlayIsCurrent()) {
            overlayContentVersion()?.let { return it }
        }
        return embeddedContentVersion() ?: "unknown"
    }

    /** Скачанный пакет не старше встроенного в APK (или его версию не узнать). */
    private fun overlayIsCurrent(): Boolean {
        val overlay = overlayContentVersion() ?: return true
        val embedded = embeddedContentVersion() ?: return true
        return ContentVersions.compare(overlay, embedded) >= 0
    }

    private fun overlayContentVersion(): String? {
        val manifest = File(contentDir, "version.json")
        if (manifest.exists()) {
            try {
                val version = JSONObject(manifest.readText()).optString("contentVersion")
                if (ContentVersions.isValid(version)) return version
            } catch (ignored: Exception) {
                // fall through to the bank metadata
            }
        }
        val bank = File(contentDir, "bank.json")
        if (bank.exists()) {
            try {
                val version = JSONObject(bank.readText()).optJSONObject("meta")
                    ?.optString("contentVersion").orEmpty()
                if (ContentVersions.isValid(version)) return version
            } catch (ignored: Exception) {
                // version unknown — the caller keeps the overlay
            }
        }
        return null
    }

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
        private const val TAG = "CTEnglishBridge"

        /** Поток обновлений по умолчанию: последний выпуск английского. */
        fun defaultUpdateBase(): String = ReleaseFeed.RELEASES_API
    }
}

/** Convenience for the (unused here) Kotlin copy of the answer checker tests. */
internal fun JSONArray.toStringList(): List<String> =
    (0 until length()).mapNotNull { index -> optString(index).takeIf { it.isNotBlank() } }

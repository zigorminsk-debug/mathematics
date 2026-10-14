package by.ziv.ctmaths

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
import java.io.File
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

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
class NativeBridge(private val activity: Activity) {

    private val dataDir = File(activity.filesDir, "data").apply { mkdirs() }
    private val contentDir = File(activity.filesDir, "content").apply { mkdirs() }
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
            put("overlay", File(contentDir, "version.json").exists())
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

    /** Content of a bank: a downloaded pack wins over the embedded asset. */
    @JavascriptInterface
    fun getContent(name: String): String? {
        if (!keyPattern.matches(name)) return null
        val overlay = File(contentDir, "$name.json")
        if (overlay.exists()) {
            return try {
                overlay.readText()
            } catch (error: IOException) {
                null
            }
        }
        return try {
            activity.assets.open("webapp/content/$name.json").bufferedReader().use { it.readText() }
        } catch (error: IOException) {
            null
        }
    }

    /* -------------------------------------------------------------- update */

    /**
     * Downloads a newer content pack (version.json + task banks) from the release
     * feed, verifies every SHA-256 and installs it over the embedded bank.  The
     * student's progress is never touched.
     */
    @JavascriptInterface
    fun checkUpdates(baseUrl: String, currentVersion: String): String {
        val base = baseUrl.ifBlank { DEFAULT_UPDATE_BASE }.trimEnd('/')
        val current = currentVersion.ifBlank { installedContentVersion() }
        return try {
            val manifest = httpGet("$base/version.json")
            val manifestJson = JSONObject(manifest)
            val version = manifestJson.optString("contentVersion")
            if (version.isBlank()) {
                return result("error", current, 0, "manifest has no contentVersion")
            }
            if (current.isNotBlank() && version == current) {
                return result("uptodate", current, 0, "content is up to date")
            }
            val files = manifestJson.optJSONObject("files") ?: JSONObject()
            var installed = 0
            val names = files.keys()
            while (names.hasNext()) {
                val fileName = names.next()
                val meta = files.optJSONObject(fileName) ?: continue
                val body = httpGet("$base/$fileName")
                val expected = meta.optString("sha256")
                if (expected.isNotBlank() && sha256(body.toByteArray()) != expected.lowercase(Locale.ROOT)) {
                    return result("error", current, installed, "checksum mismatch for $fileName")
                }
                val stem = fileName.removeSuffix(".json")
                File(contentDir, "$stem.json").writeText(body)
                installed++
            }
            result("ok", version, installed, "installed $installed content files")
        } catch (error: IOException) {
            result("offline", current, 0, error.message ?: "network unavailable")
        } catch (error: Exception) {
            result("error", current, 0, error.message ?: "unexpected error")
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

    private fun httpGet(url: String): String {
        val connection = (URL(url).openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            connectTimeout = 15000
            readTimeout = 30000
            setRequestProperty("User-Agent", "CTMathsTutor/${BuildConfig.VERSION_NAME}")
            instanceFollowRedirects = true
        }
        try {
            if (connection.responseCode !in 200..299) {
                throw IOException("HTTP ${connection.responseCode} for $url")
            }
            return connection.inputStream.bufferedReader().use { it.readText() }
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

    fun shutdown() = Unit

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
        val overlay = File(contentDir, "version.json")
        if (overlay.exists()) {
            try {
                return JSONObject(overlay.readText()).optString("contentVersion")
            } catch (ignored: Exception) {
                // fall through to the embedded version
            }
        }
        return try {
            val text = activity.assets.open("webapp/content/version.json")
                .bufferedReader().use { it.readText() }
            JSONObject(text).optString("contentVersion")
        } catch (error: Exception) {
            "unknown"
        }
    }

    companion object {
        private const val TAG = "CTMathsBridge"
        const val DEFAULT_UPDATE_BASE =
            "https://github.com/zigorminsk-debug/mathematics/releases/latest/download"
    }
}

/** Convenience for the (unused here) Kotlin copy of the answer checker tests. */
internal fun JSONArray.toStringList(): List<String> =
    (0 until length()).mapNotNull { index -> optString(index).takeIf { it.isNotBlank() } }

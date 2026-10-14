package by.ziv.ctrussian

import android.annotation.SuppressLint
import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.ViewGroup
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import androidx.webkit.WebViewAssetLoader
import kotlin.math.roundToInt

/**
 * The whole interface of the Android build lives in the shared web application
 * (``assets/webapp``) that is also used by the Windows build.  The activity is a
 * thin host: it serves the assets through [WebViewAssetLoader] (so the page has a
 * proper https origin and can use fetch/XHR) and exposes [NativeBridge] to the
 * page as ``window.CTNative``.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var bridge: NativeBridge

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()

        bridge = NativeBridge(this) { script -> webView.evaluateJavascript(script, null) }
        webView = WebView(this)
        webView.layoutParams = ViewGroup.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT
        )
        with(webView.settings) {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            mediaPlaybackRequiresUserGesture = true
            cacheMode = WebSettings.LOAD_DEFAULT
            // Respect the system font scale (e.g. 1.3): large text must stay readable.
            textZoom = (resources.configuration.fontScale * 100).roundToInt().coerceIn(85, 200)
            setSupportZoom(false)
        }
        webView.addJavascriptInterface(bridge, "CTNative")
        webView.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse? =
                assetLoader.shouldInterceptRequest(request.url)

            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val url = request.url.toString()
                // external links (contacts, WhatsApp, source code) open in the system apps
                if (url.startsWith("mailto:") || url.startsWith("tel:") ||
                    url.startsWith("sms:") || (!url.startsWith(HOST) && !url.startsWith("about:"))
                ) {
                    openExternally(url)
                    return true
                }
                return false
            }
        }

        setContentView(webView)
        applyKeepScreenOn()
        webView.loadUrl("https://$HOST/assets/webapp/index.html")

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                // let the page decide: it navigates back inside the SPA, and only
                // when it is already at the start does the activity finish
                webView.evaluateJavascript("window.CT && window.CT.onAndroidBack && window.CT.onAndroidBack()") { result ->
                    if (result == "\"exit\"") finish()
                }
            }
        })
    }

    override fun onResume() {
        super.onResume()
        bridge.applyKeepScreenOnFromSettings()
    }

    private fun applyKeepScreenOn() {
        webView.keepScreenOn = true
    }

    private fun openExternally(url: String) {
        try {
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
        } catch (ignored: ActivityNotFoundException) {
            // nothing to handle the link — stay in the app
        }
    }

    override fun onDestroy() {
        bridge.shutdown()
        super.onDestroy()
    }

    companion object {
        /** Must match the host used by [WebViewAssetLoader]. */
        const val HOST = "appassets.androidplatform.net"
    }
}

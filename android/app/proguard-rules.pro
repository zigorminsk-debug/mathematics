# The web interface talks to the bridge through reflection-like @JavascriptInterface
# annotations, so the bridge and its methods must be kept.
-keepclassmembers class by.ziv.ctmaths.NativeBridge {
    public *;
}
-keep class by.ziv.ctmaths.NativeBridge { *; }
-keepattributes JavascriptInterface

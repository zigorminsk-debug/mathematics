# The web interface talks to the bridge through reflection-like @JavascriptInterface
# annotations, so the bridge and its methods must be kept.
-keepclassmembers class by.ziv.ctrussian.NativeBridge {
    public *;
}
-keep class by.ziv.ctrussian.NativeBridge { *; }
-keepattributes JavascriptInterface

import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// ---- constant release key -------------------------------------------------
// The project ships a fixed PKCS#12 key so that every build installs over the
// previous one (Android requires the same certificate).  CI may override the
// values through environment variables / GitHub secrets without touching the
// build script.
val keystorePropertiesFile = rootProject.file("keystore/keystore.properties")
val keystoreProperties = Properties().apply {
    if (keystorePropertiesFile.exists()) {
        keystorePropertiesFile.inputStream().use { load(it) }
    }
}

fun keystoreValue(envName: String, propertyName: String): String? =
    System.getenv(envName) ?: keystoreProperties.getProperty(propertyName)

val releaseStoreFile = keystoreValue("ANDROID_KEYSTORE_FILE", "storeFile")
val releaseStorePassword = keystoreValue("ANDROID_KEYSTORE_PASSWORD", "storePassword")
val releaseKeyAlias = keystoreValue("ANDROID_KEY_ALIAS", "keyAlias")
val releaseKeyPassword = keystoreValue("ANDROID_KEY_PASSWORD", "keyPassword")
val releaseStoreType = keystoreValue("ANDROID_KEYSTORE_TYPE", "storeType") ?: "PKCS12"

// The same versionCode in local, CI and release builds. Workflow run numbers
// have separate counters and used to produce APK downgrades between channels.
val contentVersion = rootProject.file("../VERSION").readText().trim()

fun derivedVersionCode(version: String): Int {
    val match = Regex("(20[0-9]{2})\\.([0-9]{1,2})\\.([0-9]{1,2})").matchEntire(version)
        ?: error("VERSION must use YYYY.month.patch (2000–2099; patch 0–99)")
    val year = match.groupValues[1].toInt()
    val month = match.groupValues[2].toInt()
    val patch = match.groupValues[3].toInt()
    require(month in 1..12) { "VERSION month must be 1–12" }
    return (year - 2000) * 10000 + month * 100 + patch
}

val versionCodeFromFile = derivedVersionCode(contentVersion)
val appVersionCode = System.getenv("VERSION_CODE")?.let {
    it.toIntOrNull() ?: error("VERSION_CODE must be a positive integer")
} ?: versionCodeFromFile
require(appVersionCode in versionCodeFromFile..2100000000) { "VERSION_CODE must not decrease" }
val appVersionName = System.getenv("VERSION_NAME")?.removePrefix("v") ?: contentVersion
require(appVersionName == contentVersion) { "VERSION_NAME must match VERSION" }


android {
    namespace = "by.ziv.ctphysics"
    compileSdk = 34

    defaultConfig {
        applicationId = "by.ziv.ctphysics"
        minSdk = 24
        targetSdk = 34
        versionCode = appVersionCode
        versionName = appVersionName
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        resValue("string", "developer_name", "Zakharevich Igor")
        resValue("string", "developer_email", "ziv@csl.by")
        resValue("string", "developer_phone", "+3753371412")
    }

    signingConfigs {
        if (releaseStoreFile != null && releaseStorePassword != null) {
            create("release") {
                storeFile = rootProject.file("keystore/$releaseStoreFile")
                storePassword = releaseStorePassword
                keyAlias = releaseKeyAlias
                keyPassword = releaseKeyPassword
                storeType = releaseStoreType
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            isShrinkResources = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            if (signingConfigs.findByName("release") != null) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
        debug {
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
            // Тот же постоянный ключ, что и у релиза: debug-ключ, который Gradle
            // сам генерирует на каждой машине и на каждом CI-раннере, разный,
            // поэтому debug-сборка с нового раннера не вставала поверх прежней.
            // Пакет у debug всё равно отдельный (by.ziv.ctphysics.debug) — поверх
            // релиза он не встанет по определению Android, только рядом.
            if (signingConfigs.findByName("release") != null) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        buildConfig = true
    }

    packaging {
        resources.excludes += setOf("META-INF/AL2.0", "META-INF/LGPL2.1")
    }

    testOptions {
        unitTests.isReturnDefaultValues = true
    }

    lint {
        abortOnError = false
    }
}

dependencies {
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.webkit:webkit:1.11.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")

    testImplementation("junit:junit:4.13.2")
    // unitTests.isReturnDefaultValues = true stubs every org.json method, so a real
    // implementation is required on the test classpath for the parity vectors
    testImplementation("org.json:json:20240303")
}

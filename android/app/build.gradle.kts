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

android {
    namespace = "by.ziv.ctmaths"
    compileSdk = 34

    defaultConfig {
        applicationId = "by.ziv.ctmaths"
        minSdk = 24
        targetSdk = 34
        versionCode = (System.getenv("VERSION_CODE") ?: "1").toInt()
        versionName = System.getenv("VERSION_NAME") ?: "1.0.0"
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
}

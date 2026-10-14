package by.ziv.ctphysics

import org.json.JSONArray

/**
 * Канал обновления банка заданий физики.
 *
 * Общий `releases/latest/download` в репозитории отдаёт **математику**, поэтому
 * физика никогда его не читает: приложение спрашивает Releases API, выбирает
 * самый новый стабильный выпуск своей семьи тегов и скачивает файлы по ссылке
 * конкретной версии. Манифест обязан быть помечен своим предметом — иначе банк
 * математики попал бы в приложение по физике (у предметов разная статистика,
 * разные задания и разные настройки).
 *
 * Логика вынесена из [NativeBridge] в чистый Kotlin: её проверяют юнит-тесты
 * (`ReleaseFeedTest`) и те же правила действуют в Windows-версии
 * (`windows/store.go` → `ResolveFeed`) и в публикаторе (`tools/subject.py`).
 */
internal object ReleaseFeed {

    /** Предмет этого приложения: чужой банк не принимается. */
    const val SUBJECT = "physics"

    /** Семья тегов выпусков: `physics-v2026.10.1`. */
    const val TAG_PREFIX = "physics-v"

    /** Префикс пакета: `by.ziv.ctphysics`, `by.ziv.ctphysics.debug`. */
    const val PACKAGE_PREFIX = "by.ziv.ctphysics"

    const val REPOSITORY = "zigorminsk-debug/mathematics"

    /** Список выпусков. Общий `/releases/latest` не используется намеренно. */
    const val RELEASES_API =
        "https://api.github.com/repos/$REPOSITORY/releases?per_page=30"

    /** Ссылка на файлы конкретного выпуска (неизменяемая). */
    fun downloadBase(tag: String): String =
        "https://github.com/$REPOSITORY/releases/download/$tag"

    /**
     * Самый новый стабильный выпуск физики из ответа Releases API.
     *
     * Пропускаются черновики, предвыпуски и выпуски других предметов
     * (например, математический `v2026.10.8`). `null` — если физики ещё нет.
     */
    fun newestTag(releasesJson: String): String? {
        val array = try {
            JSONArray(releasesJson)
        } catch (error: Exception) {
            return null
        }
        var best: String? = null
        var bestVersion = ""
        for (index in 0 until array.length()) {
            val release = array.optJSONObject(index) ?: continue
            if (release.optBoolean("draft", false) || release.optBoolean("prerelease", false)) continue
            val tag = release.optString("tag_name")
            if (!tag.startsWith(TAG_PREFIX)) continue
            val version = tag.removePrefix(TAG_PREFIX)
            if (!ContentVersions.isValid(version)) continue
            if (best == null || ContentVersions.compare(version, bestVersion) > 0) {
                best = tag
                bestVersion = version
            }
        }
        return best
    }

    /** Подходит ли манифест этому предмету: чужой предмет отвергается целиком. */
    fun manifestMatches(subject: String, packageName: String): Boolean =
        subject == SUBJECT && packageName.startsWith(PACKAGE_PREFIX)

    /** Ссылка потока обновлений по ответу Releases API. */
    fun feedFrom(releasesJson: String): String? =
        newestTag(releasesJson)?.let { downloadBase(it) }
}

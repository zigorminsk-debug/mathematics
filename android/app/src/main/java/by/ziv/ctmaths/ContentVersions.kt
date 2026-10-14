package by.ziv.ctmaths

/** Numeric dotted versions: 2026.10.3 is newer than 2026.9.9. */
internal object ContentVersions {
    fun isValid(version: String): Boolean = version.matches(Regex("[0-9]+(\\.[0-9]+)*")) &&
        version.split(".").all { it.toLongOrNull() != null }

    fun compare(left: String, right: String): Int {
        val a = left.split(".").map { it.toLongOrNull() ?: 0L }
        val b = right.split(".").map { it.toLongOrNull() ?: 0L }
        for (index in 0 until maxOf(a.size, b.size)) {
            val comparison = (a.getOrNull(index) ?: 0L).compareTo(b.getOrNull(index) ?: 0L)
            if (comparison != 0) return comparison
        }
        return 0
    }
}

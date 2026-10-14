package by.ziv.ctrussian

import org.junit.Assert.*
import org.junit.Test

class ContentVersionsTest {
    @Test fun numericOrder() {
        assertTrue(ContentVersions.compare("2026.10.3", "2026.9.99") > 0)
        assertTrue(ContentVersions.compare("2026.10.2", "2026.10.3") < 0)
        assertEquals(0, ContentVersions.compare("2026.10.3", "2026.10.3"))
        assertEquals(0, ContentVersions.compare("2026.10", "2026.10.0"))
        assertTrue(ContentVersions.compare("2027.1.0", "2026.12.99") > 0)
    }

    @Test fun onlyNumericVersions() {
        assertTrue(ContentVersions.isValid("2026.10.3"))
        assertFalse(ContentVersions.isValid(""))
        assertFalse(ContentVersions.isValid("2026.10.x"))
        assertFalse(ContentVersions.isValid("2026..3"))
        assertFalse(ContentVersions.isValid("2026.-1.3"))
    }
}

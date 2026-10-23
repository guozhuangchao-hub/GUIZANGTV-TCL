package io.github.op7418.guizangtv;

import org.junit.Test;
import static org.junit.Assert.*;

public class HomeItemsTest {
    @Test public void sourceShortcutCanSurviveSavedOrderReload() {
        assertTrue(HomeItems.validId("control:inputs"));
        assertTrue(HomeItems.validId("com.tcl.cyberui"));
    }
    @Test public void unknownControlCommandsCannotEnterSavedOrder() {
        assertFalse(HomeItems.validId("control:reboot"));
        assertFalse(HomeItems.validId("control:inputs/../../settings"));
    }
}

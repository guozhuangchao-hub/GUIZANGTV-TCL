package io.github.op7418.guizangtv;

import org.junit.Test;
import static org.junit.Assert.*;

public class TclWakePolicyTest {
    @Test public void firstBindingAfterColdBootCanEnter() {
        assertTrue(TclWakePolicy.bootstrap(true, 28, 27, 40000, false));
    }
    @Test public void inspectionRebindCannotRepeatBootEntry() {
        assertFalse(TclWakePolicy.bootstrap(true, 28, 28, 50000, false));
    }
    @Test public void updateWhileWatchingCannotTriggerBootEntry() {
        assertFalse(TclWakePolicy.bootstrap(true, 28, 27, 50000, true));
    }
    @Test public void disabledOrLateOrUnknownBindingCannotEnter() {
        assertFalse(TclWakePolicy.bootstrap(false, 28, 27, 40000, false));
        assertFalse(TclWakePolicy.bootstrap(true, -1, -1, 40000, false));
        assertFalse(TclWakePolicy.bootstrap(true, 28, 27, 180000, false));
        assertFalse(TclWakePolicy.bootstrap(true, 28, 27, -1, false));
    }
    @Test public void coldBootResumeDoesNotOverrideBootSchedule() {
        assertFalse(TclWakePolicy.schedule(true, 27, 26, 45000, -1));
    }
    @Test public void standbyAfterCompletedBootCanEnter() {
        assertTrue(TclWakePolicy.schedule(true, 27, 27, 120000, -1));
    }
    @Test public void duplicateResumeBroadcastDoesNotRestartTwice() {
        assertFalse(TclWakePolicy.schedule(true, 27, 27, 120500, 120000));
        assertTrue(TclWakePolicy.schedule(true, 27, 27, 135000, 120000));
    }
    @Test public void disabledUnknownBootAndInvalidClockCannotEnter() {
        assertFalse(TclWakePolicy.schedule(false, 27, 27, 120000, -1));
        assertFalse(TclWakePolicy.schedule(true, -1, -1, 120000, -1));
        assertFalse(TclWakePolicy.schedule(true, 27, 27, -1, -1));
    }
}

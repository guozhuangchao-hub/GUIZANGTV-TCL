package io.github.op7418.guizangtv;

final class TclWakePolicy {
    private TclWakePolicy() { }
    static boolean bootstrap(boolean enabled, int boot, int checked, long uptime, boolean updatedThisBoot) {
        return enabled && boot >= 0 && boot != checked && uptime >= 0 && uptime < 180_000 && !updatedThisBoot;
    }
    static boolean schedule(boolean enabled, int boot, int enteredBoot, long now, long previous) {
        return enabled && boot >= 0 && boot == enteredBoot && now >= 0
                && (previous < 0 || now - previous >= 10_000);
    }
}

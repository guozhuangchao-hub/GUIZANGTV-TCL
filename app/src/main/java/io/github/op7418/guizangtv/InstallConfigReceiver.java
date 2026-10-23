package io.github.op7418.guizangtv;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import java.util.ArrayList;
import java.util.List;

/** ADB-only installer setup; the manifest requires WRITE_SECURE_SETTINGS on the sender. */
public final class InstallConfigReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context c, Intent i) {
        android.content.SharedPreferences.Editor e = c.getSharedPreferences("boot-start", 0).edit();
        if (i.hasExtra("guard")) e.putBoolean("guard-mode", i.getBooleanExtra("guard", false));
        if (i.hasExtra("enabled")) e.putBoolean("enabled", i.getBooleanExtra("enabled", false));
        if (!e.commit()) { setResultCode(1); setResultData("settings_save_failed"); return; }
        TclHomeGuard.sync(c);
        // Explicit opt-in: only append these already-installed packages, never replace saved order.
        if (i.getBooleanExtra("pin_media", false)) {
            HomeItems items = new HomeItems(c); List<String> next = new ArrayList<>(items.order);
            for (String pkg : new String[]{"com.mygithub0.tvbox0.apei583", "com.github.tvbox.osc.jun"}) {
                if (next.size() < 9 && !next.contains(pkg) && items.names.containsKey(pkg)) next.add(pkg);
            }
            items.save(next);
        }
        setResultData("enabled=" + BootStart.enabled(c) + " guard_mode=" + TvControls.guardMode(c));
    }
}

package io.github.op7418.guizangtv;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.util.Log;

/** Interfaces inspected on the owner's TCL 85J8L / Android 11. */
final class TclControls {
    private TclControls() { }
    static boolean enabled() { return "tcl_mt5879_cn".equals(Build.MODEL) || "TCL".equalsIgnoreCase(Build.MANUFACTURER)
            || "TCL".equalsIgnoreCase(Build.BRAND) || "FFALCON".equalsIgnoreCase(Build.BRAND); }

    private static Intent activity(Context context, String pkg, String name) {
        if (!enabled()) return null;
        ComponentName component = new ComponentName(pkg, name);
        try {
            ActivityInfo info = context.getPackageManager().getActivityInfo(component, 0);
            if (!info.enabled || !info.exported || (info.permission != null
                    && context.checkSelfPermission(info.permission) != PackageManager.PERMISSION_GRANTED)) return null;
            return new Intent(Intent.ACTION_MAIN).setComponent(component)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        } catch (PackageManager.NameNotFoundException unavailable) { return null; }
    }

    static Intent settings(Context context) {
        return activity(context, "com.tcl.settings", "com.tcl.settings.ui.MainActivity");
    }

    static boolean stockHome(Context context) {
        TclHomeGuard.allowStockVisit();
        return launch(context, activity(context, "com.tcl.cyberui", "com.tcl.cyberui.MainActivity"));
    }

    static boolean showInputs(Context context) {
        if (!enabled()) return false;
        ComponentName component = new ComponentName("com.tcl.settings", "com.tcl.settings.ShowWindowService");
        try {
            ServiceInfo info = context.getPackageManager().getServiceInfo(component, 0);
            if (!info.enabled || !info.exported || (info.permission != null
                    && context.checkSelfPermission(info.permission) != PackageManager.PERMISSION_GRANTED)) return false;
            context.startService(new Intent("com.tcl.settings.SHOW_WINDOW").setComponent(component)
                    .putExtra("flag", 1).putExtra("Type", "Source"));
            return true;
        } catch (PackageManager.NameNotFoundException | RuntimeException unavailable) {
            Log.w("GuiZangTcl", "Source panel unavailable", unavailable);
            return false;
        }
    }

    private static boolean launch(Context context, Intent intent) {
        if (intent == null) return false;
        try { context.startActivity(intent); return true; }
        catch (RuntimeException unavailable) {
            Log.w("GuiZangTcl", "System entry unavailable", unavailable);
            return false;
        }
    }
}

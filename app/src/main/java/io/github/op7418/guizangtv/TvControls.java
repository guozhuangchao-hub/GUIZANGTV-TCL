package io.github.op7418.guizangtv;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.media.tv.TvContract;
import android.media.tv.TvInputInfo;
import android.media.tv.TvInputManager;
import android.provider.Settings;
import android.util.Log;
import java.util.ArrayList;
import java.util.List;

/** Capability-based Android TV fallbacks; vendor source numbers are never guessed. */
final class TvControls {
    private TvControls() { }
    static boolean guardMode(Context c) {
        return TclControls.enabled() || c.getSharedPreferences("boot-start", 0).getBoolean("guard-mode", false);
    }
    static List<ComponentName> stockHomes(Context c) {
        List<ComponentName> homes = new ArrayList<>();
        for (ResolveInfo r : c.getPackageManager().queryIntentActivities(
                new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME), PackageManager.MATCH_DEFAULT_ONLY)) {
            ActivityInfo a = r.activityInfo;
            if (!a.packageName.equals(c.getPackageName()) && a.enabled && r.priority >= 0)
                homes.add(new ComponentName(a.packageName, a.name));
        }
        if (TclControls.enabled()) {
            ComponentName tcl = new ComponentName("com.tcl.cyberui", "com.tcl.cyberui.MainActivity");
            if (!homes.contains(tcl)) homes.add(tcl);
        }
        return homes;
    }
    static boolean safeStart(Context c, Intent i) {
        try {
            ResolveInfo r = c.getPackageManager().resolveActivity(i, 0);
            if (r == null || !r.activityInfo.enabled || !r.activityInfo.exported) return false;
            String permission = r.activityInfo.permission;
            if (permission != null && c.checkSelfPermission(permission) != PackageManager.PERMISSION_GRANTED) return false;
            c.startActivity(i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)); return true;
        } catch (RuntimeException error) { Log.w("GuiZangTv", "System entry unavailable", error); return false; }
    }
    static Intent settings(Context c) {
        Intent i = TclControls.enabled() ? TclControls.settings(c) : XiaomiControls.settings(c, Settings.ACTION_SETTINGS);
        return i == null ? new Intent(Settings.ACTION_SETTINGS) : i;
    }
    static boolean stockHome(Context c) {
        TclHomeGuard.allowStockVisit();
        if (TclControls.enabled() && TclControls.stockHome(c)) return true;
        if (XiaomiControls.enabled() && XiaomiControls.startStockHome(c,
                new ComponentName("com.mitv.tvhome", "com.mitv.tvhome.MainActivity"))) return true;
        for (ComponentName home : stockHomes(c))
            if (safeStart(c, new Intent(Intent.ACTION_MAIN).setComponent(home))) return true;
        return false;
    }
    static boolean showInputs(Activity c) {
        if (TclControls.enabled() && TclControls.showInputs(c)) return true;
        if (XiaomiControls.enabled() && XiaomiControls.showInputs(c)) return true;
        TvInputManager manager = c.getSystemService(TvInputManager.class);
        List<TvInputInfo> inputs = new ArrayList<>();
        try {
            if (manager != null) for (TvInputInfo i : manager.getTvInputList())
                if (i.getType() == TvInputInfo.TYPE_HDMI && i.getParentId() == null) inputs.add(i);
        } catch (RuntimeException unavailable) { Log.w("GuiZangTv", "TV input list unavailable", unavailable); }
        if (!inputs.isEmpty()) {
            String[] labels = new String[inputs.size()];
            for (int n = 0; n < inputs.size(); n++) labels[n] = inputs.get(n).loadLabel(c).toString();
            new AlertDialog.Builder(c).setTitle("信号源").setItems(labels, (d, n) -> {
                if (!safeStart(c, new Intent(Intent.ACTION_VIEW,
                        TvContract.buildChannelUriForPassthroughInput(inputs.get(n).getId()))))
                    android.widget.Toast.makeText(c, "电视未提供可用的信号源播放入口", android.widget.Toast.LENGTH_LONG).show();
            }).setNegativeButton("返回", null).show();
            return true;
        }
        // Tigris's Skyworth/Coocaa fallback; checked per component, still not device-tested here.
        ComponentName picker = new ComponentName("com.tianci.movieplatform",
                "com.ccos.cooui.homepage.tvsource.SourceDialogActivity");
        return safeStart(c, new Intent("coocaa.intent.action.SOURCE_DIALOG").setComponent(picker));
    }
}

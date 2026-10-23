package io.github.op7418.guizangtv;

import android.app.Activity;
import android.app.AlarmManager;
import android.app.AlertDialog;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.SystemClock;
import android.provider.Settings;
import android.util.Log;
import android.widget.Toast;

/** Opt-in boot entry, with a TCL-only event-driven home guard. */
public final class BootStart {
    private static final String PREFS = "boot-start";
    private static final String EXTRA = "guizang.boot-count";
    private static final String WAKE = "guizang.from-standby";
    private static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }
    static boolean enabled(Context c) { return prefs(c).getBoolean("enabled", false); }
    private static int bootCount(Context c) {
        return Settings.Global.getInt(c.getContentResolver(), Settings.Global.BOOT_COUNT, -1);
    }
    static void enter(Context a) {
        int boot = bootCount(a);
        String reason = BootStartPolicy.skipReason(XiaomiControls.enabled() || TvControls.guardMode(a), enabled(a), boot, prefs(a).getInt("attempted", -1),
                SystemClock.elapsedRealtime());
        if (reason != null) { Log.i("GuiZangBoot", reason); return; }
        if (TvControls.guardMode(a) && !Settings.canDrawOverlays(a)) {
            status(a, "尚未允许显示在其他应用上层，无法从开机后台进入桌面");
            return;
        }
        if (!prefs(a).edit().putInt("attempted", boot).putString("status", "系统已调用启动入口，等待界面确认").commit()) return;
        openHome(a, boot, false);
    }
    private static void openHome(Context a, int boot, boolean wake) {
        try {
            a.startActivity(new Intent(a, FrameHomeActivity.class)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)
                    .putExtra(EXTRA, boot).putExtra(WAKE, wake));
        } catch (RuntimeException error) {
            status(a, "启动失败：" + error.getClass().getSimpleName());
            Log.w("GuiZangBoot", "Launch rejected", error);
        }
    }
    static void scheduleTcl(Context c, boolean wake) {
        if (!enabled(c)) return;
        if (TclHomeGuard.running()) { TclHomeGuard.bootOrWake(); return; }
        long now = SystemClock.elapsedRealtime();
        if (wake && !TclWakePolicy.schedule(enabled(c), bootCount(c), prefs(c).getInt("attempted", -1),
                now, prefs(c).getLong("wake-scheduled", -1))) return;
        if (wake) prefs(c).edit().putLong("wake-scheduled", now).apply();
        else prefs(c).edit().remove("wake-scheduled").remove("wake-entered").apply();
        Intent intent = new Intent(c, TclBootReceiver.class).setAction(TclBootReceiver.ENTER)
                .putExtra("wake", wake).putExtra("wake-id", now);
        PendingIntent pending = PendingIntent.getBroadcast(c, wake ? 1 : 0, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        // This firmware forces its own HOME about 14 s after BOOT_COMPLETED. Enter once after it.
        AlarmManager alarm = c.getSystemService(AlarmManager.class);
        long at = now + (wake ? 3_500 : 20_000);
        if (android.os.Build.VERSION.SDK_INT < 31 || alarm.canScheduleExactAlarms())
            alarm.setExact(AlarmManager.ELAPSED_REALTIME_WAKEUP, at, pending);
        else alarm.setAndAllowWhileIdle(AlarmManager.ELAPSED_REALTIME_WAKEUP, at, pending);
        status(c, wake ? "待机恢复完成，准备进入桌面" : "等待 TCL 完成系统启动后进入桌面");
    }
    static void scheduledTclEntry(Context c, boolean wake, long id) {
        if (!enabled(c)) return;
        if (!wake) { enter(c); return; }
        int boot = bootCount(c);
        if (boot < 0 || prefs(c).getInt("attempted", -1) != boot
                || id <= prefs(c).getLong("wake-entered", -1)) return;
        if (!Settings.canDrawOverlays(c)) { status(c, "缺少后台进入桌面的权限"); return; }
        if (!prefs(c).edit().putLong("wake-entered", id).commit()) return;
        openHome(c, boot, true);
    }
    private static boolean configured(Context c) {
        if (TvControls.guardMode(c)) return Settings.canDrawOverlays(c);
        return c.getPackageName().equals(Settings.System.getString(c.getContentResolver(), "start_3rd_app"));
    }
    private static void status(Context c, String value) {
        prefs(c).edit().putString("status", value).apply();
        Log.i("GuiZangBoot", value);
    }
    static void confirm(Activity activity) {
        Intent intent = activity.getIntent();
        int boot = intent.getIntExtra(EXTRA, -1);
        if (boot < 0) return;
        intent.removeExtra(EXTRA);
        if (boot == bootCount(activity) && prefs(activity).getInt("attempted", -1) == boot && enabled(activity)) {
            status(activity, intent.getBooleanExtra(WAKE, false) ? "已在待机唤醒后进入桌面" : "已在本次开机后进入桌面");
        }
        intent.removeExtra(WAKE);
    }
    static void settings(Activity a, Runnable systemSettings) {
        new AlertDialog.Builder(a).setTitle("设置")
                .setItems(new String[]{"电视系统设置", "开机自动进入：" + (enabled(a) ? "已开启" : "已关闭")},
                        (d, i) -> { if (i == 0) systemSettings.run(); else show(a); })
                .setNegativeButton("返回", null).show();
    }
    static void show(Activity a) {
        if (TvControls.guardMode(a)) {
            new AlertDialog.Builder(a).setTitle("开机与桌面守护")
                    .setMessage("开机、待机唤醒或返回系统主页时，自动进入归藏。Home 键返回归藏；正在使用其他应用或 HDMI 时不会抢回。可从应用列表主动打开系统原桌面。\n\n"
                            + "需允许自启动及桌面守护。\n守护：" + (TclHomeGuard.running() ? "运行中" : "未运行，需电脑授权")
                            + "\n上次状态：" + prefs(a).getString("status", "尚未进行完整重启测试"))
                    .setPositiveButton(enabled(a) ? "关闭自动进入" : "开启自动进入", (d, which) -> {
                        boolean value = !enabled(a);
                        prefs(a).edit().putBoolean("enabled", value).apply();
                        TclHomeGuard.sync(a);
                        Toast.makeText(a, value ? "已开启，将在下次完整开机后尝试进入" : "已关闭开机自动进入", Toast.LENGTH_LONG).show();
                    }).setNegativeButton("返回", null).show();
            return;
        }
        if (!XiaomiControls.enabled()) {
            new AlertDialog.Builder(a).setTitle("开机自动进入（实验）")
                    .setMessage("目前仅适配 MiTV-MTSU0。其他机型请先使用普通应用入口。")
                    .setNegativeButton("返回", null).show();
            return;
        }
        String state = prefs(a).getString("status", "尚未进行完整重启测试");
        new AlertDialog.Builder(a).setTitle("开机自动进入（实验）")
                .setMessage("仅在完整开机后尝试一次，不接管 Home 键，同次开机的后续调用直接跳过。\n\n"
                        + "由已适配的小米系统调用启动入口；不需要悬浮窗权限。\n\n"
                        + "系统入口：" + (configured(a) ? "已配置" : "尚未配置，需电脑设置") + "\n上次状态：" + state)
                .setPositiveButton(enabled(a) ? "关闭自动进入" : "开启自动进入", (d, which) -> {
                    boolean value = !enabled(a);
                    prefs(a).edit().putBoolean("enabled", value).apply();
                    Toast.makeText(a, value ? (configured(a) ? "已开启，下次完整重启时尝试进入" : "开关已开启，还需按项目文档配置系统入口") : "已关闭开机自动进入", Toast.LENGTH_LONG).show();
                })
                .setNegativeButton("返回", null).show();
    }
    static void dump(Context c, java.io.PrintWriter out) {
        out.println("BootStart: enabled=" + enabled(c) + " configured=" + configured(c)
                + " guard=" + TclHomeGuard.running()
                + " boot=" + bootCount(c) + " attempted=" + prefs(c).getInt("attempted", -1)
                + " status=" + prefs(c).getString("status", "none"));
    }
}

package io.github.op7418.guizangtv;

import android.accessibilityservice.AccessibilityService;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;
import android.os.SystemClock;
import android.provider.Settings;
import android.service.notification.NotificationListenerService;
import android.util.Log;
import android.view.KeyEvent;
import android.view.accessibility.AccessibilityEvent;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Opt-in window guard (legacy component name retained for upgrade), adapted from Tigris/Aerial. See assets/THIRD_PARTY_TCL.txt.
 * No screen content or notifications are read; only the stock home Activity is intercepted. */
public final class TclHomeGuard extends AccessibilityService {
    private final List<ComponentName> stockHomes = new ArrayList<>();
    private boolean stock(String pkg, String cls) {
        return pkg != null && cls != null && stockHomes.contains(new ComponentName(pkg, cls));
    }
    private static TclHomeGuard instance;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private static String lastPackage, lastClass;
    private long allowStockUntil;
    private final Runnable settled = () -> {
        // Like Tigris: binding can happen after HOME's window event. Wait for CEC/app
        // transitions before the one initial fallback; known apps and inputs are left alone.
        if (lastPackage == null || stock(lastPackage, lastClass))
            bringHome("settled stock home or initial binding");
    };
    private final BroadcastReceiver screenOn = new BroadcastReceiver() {
        @Override public void onReceive(Context c, Intent i) { checkOnceSettled(); }
    };

    static boolean running() { return instance != null; }
    static void bootOrWake() { if (instance != null) instance.checkOnceSettled(); }

    /** Preserve the TV assistant and all other enabled services when toggling ours. */
    static void sync(Context c) {
        if (c.checkSelfPermission("android.permission.WRITE_SECURE_SETTINGS")
                != android.content.pm.PackageManager.PERMISSION_GRANTED) return;
        String me = new ComponentName(c, TclHomeGuard.class).flattenToString();
        String old = Settings.Secure.getString(c.getContentResolver(), Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES);
        List<String> entries = new ArrayList<>();
        if (old != null && !old.isEmpty()) entries.addAll(Arrays.asList(old.split(":")));
        boolean found = entries.removeIf(v -> new ComponentName(c, TclHomeGuard.class)
                .equals(ComponentName.unflattenFromString(v)));
        boolean on = BootStart.enabled(c) && TvControls.guardMode(c);
        if (on && TvControls.guardMode(c)) entries.add(me);
        if (found != on) {
            Settings.Secure.putString(c.getContentResolver(), Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES,
                    String.join(":", entries));
        }
        if (on) Settings.Secure.putInt(c.getContentResolver(), Settings.Secure.ACCESSIBILITY_ENABLED, 1);
    }

    static void onHomeResumed(Context c) {
        sync(c);
        if (instance != null) instance.allowStockUntil = 0;
    }

    static void allowStockVisit() {
        if (instance != null) instance.allowStockUntil = SystemClock.uptimeMillis() + 3_600_000;
    }

    @Override protected void onServiceConnected() {
        instance = this;
        stockHomes.clear();
        stockHomes.addAll(TvControls.stockHomes(this));
        if (android.os.Build.VERSION.SDK_INT >= 33) registerReceiver(screenOn, new IntentFilter(Intent.ACTION_SCREEN_ON), Context.RECEIVER_NOT_EXPORTED);
        else registerReceiver(screenOn, new IntentFilter(Intent.ACTION_SCREEN_ON));
        Log.i("GuiZangGuard", "connected");
        int boot = Settings.Global.getInt(getContentResolver(), Settings.Global.BOOT_COUNT, -1);
        android.content.SharedPreferences prefs = getSharedPreferences("boot-start", MODE_PRIVATE);
        boolean updatedThisBoot = true;
        try {
            updatedThisBoot = getPackageManager().getPackageInfo(getPackageName(), 0).lastUpdateTime
                    >= System.currentTimeMillis() - SystemClock.elapsedRealtime();
        } catch (android.content.pm.PackageManager.NameNotFoundException unavailable) { }
        // Accessibility inspection can rebind the same service. Never repeat boot entry then,
        // or during an app update while the viewer is already using another app.
        if (TclWakePolicy.bootstrap(BootStart.enabled(this), boot, prefs.getInt("guard-boot-checked", -1),
                SystemClock.elapsedRealtime(), updatedThisBoot)) {
            prefs.edit().putInt("guard-boot-checked", boot).commit();
            checkOnceSettled();
        }
    }

    private void checkOnceSettled() {
        handler.removeCallbacks(settled);
        handler.postDelayed(settled, 1500);
    }

    private void bringHome(String reason) {
        if (stockHomes.isEmpty()) return;
        PowerManager power = getSystemService(PowerManager.class);
        if (!TvControls.guardMode(this) || !BootStart.enabled(this) || !power.isInteractive()
                || SystemClock.uptimeMillis() < allowStockUntil) return;
        Log.i("GuiZangGuard", reason);
        try {
            startActivity(new Intent(this, FrameHomeActivity.class)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP));
        } catch (RuntimeException error) { Log.w("GuiZangGuard", "start rejected", error); }
    }

    @Override public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event.getEventType() != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED
                || event.getPackageName() == null || event.getClassName() == null) return;
        String pkg = event.getPackageName().toString(), cls = event.getClassName().toString();
        try { getPackageManager().getActivityInfo(new ComponentName(pkg, cls), 0); }
        catch (android.content.pm.PackageManager.NameNotFoundException unavailable) { return; }
        lastPackage = pkg; lastClass = cls;
        handler.removeCallbacks(settled);
        if (stock(pkg, cls)) bringHome("stock home visible");
        else if (!getPackageName().equals(pkg) && stockHomes.stream().noneMatch(h -> h.getPackageName().equals(pkg))) allowStockUntil = 0;
    }

    @Override protected boolean onKeyEvent(KeyEvent event) {
        if (!TvControls.guardMode(this) || !BootStart.enabled(this) || event.getKeyCode() != KeyEvent.KEYCODE_HOME) return false;
        if (event.getAction() == KeyEvent.ACTION_UP && !event.isCanceled()) {
            allowStockUntil = 0;
            bringHome("Home key");
        }
        return true;
    }
    @Override public void onInterrupt() { }
    @Override public void onDestroy() {
        try { unregisterReceiver(screenOn); } catch (IllegalArgumentException notRegistered) { }
        handler.removeCallbacksAndMessages(null);
        if (instance == this) instance = null;
        super.onDestroy();
    }

    /** Android rebinds this after process death. It never reads or handles notifications. */
    public static final class Revival extends NotificationListenerService {
        @Override public void onListenerConnected() {
            Log.i("GuiZangGuard", "revival bound");
            sync(this);
            new Handler(Looper.getMainLooper()).postDelayed(() -> {
                if (running() || !BootStart.enabled(this) || !TvControls.guardMode(this)
                        || checkSelfPermission("android.permission.WRITE_SECURE_SETTINGS")
                        != android.content.pm.PackageManager.PERMISSION_GRANTED) return;
                String old = Settings.Secure.getString(getContentResolver(), Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES);
                if (old == null) return;
                ComponentName me = new ComponentName(this, TclHomeGuard.class);
                List<String> others = new ArrayList<>(Arrays.asList(old.split(":")));
                if (!others.removeIf(v -> me.equals(ComponentName.unflattenFromString(v)))) return;
                Settings.Secure.putString(getContentResolver(), Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES, String.join(":", others));
                // Re-read other services in sync rather than writing a stale saved list.
                new Handler(Looper.getMainLooper()).postDelayed(() -> sync(this), 1500);
            }, 5000);
        }
    }
}

package io.github.op7418.guizangtv;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** One scheduled entry per boot or actual TCL standby-resume event. */
public final class TclBootReceiver extends BroadcastReceiver {
    static final String ENTER = "io.github.op7418.guizangtv.ENTER_AFTER_TCL_START";
    @Override public void onReceive(Context context, Intent intent) {
        if (!TvControls.guardMode(context)) return;
        TclHomeGuard.sync(context);
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) BootStart.scheduleTcl(context, false);
        else if ("tcl.sys.intent.action.STR_RESUME_COMPLETED".equals(intent.getAction())) BootStart.scheduleTcl(context, true);
        else if (ENTER.equals(intent.getAction())) BootStart.scheduledTclEntry(context,
                intent.getBooleanExtra("wake", false), intent.getLongExtra("wake-id", -1));
    }
}

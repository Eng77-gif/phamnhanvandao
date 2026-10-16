package click.phamnhan.fco;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Sau khi khởi động lại máy, đặt lại lịch nhắc đã lưu. */
public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context c, Intent in) {
        if (Intent.ACTION_BOOT_COMPLETED.equals(in.getAction())) Reminders.scheduleAll(c);
    }
}

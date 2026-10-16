package click.phamnhan.fco;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

public class ReminderReceiver extends BroadcastReceiver {
    private static final String CHANNEL = "reminders";

    @Override
    public void onReceive(Context c, Intent in) {
        String id = in.getStringExtra("id");
        String title = in.getStringExtra("title");
        long repeat = in.getLongExtra("repeat", 0);
        if (id == null) return;

        NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
        if (Build.VERSION.SDK_INT >= 26)
            nm.createNotificationChannel(new NotificationChannel(CHANNEL, "Lời nhắc", NotificationManager.IMPORTANCE_DEFAULT));
        Intent open = new Intent(c, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pi = PendingIntent.getActivity(c, 0, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(c, CHANNEL) : new Notification.Builder(c);
        b.setSmallIcon(android.R.drawable.ic_popup_reminder)
                .setContentTitle("FC Online Trợ Lý")
                .setContentText(title)
                .setContentIntent(pi)
                .setAutoCancel(true);
        try { nm.notify(id.hashCode(), b.build()); } catch (SecurityException ignored) {}

        if (repeat > 0) Reminders.schedule(c, id, title, System.currentTimeMillis() + repeat, repeat);
    }
}

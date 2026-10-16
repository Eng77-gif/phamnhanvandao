package click.phamnhan.fco;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.HashSet;
import java.util.Set;

/** Lên lịch thông báo cho lời nhắc. Danh sách nhắc được JS gửi sang dưới dạng JSON [{id,title,at,repeat}]. */
final class Reminders {
    private static final String PREFS = "reminders";
    static final long DAY = 24L * 60 * 60 * 1000;

    static void save(Context c, String json) {
        c.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putString("list", json).apply();
    }

    static long interval(String repeat) {
        if ("daily".equals(repeat)) return DAY;
        if ("weekly".equals(repeat)) return 7 * DAY;
        return 0;
    }

    static PendingIntent intent(Context c, String id, String title, long repeatMs) {
        Intent i = new Intent(c, ReminderReceiver.class);
        i.putExtra("id", id);
        i.putExtra("title", title);
        i.putExtra("repeat", repeatMs);
        return PendingIntent.getBroadcast(c, id.hashCode(), i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    static void schedule(Context c, String id, String title, long at, long repeatMs) {
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, at, intent(c, id, title, repeatMs));
    }

    static void scheduleAll(Context c) {
        SharedPreferences p = c.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        for (String old : p.getStringSet("ids", new HashSet<>())) am.cancel(intent(c, old, "", 0));
        Set<String> ids = new HashSet<>();
        long now = System.currentTimeMillis();
        try {
            JSONArray arr = new JSONArray(p.getString("list", "[]"));
            for (int k = 0; k < arr.length(); k++) {
                JSONObject r = arr.getJSONObject(k);
                String id = r.getString("id");
                long at = r.getLong("at");
                long rep = interval(r.optString("repeat"));
                if (at <= now) {
                    if (rep == 0) continue;
                    at += ((now - at) / rep + 1) * rep;
                }
                schedule(c, id, r.optString("title"), at, rep);
                ids.add(id);
            }
        } catch (Exception ignored) {}
        p.edit().putStringSet("ids", ids).apply();
    }
}

package xyz.doniwirawan.bikefit

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/** Saved results, on this device only — the phone equivalent of the web app's localStorage list. */
object ResultStore {
    private const val PREFS = "bikefit"
    private const val KEY = "history"
    private const val MAX = 20

    fun save(ctx: Context, r: FitResult) {
        val o = JSONObject().apply {
            put("at", System.currentTimeMillis())
            put("bike", r.bike)
            put("strokes", r.strokes)
            put("overall", r.overall.name)
            put("offAxis", r.offAxis)
            r.hipTop?.let { put("hipTop", it.toDouble()) }
            put("angles", JSONObject().apply {
                r.angles.forEach { (k, v) -> if (!v.isNaN()) put(k, v.toDouble()) }
            })
            put("grades", JSONObject().apply { r.grades.forEach { (k, v) -> put(k, v.name) } })
            put("advice", JSONArray(r.advice))
        }
        val list = raw(ctx)
        val next = JSONArray().put(o)
        for (i in 0 until minOf(list.length(), MAX - 1)) next.put(list.get(i))
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .putString(KEY, next.toString()).apply()
    }

    fun raw(ctx: Context): JSONArray =
        runCatching {
            JSONArray(ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(KEY, "[]"))
        }.getOrDefault(JSONArray())

    fun latest(ctx: Context): JSONObject? =
        raw(ctx).let { if (it.length() > 0) it.getJSONObject(0) else null }

    fun clear(ctx: Context) =
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().remove(KEY).apply()
}

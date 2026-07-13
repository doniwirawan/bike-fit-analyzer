package xyz.doniwirawan.bikefit

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.work.CoroutineWorker
import androidx.work.Data
import androidx.work.ForegroundInfo
import androidx.work.WorkerParameters
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlin.math.roundToInt

/**
 * Runs the analysis as a foreground service, so it keeps going when the user leaves the app —
 * this is the whole reason the app is native rather than a wrapper. A browser tab gets throttled
 * or killed in the background; a foreground worker does not.
 *
 * Posts a progress notification while it works, and a result notification when it's done.
 */
class AnalysisWorker(ctx: Context, params: WorkerParameters) : CoroutineWorker(ctx, params) {

    companion object {
        const val KEY_URI = "uri"
        const val KEY_BIKE = "bike"
        const val PROGRESS = "progress"

        const val CH_PROGRESS = "analysis_progress"
        const val CH_DONE = "analysis_done"
        const val NOTIF_PROGRESS = 41
        const val NOTIF_DONE = 42

        fun ensureChannels(ctx: Context) {
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
            val nm = ctx.getSystemService(NotificationManager::class.java)
            nm.createNotificationChannel(
                NotificationChannel(CH_PROGRESS, "Analysis progress", NotificationManager.IMPORTANCE_LOW)
            )
            nm.createNotificationChannel(
                NotificationChannel(CH_DONE, "Analysis finished", NotificationManager.IMPORTANCE_DEFAULT)
            )
        }
    }

    override suspend fun doWork(): androidx.work.ListenableWorker.Result = withContext(Dispatchers.Default) {
        val uriStr = inputData.getString(KEY_URI) ?: return@withContext androidx.work.ListenableWorker.Result.failure()
        val bike = inputData.getString(KEY_BIKE) ?: "road_endurance"
        ensureChannels(applicationContext)

        setForeground(foregroundInfo(0))
        try {
            val result = Analyzer(applicationContext).analyze(Uri.parse(uriStr), bike) { p ->
                val pct = (p * 100).roundToInt()
                setProgressAsync(Data.Builder().putInt(PROGRESS, pct).build())
                runCatching { NotificationManagerCompat.from(applicationContext)
                    .notify(NOTIF_PROGRESS, progressNotification(pct)) }
            }
            ResultStore.save(applicationContext, result)
            notifyDone(result)
            androidx.work.ListenableWorker.Result.success()
        } catch (e: Exception) {
            notifyFailed(e.message ?: "Analysis failed")
            androidx.work.ListenableWorker.Result.failure(
                Data.Builder().putString("error", e.message).build()
            )
        }
    }

    private fun progressNotification(pct: Int) =
        NotificationCompat.Builder(applicationContext, CH_PROGRESS)
            .setContentTitle("Analyzing your ride")
            .setContentText("$pct%")
            .setSmallIcon(android.R.drawable.stat_sys_download)
            .setProgress(100, pct, false)
            .setOngoing(true)
            .setSilent(true)
            .build()

    private fun foregroundInfo(pct: Int): ForegroundInfo =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q)
            ForegroundInfo(NOTIF_PROGRESS, progressNotification(pct),
                android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        else ForegroundInfo(NOTIF_PROGRESS, progressNotification(pct))

    private fun canNotify() =
        Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
            ContextCompat.checkSelfPermission(applicationContext, Manifest.permission.POST_NOTIFICATIONS) ==
            PackageManager.PERMISSION_GRANTED

    private fun notifyDone(r: FitResult) {
        val nm = NotificationManagerCompat.from(applicationContext)
        nm.cancel(NOTIF_PROGRESS)
        if (!canNotify()) return
        val knee = r.angles[Fit.KNEE]
        val text = buildString {
            append(Fit.verdict(r.overall))
            if (knee != null && !knee.isNaN()) append(" · knee ${knee.roundToInt()}°")
            append(" · ${r.strokes} strokes")
        }
        val open = PendingIntent.getActivity(
            applicationContext, 0,
            Intent(applicationContext, MainActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        nm.notify(NOTIF_DONE,
            NotificationCompat.Builder(applicationContext, CH_DONE)
                .setContentTitle("Your bike fit is ready")
                .setContentText(text)
                .setSmallIcon(android.R.drawable.stat_notify_chat)
                .setContentIntent(open)
                .setAutoCancel(true)
                .build())
    }

    private fun notifyFailed(msg: String) {
        val nm = NotificationManagerCompat.from(applicationContext)
        nm.cancel(NOTIF_PROGRESS)
        if (!canNotify()) return
        nm.notify(NOTIF_DONE,
            NotificationCompat.Builder(applicationContext, CH_DONE)
                .setContentTitle("Analysis failed")
                .setContentText(msg)
                .setSmallIcon(android.R.drawable.stat_notify_error)
                .setAutoCancel(true)
                .build())
    }
}

package xyz.doniwirawan.bikefit

import android.content.Context
import android.net.Uri
import java.io.File

/**
 * Copy the picked video into the app's own storage before analysing it.
 *
 * A URI handed over by the system file picker carries only a temporary grant. The analysis runs
 * in a background worker, possibly after the user has left the app — by then the grant can be
 * gone, and the worker dies with a SecurityException. Staging a private copy makes the worker
 * independent of that grant.
 */
object Staging {
    fun stage(ctx: Context, uri: Uri): Uri {
        val out = File(ctx.cacheDir, "analysis-input.mp4")
        ctx.contentResolver.openInputStream(uri).use { input ->
            requireNotNull(input) { "Couldn't open that video." }
            out.outputStream().use { input.copyTo(it) }
        }
        return Uri.fromFile(out)
    }
}

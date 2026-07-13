package xyz.doniwirawan.bikefit

import android.content.Context
import android.graphics.Bitmap
import android.media.MediaMetadataRetriever
import android.net.Uri
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.poselandmarker.PoseLandmarker
import kotlin.math.max
import kotlin.math.roundToInt

/** MediaPipe BlazePose landmark indices, near-side pairs. */
private val SIDE = mapOf(
    "left" to mapOf("shoulder" to 11, "elbow" to 13, "wrist" to 15, "hip" to 23, "knee" to 25, "ankle" to 27),
    "right" to mapOf("shoulder" to 12, "elbow" to 14, "wrist" to 16, "hip" to 24, "knee" to 26, "ankle" to 28),
)

data class FitResult(
    val angles: Map<String, Float>,
    val grades: Map<String, Fit.Grade>,
    val overall: Fit.Grade,
    val strokes: Int,
    val hipTop: Float?,
    val bike: String,
    val advice: List<String>,
    val offAxis: Boolean,
    val stillFrame: Bitmap?,
)

class Analyzer(private val ctx: Context) {

    /** @param onProgress 0f..1f */
    fun analyze(uri: Uri, bike: String, onProgress: (Float) -> Unit): FitResult {
        val landmarker = PoseLandmarker.createFromOptions(
            ctx,
            PoseLandmarker.PoseLandmarkerOptions.builder()
                .setBaseOptions(
                    BaseOptions.builder()
                        .setModelAssetPath("pose_landmarker_full.task")
                        .build()
                )
                .setRunningMode(RunningMode.VIDEO)
                .setNumPoses(1)
                .build()
        )

        val mmr = MediaMetadataRetriever()
        mmr.setDataSource(ctx, uri)
        val durMs = mmr.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)?.toLongOrNull() ?: 0L
        if (durMs <= 0L) { landmarker.close(); mmr.release(); throw IllegalStateException("Couldn't read that video.") }

        // Sample ~15 fps: enough to catch the bottom of every stroke without decoding everything.
        val stepMs = 66L
        val count = (durMs / stepMs).toInt().coerceAtMost(600)

        val ankleY = mutableListOf<Float>()
        val perFrame = mutableListOf<Map<String, Float>>()
        val stills = mutableListOf<Pair<Long, Bitmap>>()
        val viewRatios = mutableListOf<Float>()
        var leftConf = 0f; var rightConf = 0f

        // First pass over the frames.
        val raw = mutableListOf<Triple<Long, List<com.google.mediapipe.tasks.components.containers.NormalizedLandmark>, Bitmap>>()
        for (i in 0 until count) {
            val tUs = i * stepMs * 1000
            // OPTION_CLOSEST, not OPTION_CLOSEST_SYNC: sync frames are keyframes, which can be
            // seconds apart. Sampling those returns the same few positions over and over, the
            // ankle signal goes flat, and most pedal strokes are never detected.
            val bmp = mmr.getFrameAtTime(tUs, MediaMetadataRetriever.OPTION_CLOSEST) ?: continue
            val mp = BitmapImageBuilder(bmp).build()
            val res = landmarker.detectForVideo(mp, i * stepMs)
            val lms = res.landmarks().firstOrNull()
            if (lms != null) {
                raw.add(Triple(i * stepMs, lms, bmp))
                leftConf += (lms[25].visibility().orElse(0f) + lms[27].visibility().orElse(0f))
                rightConf += (lms[26].visibility().orElse(0f) + lms[28].visibility().orElse(0f))
            }
            onProgress(i / count.toFloat() * 0.9f)
        }
        landmarker.close()

        if (raw.size < 5) { mmr.release(); throw IllegalStateException("Couldn't track your body clearly.") }

        val near = if (leftConf >= rightConf) "left" else "right"
        val ids = SIDE[near]!!
        val w = raw.first().third.width.toFloat()
        val h = raw.first().third.height.toFloat()

        for ((_, lms, _) in raw) {
            fun pt(k: String): Fit.P {
                val lm = lms[ids[k]!!]
                return Fit.P(lm.x() * w, lm.y() * h, lm.visibility().orElse(0f))
            }
            fun vis(vararg ks: String) = ks.all { pt(it).v >= Fit.MIN_VIS }

            val hip = pt("hip"); val knee = pt("knee"); val ankle = pt("ankle")
            val sh = pt("shoulder"); val el = pt("elbow"); val wr = pt("wrist")

            val a = mutableMapOf<String, Float>()
            a[Fit.KNEE] = if (vis("hip", "knee", "ankle")) 180f - Fit.angleAt(hip, knee, ankle) else Float.NaN
            a[Fit.TORSO] = if (vis("hip", "shoulder")) Fit.torsoFromHorizontal(hip, sh) else Float.NaN
            a[Fit.ELBOW] = if (vis("shoulder", "elbow", "wrist")) 180f - Fit.angleAt(sh, el, wr) else Float.NaN
            a[Fit.SHOULDER] = if (vis("hip", "shoulder", "elbow")) Fit.angleAt(hip, sh, el) else Float.NaN
            a["hip_angle"] = if (vis("shoulder", "hip", "knee")) Fit.angleAt(sh, hip, knee) else Float.NaN
            perFrame.add(a)
            ankleY.add(if (vis("ankle")) ankle.y else Float.NaN)

            // Off-axis check: shoulders/hips should look narrow from the side.
            val sL = lms[11]; val sR = lms[12]; val hL = lms[23]; val hR = lms[24]
            val shoulderSpread = kotlin.math.abs(sL.x() - sR.x()) * w
            val hipSpread = kotlin.math.abs(hL.x() - hR.x()) * w
            val torsoLen = kotlin.math.hypot(
                ((sL.x() + sR.x()) / 2 - (hL.x() + hR.x()) / 2) * w,
                ((sL.y() + sR.y()) / 2 - (hL.y() + hR.y()) / 2) * h
            )
            if (torsoLen > 1f) viewRatios.add(max(shoulderSpread, hipSpread) / torsoLen)
        }

        // Bottom of each stroke = peaks of ankle Y (image y grows downward).
        val valid = ankleY.filter { !it.isNaN() }.sorted()
        if (valid.size < 5) { mmr.release(); throw IllegalStateException("Couldn't track your legs clearly.") }
        val amp = valid[(valid.size * 0.95).toInt().coerceAtMost(valid.size - 1)] -
                  valid[(valid.size * 0.05).toInt()]
        val fps = 1000f / stepMs
        val minDist = max(3, (fps * 0.35f).roundToInt())
        val prom = max(2f, 0.25f * amp)

        val bdc = Fit.findPeaks(ankleY, minDist, prom)
        val tdc = Fit.findPeaks(ankleY.map { if (it.isNaN()) Float.NaN else -it }, minDist, prom)
        if (bdc.isEmpty()) { mmr.release(); throw IllegalStateException("No clear pedal strokes found.") }

        fun med(m: String) = Fit.median(bdc.mapNotNull { perFrame[it][m] })
        val angles = mapOf(
            Fit.KNEE to med(Fit.KNEE),
            Fit.TORSO to med(Fit.TORSO),
            Fit.ELBOW to med(Fit.ELBOW),
            Fit.SHOULDER to med(Fit.SHOULDER),
        )
        val hipTop = if (tdc.isNotEmpty()) Fit.median(tdc.mapNotNull { perFrame[it]["hip_angle"] }) else null

        val zones = Fit.zonesFor(bike)
        val grades = angles.mapValues { (m, v) -> Fit.grade(v, zones[m]!!) }
        val overall = Fit.worst(*grades.values.toTypedArray())

        // The deepest stroke, for the still shown with the result.
        val deepest = bdc.maxByOrNull { ankleY[it].takeIf { y -> !y.isNaN() } ?: Float.MIN_VALUE }
        val still = deepest?.let { raw.getOrNull(it)?.third }

        val offAxis = viewRatios.size >= 5 && Fit.median(viewRatios) > 0.55f
        onProgress(1f)
        mmr.release()

        return FitResult(
            angles = angles,
            grades = grades,
            overall = overall,
            strokes = bdc.size,
            hipTop = hipTop?.takeIf { !it.isNaN() },
            bike = bike,
            advice = Fit.advice(angles, grades, bike),
            offAxis = offAxis,
            stillFrame = still,
        )
    }
}

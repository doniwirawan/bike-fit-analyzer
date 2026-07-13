package xyz.doniwirawan.bikefit

import kotlin.math.abs
import kotlin.math.acos
import kotlin.math.atan2
import kotlin.math.hypot
import kotlin.math.min
import kotlin.math.roundToInt

/**
 * The grading rules, ported from the web app (web/app.html).
 *
 * These numbers are the contract between the two: if they drift apart, the phone and the
 * website give the same rider different verdicts on the same clip. Any change here must be
 * mirrored there, and in files/bikefit-research-ranges.md.
 */
object Fit {

    // green_lo, green_hi, red_lo, red_hi
    data class Zone(val gLo: Int, val gHi: Int, val rLo: Int, val rHi: Int) {
        val target get() = "$gLo–$gHi°"
    }

    const val KNEE = "knee_flexion_bdc"
    const val TORSO = "torso_from_horiz"
    const val ELBOW = "elbow_flexion"
    const val SHOULDER = "shoulder_angle"

    val fixedZones = mapOf(
        KNEE to Zone(30, 40, 28, 42),
        ELBOW to Zone(15, 30, 8, 45),
        SHOULDER to Zone(80, 95, 70, 105),
    )

    /** Only the torso target moves with the bike — saddle height does not. */
    val bikeTorso = linkedMapOf(
        "road_endurance" to Zone(40, 50, 34, 56),
        "road_race" to Zone(32, 42, 28, 48),
        "tt_tri" to Zone(12, 28, 8, 34),
        "gravel" to Zone(42, 52, 36, 58),
        "mtb" to Zone(46, 58, 40, 64),
        "city" to Zone(55, 70, 48, 78),
    )

    val bikeLabels = linkedMapOf(
        "road_endurance" to "Road — endurance",
        "road_race" to "Road — race / aggressive",
        "tt_tri" to "TT / Triathlon",
        "gravel" to "Gravel",
        "mtb" to "Mountain (MTB)",
        "city" to "City / Hybrid / Commuter / E-bike",
    )

    const val MIN_VIS = 0.5f

    enum class Grade { GREEN, AMBER, RED, GRAY }

    fun zonesFor(bike: String): Map<String, Zone> =
        fixedZones + mapOf(TORSO to (bikeTorso[bike] ?: bikeTorso.values.first()))

    fun grade(v: Float?, z: Zone): Grade {
        if (v == null || v.isNaN()) return Grade.GRAY
        if (v >= z.gLo && v <= z.gHi) return Grade.GREEN
        if (v < z.rLo || v > z.rHi) return Grade.RED
        return Grade.AMBER
    }

    fun worst(vararg g: Grade): Grade {
        val order = mapOf(Grade.GRAY to 0, Grade.GREEN to 1, Grade.AMBER to 2, Grade.RED to 3)
        return g.maxByOrNull { order[it]!! } ?: Grade.GRAY
    }

    fun verdict(g: Grade) = when (g) {
        Grade.GREEN -> "Dialed"
        Grade.AMBER -> "Minor tweaks"
        Grade.RED -> "Fix needed"
        Grade.GRAY -> "Incomplete"
    }

    // ---- geometry ----

    data class P(val x: Float, val y: Float, val v: Float = 1f)

    /** Interior angle at b, in degrees. */
    fun angleAt(a: P, b: P, c: P): Float {
        val v1x = a.x - b.x; val v1y = a.y - b.y
        val v2x = c.x - b.x; val v2y = c.y - b.y
        val n1 = hypot(v1x, v1y); val n2 = hypot(v2x, v2y)
        if (n1 == 0f || n2 == 0f) return Float.NaN
        val cos = ((v1x * v2x + v1y * v2y) / (n1 * n2)).coerceIn(-1f, 1f)
        return Math.toDegrees(acos(cos).toDouble()).toFloat()
    }

    /** Torso angle from horizontal (0 = flat on the bars, 90 = bolt upright). */
    fun torsoFromHorizontal(hip: P, shoulder: P): Float {
        val dx = abs(shoulder.x - hip.x)
        val dy = abs(shoulder.y - hip.y)   // y grows downward in image space
        return Math.toDegrees(atan2(dy, dx).toDouble()).toFloat()
    }

    fun median(xs: List<Float>): Float {
        val s = xs.filter { !it.isNaN() }.sorted()
        if (s.isEmpty()) return Float.NaN
        return s[s.size / 2]
    }

    /**
     * Peaks of a 1-D signal, the way the web app finds the bottom of each pedal stroke:
     * a local maximum that stands `prominence` above its neighbours and is at least
     * `minDist` samples from the last one.
     */
    fun findPeaks(y: List<Float>, minDist: Int, prominence: Float): List<Int> {
        val out = mutableListOf<Int>()
        var last = -minDist - 1
        for (i in 1 until y.size - 1) {
            val v = y[i]
            if (v.isNaN()) continue
            if (v >= y[i - 1] && v >= y[i + 1]) {
                val lo = maxOf(0, i - minDist)
                val hi = minOf(y.size - 1, i + minDist)
                val around = (lo..hi).mapNotNull { y[it].takeIf { f -> !f.isNaN() } }
                if (around.isEmpty()) continue
                if (v - (around.minOrNull() ?: v) < prominence) continue
                if (v < (around.maxOrNull() ?: v)) continue
                if (i - last < minDist) continue
                out.add(i); last = i
            }
        }
        return out
    }

    // ---- advice (same wording as the web app) ----

    fun advice(angles: Map<String, Float>, grades: Map<String, Grade>, bike: String): List<String> {
        val out = mutableListOf<String>()
        val z = zonesFor(bike)

        val knee = angles[KNEE]
        if (knee != null && !knee.isNaN() && grades[KNEE] != Grade.GREEN) {
            val mm = min(20, (abs(knee - 35f) * 1.5f).roundToInt())
            out += if (knee > 40)
                "Saddle looks low — knee still bent ${knee.roundToInt()}° at the bottom (aim 30–40°). " +
                    "Raise it about ${mm}mm, in 2–3mm steps, and re-film. This is the most reliable reading here."
            else
                "Saddle looks high — leg nearly straight (${knee.roundToInt()}°) at the bottom (aim 30–40°). " +
                    "Lower it about ${mm}mm, in 2–3mm steps, and re-film. This is the most reliable reading here."
        }

        val torso = angles[TORSO]
        if (torso != null && !torso.isNaN() && grades[TORSO] != Grade.GREEN) {
            val zz = z[TORSO]!!
            out += if (torso > zz.gHi)
                "Torso more upright (${torso.roundToInt()}°) than typical for this bike (aim ${zz.target}). " +
                    "Comfortable — but if you want more power/aero and your flexibility allows, a slightly lower front end helps."
            else
                "Torso lower/more aggressive (${torso.roundToInt()}°) than typical for this bike (aim ${zz.target}). " +
                    "If your lower back or neck complains, raise the bars or shorten the reach a touch."
        }

        val elbow = angles[ELBOW]
        if (elbow != null && !elbow.isNaN() && grades[ELBOW] != Grade.GREEN) {
            out += if (elbow < 15)
                "Elbow ${elbow.roundToInt()}° → arms look locked. Soften your elbows first — a slight bend absorbs " +
                    "road buzz and often fixes this without touching the bike."
            else
                "Elbow ${elbow.roundToInt()}° → arms quite bent. Usually fine; only if it feels cramped might the reach be a touch short."
        }

        val sh = angles[SHOULDER]
        if (sh != null && !sh.isNaN() && grades[SHOULDER] != Grade.GREEN) {
            out += if (sh < 80)
                "Shoulder ${sh.roundToInt()}° → cockpit looks a bit cramped. Reach is the least reliable 2D angle — " +
                    "re-check your hand position and that the camera is square before changing anything."
            else
                "Shoulder ${sh.roundToInt()}° → reach looks a bit long. Reach is the least reliable 2D angle — " +
                    "don't shorten the stem off one clip; re-film square-on, then change one thing at a time."
        }

        if (out.isEmpty()) out += "Everything's in range — nice fit. Re-film if you change anything."
        return out
    }
}

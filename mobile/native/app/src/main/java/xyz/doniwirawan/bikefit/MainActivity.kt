package xyz.doniwirawan.bikefit

import android.Manifest
import android.net.Uri
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.work.*
import org.json.JSONObject
import kotlin.math.roundToInt

private val LABEL = mapOf(
    Fit.KNEE to "Knee at bottom",
    Fit.TORSO to "Torso from horizontal",
    Fit.ELBOW to "Elbow bend",
    Fit.SHOULDER to "Shoulder (reach)",
)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        AnalysisWorker.ensureChannels(this)
        val handed: Uri? = when (intent?.action) {
            android.content.Intent.ACTION_SEND -> intent.getParcelableExtra(android.content.Intent.EXTRA_STREAM)
            android.content.Intent.ACTION_VIEW -> intent.data
            else -> null
        }
        setContent {
            BikeFitTheme { App(handed) }
        }
    }
}

@Composable
private fun App(handed: Uri? = null) {
    val ctx = androidx.compose.ui.platform.LocalContext.current
    var bike by remember { mutableStateOf("road_endurance") }
    var video by remember { mutableStateOf<Uri?>(handed) }
    var recording by remember { mutableStateOf(false) }
    var about by remember { mutableStateOf(false) }
    var result by remember { mutableStateOf(ResultStore.latest(ctx)) }
    var error by remember { mutableStateOf<String?>(null) }

    val work = WorkManager.getInstance(ctx)
    val infos by work.getWorkInfosForUniqueWorkLiveData("analysis")
        .observeAsStateCompat()

    // A worker killed with the process (crash, force-stop) can leave its WorkInfo stuck in
    // RUNNING, which left a progress bar on screen forever. Clear a stale run on start.
    val info = infos?.firstOrNull()
    LaunchedEffect(Unit) {
        if (info?.state == WorkInfo.State.RUNNING && info.progress.getInt(AnalysisWorker.PROGRESS, 0) == 0)
            work.cancelUniqueWork("analysis")
    }
    val running = info?.state == WorkInfo.State.RUNNING
    val progress = info?.progress?.getInt(AnalysisWorker.PROGRESS, 0) ?: 0

    // refresh the result when the worker finishes
    LaunchedEffect(info?.state) {
        if (info?.state?.isFinished == true) result = ResultStore.latest(ctx)
    }

    val notifPerm = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {}
    LaunchedEffect(Unit) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU)
            notifPerm.launch(Manifest.permission.POST_NOTIFICATIONS)
    }

    // No takePersistableUriPermission here: ACTION_GET_CONTENT never grants a persistable one, so
    // asking for it throws SecurityException in this callback. Staging.stage() copies the clip into
    // app storage anyway, which is what actually makes the background worker independent of the grant.
    val pick = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) video = uri
    }

    // The recorder owns the whole screen while it is up: a viewfinder you have to scroll to keep
    // in view is useless when you are lining up the shot from across the room.
    if (recording) {
        Box(Modifier.fillMaxSize().background(androidx.compose.ui.graphics.Color.Black)
            .windowInsetsPadding(WindowInsets.safeDrawing)) {
            RecorderScreen(
                onRecorded = { uri -> video = uri; recording = false },
                onCancel = { recording = false }
            )
        }
        return
    }

    if (about) {
        androidx.activity.compose.BackHandler { about = false }
        AboutScreen(onBack = { about = false })
        return
    }

    Column(
        Modifier.fillMaxSize().background(P.bg).windowInsetsPadding(WindowInsets.safeDrawing)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 12.dp)
    ) {
        Header("Bike Fit Analyzer", "About") { about = true }
        Spacer(Modifier.height(26.dp))

        Text("Check your fit", fontFamily = MonaWide, fontWeight = FontWeight.ExtraBold,
            fontSize = 30.sp, lineHeight = 33.sp, letterSpacing = (-0.8).sp)
        Spacer(Modifier.height(8.dp))
        Text("Film yourself side-on, pedalling for 20 to 30 seconds. It runs on this phone and nothing is uploaded.",
            color = P.mut, style = MaterialTheme.typography.bodyMedium)
        Spacer(Modifier.height(22.dp))

        Card {
            Text("Bike type", style = MaterialTheme.typography.labelMedium)
            Spacer(Modifier.height(8.dp))
            var open by remember { mutableStateOf(false) }
            Box {
                Row(
                    Modifier.fillMaxWidth().heightIn(min = 52.dp)
                        .background(P.bg, RoundedCornerShape(RADIUS_SM + 2.dp))
                        .border(1.dp, P.line, RoundedCornerShape(RADIUS_SM + 2.dp))
                        .clickable(enabled = !running) { open = true }
                        .padding(horizontal = 16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(Fit.bikeLabels[bike] ?: bike, style = MaterialTheme.typography.bodyLarge,
                        modifier = Modifier.weight(1f))
                    Chevron()
                }
                DropdownMenu(expanded = open, onDismissRequest = { open = false },
                    modifier = Modifier.background(P.card)) {
                    Fit.bikeLabels.forEach { (k, label) ->
                        DropdownMenuItem(
                            text = { Text(label, fontWeight = if (k == bike) FontWeight.Bold else FontWeight.Normal) },
                            onClick = { bike = k; open = false })
                    }
                }
            }
            Spacer(Modifier.height(8.dp))
            Text("Only the torso target changes with the bike. Saddle height (knee) is the same on any bike.",
                color = P.mut, style = MaterialTheme.typography.bodySmall)

            Spacer(Modifier.height(18.dp))
            Divider()
            Spacer(Modifier.height(18.dp))

            if (video == null) {
                Text("Your video", style = MaterialTheme.typography.labelMedium)
                Spacer(Modifier.height(10.dp))
                PrimaryButton("Choose a video", { pick.launch("video/*") }, Modifier.fillMaxWidth(), enabled = !running)
                Spacer(Modifier.height(10.dp))
                GhostButton("Record with camera", { recording = true }, Modifier.fillMaxWidth(), enabled = !running)
            } else {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("Video ready", style = MaterialTheme.typography.labelLarge)
                        Text(if (running) "Analyzing now" else "Pick a bike type above, then analyze.",
                            color = P.mut, style = MaterialTheme.typography.bodySmall)
                    }
                    TextButton(onClick = { pick.launch("video/*") }, enabled = !running,
                        modifier = Modifier.heightIn(min = 44.dp)) {
                        Text("Change", color = if (running) P.mut else P.accent, style = MaterialTheme.typography.labelMedium)
                    }
                }
                Spacer(Modifier.height(12.dp))
                PrimaryButton(if (running) "Analyzing…" else "Analyze", {
                    // Never fail silently: if the video can't be read, say so instead of
                    // leaving the user tapping a button that does nothing.
                    val staged = try { Staging.stage(ctx, video!!) } catch (e: Exception) {
                        error = "Couldn't read that video (${e.message ?: "unknown error"})."
                        null
                    }
                    if (staged != null) {
                        error = null
                        work.enqueueUniqueWork(
                            "analysis", ExistingWorkPolicy.REPLACE,
                            OneTimeWorkRequestBuilder<AnalysisWorker>()
                                .setInputData(
                                    Data.Builder()
                                        .putString(AnalysisWorker.KEY_URI, staged.toString())
                                        .putString(AnalysisWorker.KEY_BIKE, bike)
                                        .build()
                                ).build()
                        )
                    }
                }, Modifier.fillMaxWidth(), enabled = !running)
                Spacer(Modifier.height(10.dp))
                GhostButton("Record a new clip", { recording = true }, Modifier.fillMaxWidth(), enabled = !running)
            }

            if (running) {
                Spacer(Modifier.height(18.dp))
                Row(verticalAlignment = Alignment.Bottom) {
                    Text("$progress%", fontFamily = MonaWide, fontWeight = FontWeight.ExtraBold, fontSize = 22.sp)
                    Spacer(Modifier.width(8.dp))
                    Text("analyzed", color = P.mut, style = MaterialTheme.typography.bodySmall,
                        modifier = Modifier.padding(bottom = 3.dp))
                }
                Spacer(Modifier.height(8.dp))
                LinearProgressIndicator(
                    progress = { progress / 100f },
                    modifier = Modifier.fillMaxWidth().height(6.dp),
                    color = P.accent, trackColor = P.grid,
                    strokeCap = androidx.compose.ui.graphics.StrokeCap.Round, gapSize = 0.dp,
                    drawStopIndicator = {}
                )
                Spacer(Modifier.height(8.dp))
                Text("You can leave the app. It keeps going and notifies you when it's done.",
                    color = P.mut, style = MaterialTheme.typography.bodySmall)
            }

            error?.let {
                Spacer(Modifier.height(14.dp))
                Text(it, color = P.red, style = MaterialTheme.typography.bodySmall)
            }
        }

        result?.let { r ->
            Spacer(Modifier.height(34.dp))
            SectionTitle("Your fit", "Latest result. Saved on this phone only.")
            ResultView(r)
        }

        val history = remember(result) { ResultStore.raw(ctx) }
        if (history.length() > 1) {
            Spacer(Modifier.height(34.dp))
            HistoryView(history) { result = ResultStore.latest(ctx) }
        }
        Spacer(Modifier.height(24.dp))
    }
}

@Composable
private fun Chevron() {
    val c = P.mut
    androidx.compose.foundation.Canvas(Modifier.size(14.dp)) {
        val w = size.width; val h = size.height
        val path = androidx.compose.ui.graphics.Path().apply {
            moveTo(w * .15f, h * .35f); lineTo(w * .5f, h * .7f); lineTo(w * .85f, h * .35f)
        }
        drawPath(path, c, style = androidx.compose.ui.graphics.drawscope.Stroke(
            width = 2.dp.toPx(), cap = androidx.compose.ui.graphics.StrokeCap.Round,
            join = androidx.compose.ui.graphics.StrokeJoin.Round))
    }
}

/** Saved results, and a before/after when two are ticked. */
@Composable
private fun HistoryView(history: org.json.JSONArray, onChanged: () -> Unit) {
    val ctx = androidx.compose.ui.platform.LocalContext.current
    var picked by remember { mutableStateOf(listOf<Long>()) }
    var shown by remember { mutableStateOf<Long?>(null) }

    SectionTitle("Saved results", "Tick two to compare them. Saved on this phone only.")

    if (picked.size == 2) {
        val pair = (0 until history.length()).map { history.getJSONObject(it) }
            .filter { it.optLong("at") in picked }
            .sortedBy { it.optLong("at") }
        if (pair.size == 2) { CompareView(pair[0], pair[1]); Spacer(Modifier.height(12.dp)) }
    }

    Card(pad = 0.dp) {
        for (i in 0 until history.length()) {
            val e = history.getJSONObject(i)
            val at = e.optLong("at")
            val when_ = java.text.SimpleDateFormat("d MMM, HH:mm", java.util.Locale.getDefault())
                .format(java.util.Date(at))
            val knee = e.optJSONObject("angles")?.optDouble(Fit.KNEE)
            if (i > 0) Divider()
            Row(
                Modifier.fillMaxWidth().padding(start = 4.dp, end = 8.dp, top = 6.dp, bottom = 6.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Checkbox(
                    checked = picked.contains(at),
                    onCheckedChange = { on -> picked = if (on) (picked + at).takeLast(2) else picked - at },
                    colors = CheckboxDefaults.colors(checkedColor = P.accent, uncheckedColor = P.mut,
                        checkmarkColor = P.accentInk)
                )
                Column(Modifier.weight(1f)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        GradeDot(e.optString("overall", "GRAY"), 8.dp)
                        Spacer(Modifier.width(7.dp))
                        Text(
                            Fit.verdict(Fit.Grade.valueOf(e.optString("overall", "GRAY"))) +
                                (knee?.takeIf { !it.isNaN() }?.let { " · knee ${it.roundToInt()}°" } ?: ""),
                            style = MaterialTheme.typography.labelLarge
                        )
                    }
                    Text(when_, color = P.mut, style = MaterialTheme.typography.bodySmall)
                }
                TextButton(onClick = { shown = if (shown == at) null else at },
                    modifier = Modifier.heightIn(min = 44.dp)) {
                    Text(if (shown == at) "Close" else "Open", color = P.accent, style = MaterialTheme.typography.labelMedium)
                }
            }
        }
    }

    shown?.let { at ->
        (0 until history.length()).map { history.getJSONObject(it) }.firstOrNull { it.optLong("at") == at }?.let {
            Spacer(Modifier.height(16.dp))
            ResultView(it)
        }
    }

    Spacer(Modifier.height(8.dp))
    TextButton(onClick = { ResultStore.clear(ctx); picked = emptyList(); shown = null; onChanged() },
        modifier = Modifier.heightIn(min = 44.dp)) {
        Text("Clear saved results", color = P.mut, style = MaterialTheme.typography.labelMedium)
    }
}

/** Before/after. "Better" means the reading moved into a better band, not that the number went up. */
@Composable
private fun CompareView(before: JSONObject, after: JSONObject) {
    fun angle(o: JSONObject, m: String): Float? =
        o.optJSONObject("angles")?.let { if (it.has(m)) it.getDouble(m).toFloat() else null }
    fun gradeOf(o: JSONObject, m: String, v: Float?): Fit.Grade {
        val z = Fit.zonesFor(o.optString("bike", "road_endurance"))[m]!!
        return Fit.grade(v, z)
    }
    val rank = mapOf(Fit.Grade.GRAY to 0, Fit.Grade.RED to 1, Fit.Grade.AMBER to 2, Fit.Grade.GREEN to 3)
    fun fmt(v: Float?) = v?.takeIf { !it.isNaN() }?.let { "${it.roundToInt()}°" } ?: "–"

    Card {
        Row {
            Text("Before and after", style = MaterialTheme.typography.labelLarge, modifier = Modifier.weight(1f))
            Text("Change", color = P.mut, style = MaterialTheme.typography.bodySmall)
        }
        Spacer(Modifier.height(6.dp))
        listOf(Fit.KNEE, Fit.TORSO, Fit.ELBOW, Fit.SHOULDER).forEachIndexed { i, m ->
            val a = angle(before, m); val b = angle(after, m)
            val ga = gradeOf(before, m, a); val gb = gradeOf(after, m, b)
            val moved = (rank[gb] ?: 0) - (rank[ga] ?: 0)
            val tone = if (moved > 0) P.green else if (moved < 0) P.red else P.mut
            val delta = if (a != null && b != null && !a.isNaN() && !b.isNaN())
                "${if (b - a > 0) "+" else ""}${(b - a).roundToInt()}°" else ""
            if (i > 0) Divider()
            Row(Modifier.fillMaxWidth().padding(vertical = 10.dp), verticalAlignment = Alignment.CenterVertically) {
                Text(LABEL[m]!!, style = MaterialTheme.typography.bodySmall, modifier = Modifier.weight(1f))
                Text(fmt(a), color = P.gradeColor(ga.name), fontWeight = FontWeight.Bold, fontSize = 14.sp)
                Text("  →  ", color = P.mut, fontSize = 13.sp)
                Text(fmt(b), color = P.gradeColor(gb.name), fontWeight = FontWeight.Bold, fontSize = 14.sp)
                Text(delta, color = tone, fontWeight = FontWeight.Bold, fontSize = 14.sp,
                    textAlign = androidx.compose.ui.text.style.TextAlign.End, modifier = Modifier.width(52.dp))
            }
        }
        Spacer(Modifier.height(4.dp))
        Text("Green means it moved into a better band, red means it moved out of one.",
            color = P.mut, style = MaterialTheme.typography.bodySmall)
    }
}

@Composable
private fun ResultView(r: JSONObject) {
    val angles = r.getJSONObject("angles")
    val grades = r.getJSONObject("grades")
    val bike = r.optString("bike", "road_endurance")
    val zones = Fit.zonesFor(bike)
    val overall = r.optString("overall", "GRAY")

    Card {
        Row(verticalAlignment = Alignment.CenterVertically) {
            GradeDot(overall, 12.dp)
            Spacer(Modifier.width(10.dp))
            Text(Fit.verdict(Fit.Grade.valueOf(overall)), fontFamily = MonaWide, fontWeight = FontWeight.ExtraBold,
                fontSize = 22.sp, letterSpacing = (-0.4).sp)
        }
        Spacer(Modifier.height(2.dp))
        Text("${r.optInt("strokes")} pedal strokes · ${Fit.bikeLabels[bike] ?: bike}",
            color = P.mut, style = MaterialTheme.typography.bodySmall)
        Spacer(Modifier.height(6.dp))

        listOf(Fit.KNEE, Fit.TORSO, Fit.ELBOW, Fit.SHOULDER).forEach { m ->
            val v = if (angles.has(m)) angles.getDouble(m).toFloat() else Float.NaN
            val g = grades.optString(m, "GRAY")
            Spacer(Modifier.height(12.dp))
            Divider()
            Spacer(Modifier.height(14.dp))
            Row(verticalAlignment = Alignment.Bottom) {
                Column(Modifier.weight(1f)) {
                    Text(LABEL[m]!!, style = MaterialTheme.typography.labelLarge)
                    Text("target ${zones[m]!!.target}", color = P.mut, style = MaterialTheme.typography.bodySmall)
                }
                Text(if (v.isNaN()) "–" else "${v.roundToInt()}°", color = P.gradeColor(g),
                    fontFamily = MonaWide, fontWeight = FontWeight.ExtraBold, fontSize = 34.sp,
                    lineHeight = 36.sp, letterSpacing = (-1).sp)
            }
            Spacer(Modifier.height(8.dp))
            RangeBar(if (v.isNaN()) null else v, zones[m]!!)
        }
    }

    if (r.optBoolean("offAxis")) {
        Spacer(Modifier.height(12.dp))
        Card {
            Text("Camera angle", style = MaterialTheme.typography.labelLarge)
            Spacer(Modifier.height(4.dp))
            Text("This clip doesn't look square-on, so the angles, reach most of all, may be stretched. " +
                "Re-film with the camera directly beside you.", color = P.mut, style = MaterialTheme.typography.bodySmall)
        }
    }

    Spacer(Modifier.height(12.dp))
    Card {
        Text("What to do", style = MaterialTheme.typography.labelLarge)
        val advice = r.getJSONArray("advice")
        for (i in 0 until advice.length()) {
            Spacer(Modifier.height(10.dp))
            Row {
                Text("${i + 1}", fontFamily = MonaWide, fontWeight = FontWeight.ExtraBold, color = P.mut,
                    fontSize = 15.sp, modifier = Modifier.width(22.dp))
                Text(advice.getString(i), style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
    Spacer(Modifier.height(10.dp))
    Text("A 2D side-view estimate, not a professional bike fit, and not medical advice. " +
        "Saddle height (knee) is the most reliable number here; reach is the softest.",
        color = P.mut, style = MaterialTheme.typography.bodySmall)
}

/** Small helper so we can observe WorkManager's LiveData from Compose without extra deps. */
@Composable
private fun androidx.lifecycle.LiveData<List<WorkInfo>>.observeAsStateCompat(): State<List<WorkInfo>?> {
    val state = remember { mutableStateOf<List<WorkInfo>?>(null) }
    val owner = androidx.compose.ui.platform.LocalLifecycleOwner.current
    DisposableEffect(this, owner) {
        val obs = androidx.lifecycle.Observer<List<WorkInfo>> { state.value = it }
        observe(owner, obs)
        onDispose { removeObserver(obs) }
    }
    return state
}

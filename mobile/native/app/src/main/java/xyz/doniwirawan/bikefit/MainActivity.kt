package xyz.doniwirawan.bikefit

import android.Manifest
import android.net.Uri
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.work.*
import org.json.JSONObject
import kotlin.math.roundToInt

private val GREEN = Color(0xFF16A34A)
private val AMBER = Color(0xFFD97706)
private val RED = Color(0xFFDC2626)
private val GRAY = Color(0xFF9AA3B2)
private val BG = Color(0xFF0B0F16)
private val CARD = Color(0xFF111825)
private val LINE = Color(0xFF1E2734)
private val FG = Color(0xFFDFE6F0)
private val MUT = Color(0xFF8B97A8)
private val ACCENT = Color(0xFF4D8BFF)

private fun colorOf(g: String) = when (g) {
    "GREEN" -> GREEN; "AMBER" -> AMBER; "RED" -> RED; else -> GRAY
}

private val LABEL = mapOf(
    Fit.KNEE to "Knee at bottom",
    Fit.TORSO to "Torso from horizontal",
    Fit.ELBOW to "Elbow bend",
    Fit.SHOULDER to "Shoulder (reach)",
)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        AnalysisWorker.ensureChannels(this)
        val handed: Uri? = when (intent?.action) {
            android.content.Intent.ACTION_SEND -> intent.getParcelableExtra(android.content.Intent.EXTRA_STREAM)
            android.content.Intent.ACTION_VIEW -> intent.data
            else -> null
        }
        setContent {
            MaterialTheme(colorScheme = darkColorScheme(background = BG, surface = CARD)) { App(handed) }
        }
    }
}

@Composable
private fun App(handed: Uri? = null) {
    val ctx = androidx.compose.ui.platform.LocalContext.current
    var bike by remember { mutableStateOf("road_endurance") }
    var video by remember { mutableStateOf<Uri?>(handed) }
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

    val pick = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) {
            video = uri
            ctx.contentResolver.takePersistableUriPermission(
                uri, android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION
            ).let { }
        }
    }

    Column(
        Modifier.fillMaxSize().background(BG).padding(18.dp).verticalScroll(rememberScrollState())
    ) {
        Text("BIKE FIT ANALYZER", color = FG, fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.Bold, letterSpacing = 2.sp, fontSize = 14.sp)
        Spacer(Modifier.height(4.dp))
        Text("Runs on your phone. Nothing is uploaded.", color = MUT, fontSize = 13.sp)
        Spacer(Modifier.height(20.dp))

        Text("BIKE TYPE", color = MUT, fontFamily = FontFamily.Monospace, fontSize = 11.sp, letterSpacing = 1.sp)
        Spacer(Modifier.height(6.dp))
        var open by remember { mutableStateOf(false) }
        Box {
            OutlinedButton(onClick = { open = true }, modifier = Modifier.fillMaxWidth()) {
                Text(Fit.bikeLabels[bike] ?: bike, color = FG)
            }
            DropdownMenu(expanded = open, onDismissRequest = { open = false }) {
                Fit.bikeLabels.forEach { (k, label) ->
                    DropdownMenuItem(text = { Text(label) }, onClick = { bike = k; open = false })
                }
            }
        }
        Spacer(Modifier.height(6.dp))
        Text("Only the torso target changes with the bike. Saddle height (knee) is the same on any bike.",
            color = MUT, fontSize = 11.sp)

        Spacer(Modifier.height(16.dp))
        Button(
            onClick = { pick.launch("video/*") },
            enabled = !running,
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(containerColor = ACCENT)
        ) { Text(if (video == null) "Choose a video" else "Choose a different video") }

        video?.let {
            Spacer(Modifier.height(10.dp))
            Button(
                onClick = {
                    // Never fail silently: if the video can't be read, say so instead of
                    // leaving the user tapping a button that does nothing.
                    val staged = try { Staging.stage(ctx, it) } catch (e: Exception) {
                        error = "Couldn't read that video (${e.message ?: "unknown error"})."
                        return@Button
                    }
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
                },
                enabled = !running,
                modifier = Modifier.fillMaxWidth()
            ) { Text(if (running) "Analyzing…" else "Analyze") }
        }

        error?.let {
            Spacer(Modifier.height(12.dp))
            Text(it, color = RED, fontSize = 13.sp)
        }

        if (running) {
            Spacer(Modifier.height(14.dp))
            LinearProgressIndicator(progress = { progress / 100f }, modifier = Modifier.fillMaxWidth())
            Spacer(Modifier.height(6.dp))
            Text("$progress% — you can leave the app, it keeps going and will notify you.",
                color = MUT, fontSize = 12.sp)
        }

        result?.let { r ->
            Spacer(Modifier.height(24.dp))
            ResultView(r)
        }

        val history = remember(result) { ResultStore.raw(ctx) }
        if (history.length() > 1) {
            Spacer(Modifier.height(28.dp))
            HistoryView(history) { result = ResultStore.latest(ctx) }
        }
    }
}

/** Saved results, and a before/after when two are ticked. */
@Composable
private fun HistoryView(history: org.json.JSONArray, onChanged: () -> Unit) {
    val ctx = androidx.compose.ui.platform.LocalContext.current
    var picked by remember { mutableStateOf(listOf<Long>()) }
    var shown by remember { mutableStateOf<JSONObject?>(null) }

    Text("SAVED RESULTS", color = MUT, fontFamily = FontFamily.Monospace,
        fontSize = 11.sp, letterSpacing = 1.sp)
    Spacer(Modifier.height(2.dp))
    Text("Tick two to compare them. Saved on this phone only.", color = MUT, fontSize = 11.sp)
    Spacer(Modifier.height(8.dp))

    if (picked.size == 2) {
        val pair = (0 until history.length()).map { history.getJSONObject(it) }
            .filter { it.optLong("at") in picked }
            .sortedBy { it.optLong("at") }
        if (pair.size == 2) CompareView(pair[0], pair[1])
    }

    for (i in 0 until history.length()) {
        val e = history.getJSONObject(i)
        val at = e.optLong("at")
        val when_ = java.text.SimpleDateFormat("dd MMM, HH:mm", java.util.Locale.getDefault())
            .format(java.util.Date(at))
        val knee = e.optJSONObject("angles")?.optDouble(Fit.KNEE)
        Row(
            Modifier.fillMaxWidth().padding(vertical = 3.dp)
                .background(CARD, RoundedCornerShape(10.dp)).padding(10.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Checkbox(
                checked = picked.contains(at),
                onCheckedChange = { on ->
                    picked = if (on) (picked + at).takeLast(2) else picked - at
                }
            )
            Column(Modifier.weight(1f)) {
                Text(when_, color = MUT, fontFamily = FontFamily.Monospace, fontSize = 10.sp)
                Text(
                    Fit.verdict(Fit.Grade.valueOf(e.optString("overall", "GRAY"))) +
                        (knee?.takeIf { !it.isNaN() }?.let { " · knee ${it.roundToInt()}°" } ?: ""),
                    color = colorOf(e.optString("overall")), fontSize = 13.sp, fontWeight = FontWeight.Bold
                )
            }
            TextButton(onClick = { shown = e }) { Text("Open", fontSize = 12.sp) }
        }
    }

    Spacer(Modifier.height(6.dp))
    TextButton(onClick = { ResultStore.clear(ctx); picked = emptyList(); onChanged() }) {
        Text("Clear all", color = MUT, fontSize = 12.sp)
    }

    shown?.let { e ->
        Spacer(Modifier.height(16.dp))
        ResultView(e)
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

    Column(
        Modifier.fillMaxWidth().padding(bottom = 10.dp)
            .background(CARD, RoundedCornerShape(12.dp)).padding(12.dp)
    ) {
        Text("BEFORE  →  AFTER", color = MUT, fontFamily = FontFamily.Monospace,
            fontSize = 10.sp, letterSpacing = 1.sp)
        Spacer(Modifier.height(6.dp))
        listOf(Fit.KNEE, Fit.TORSO, Fit.ELBOW, Fit.SHOULDER).forEach { m ->
            val a = angle(before, m); val b = angle(after, m)
            val ga = gradeOf(before, m, a); val gb = gradeOf(after, m, b)
            val moved = (rank[gb] ?: 0) - (rank[ga] ?: 0)
            val tone = if (moved > 0) GREEN else if (moved < 0) RED else MUT
            val delta = if (a != null && b != null && !a.isNaN() && !b.isNaN())
                "${if (b - a > 0) "+" else ""}${(b - a).roundToInt()}°" else ""
            Row(Modifier.fillMaxWidth().padding(vertical = 3.dp)) {
                Text(LABEL[m]!!, color = FG, fontSize = 12.sp, modifier = Modifier.weight(1f))
                Text(a?.takeIf { !it.isNaN() }?.let { "${it.roundToInt()}°" } ?: "—",
                    color = colorOf(ga.name), fontFamily = FontFamily.Monospace, fontSize = 12.sp)
                Text("  →  ", color = MUT, fontSize = 12.sp)
                Text(b?.takeIf { !it.isNaN() }?.let { "${it.roundToInt()}°" } ?: "—",
                    color = colorOf(gb.name), fontFamily = FontFamily.Monospace, fontSize = 12.sp)
                Text("  $delta", color = tone, fontFamily = FontFamily.Monospace,
                    fontSize = 12.sp, fontWeight = FontWeight.Bold)
            }
        }
        Spacer(Modifier.height(4.dp))
        Text("Green = moved into a better band. Red = moved out of one.",
            color = MUT, fontSize = 10.sp)
    }
}

@Composable
private fun ResultView(r: JSONObject) {
    val angles = r.getJSONObject("angles")
    val grades = r.getJSONObject("grades")
    val bike = r.optString("bike", "road_endurance")
    val zones = Fit.zonesFor(bike)

    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(10.dp).background(colorOf(r.optString("overall")), RoundedCornerShape(5.dp)))
        Spacer(Modifier.width(8.dp))
        Text(
            "${Fit.verdict(Fit.Grade.valueOf(r.optString("overall", "GRAY")))} · " +
                "${r.optInt("strokes")} pedal strokes",
            color = FG, fontWeight = FontWeight.Bold, fontSize = 16.sp
        )
    }
    Spacer(Modifier.height(12.dp))

    listOf(Fit.KNEE, Fit.TORSO, Fit.ELBOW, Fit.SHOULDER).forEach { m ->
        val v = if (angles.has(m)) angles.getDouble(m).toFloat() else Float.NaN
        val g = grades.optString(m, "GRAY")
        Column(
            Modifier.fillMaxWidth().padding(bottom = 8.dp)
                .background(CARD, RoundedCornerShape(12.dp)).padding(12.dp)
        ) {
            Text(LABEL[m]!!.uppercase(), color = MUT, fontFamily = FontFamily.Monospace,
                fontSize = 10.sp, letterSpacing = 1.sp)
            Text(if (v.isNaN()) "—" else "${v.roundToInt()}°",
                color = colorOf(g), fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold, fontSize = 26.sp)
            Text("target ${zones[m]!!.target}", color = MUT,
                fontFamily = FontFamily.Monospace, fontSize = 11.sp)
        }
    }

    if (r.optBoolean("offAxis")) {
        Text("This clip doesn't look square-on — the angles, especially reach, may be stretched. " +
            "Re-film with the camera directly beside you.", color = AMBER, fontSize = 12.sp)
        Spacer(Modifier.height(10.dp))
    }

    Text("DO THIS", color = MUT, fontFamily = FontFamily.Monospace, fontSize = 11.sp, letterSpacing = 1.sp)
    Spacer(Modifier.height(4.dp))
    val advice = r.getJSONArray("advice")
    for (i in 0 until advice.length()) {
        Text("• ${advice.getString(i)}", color = FG, fontSize = 13.sp,
            modifier = Modifier.padding(vertical = 3.dp))
    }
    Spacer(Modifier.height(12.dp))
    Text("2D side-view estimate, not a professional bike fit. Not medical advice. " +
        "Saddle height (knee) is the most reliable number here; reach is the softest.",
        color = MUT, fontSize = 11.sp)
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

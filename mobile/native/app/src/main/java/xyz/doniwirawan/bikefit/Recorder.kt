package xyz.doniwirawan.bikefit

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.video.FileOutputOptions
import androidx.camera.video.Quality
import androidx.camera.video.QualitySelector
import androidx.camera.video.Recorder
import androidx.camera.video.Recording
import androidx.camera.video.VideoCapture
import androidx.camera.video.VideoRecordEvent
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.Alignment
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import java.io.File
import java.util.concurrent.Executors

private const val MAX_SECONDS = 30

/**
 * Record the clip inside the app, with a real camera preview and a front/back switch.
 *
 * The rear camera is the default: to film yourself side-on the phone sits beside the bike, facing
 * you, so the rear (better) camera is the one pointing at the rider. The front camera is there for
 * when you're setting the shot up alone and need to see the frame.
 *
 * The clip is written to the app's own cache and handed straight to the analyzer. It never leaves
 * the device — the app holds no INTERNET permission.
 */
@Composable
fun RecorderScreen(
    onRecorded: (Uri) -> Unit,
    onCancel: () -> Unit,
) {
    val ctx = LocalContext.current
    val owner = LocalLifecycleOwner.current
    val exec = remember { Executors.newSingleThreadExecutor() }

    var granted by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(ctx, Manifest.permission.CAMERA) ==
                PackageManager.PERMISSION_GRANTED
        )
    }
    val ask = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {
        granted = it
    }
    LaunchedEffect(Unit) { if (!granted) ask.launch(Manifest.permission.CAMERA) }

    var backCamera by remember { mutableStateOf(true) }
    var recording by remember { mutableStateOf<Recording?>(null) }
    var seconds by remember { mutableStateOf(0) }
    var capture by remember { mutableStateOf<VideoCapture<Recorder>?>(null) }
    var error by remember { mutableStateOf<String?>(null) }

    DisposableEffect(Unit) { onDispose { recording?.stop(); exec.shutdown() } }

    // count up while recording, and stop at 30s so a forgotten recording can't run forever
    LaunchedEffect(recording) {
        if (recording == null) { seconds = 0; return@LaunchedEffect }
        while (recording != null && seconds < MAX_SECONDS) {
            kotlinx.coroutines.delay(1000); seconds++
        }
        if (seconds >= MAX_SECONDS) recording?.stop()
    }

    if (!granted) {
        Column(Modifier.fillMaxSize().background(P.bg).padding(20.dp), verticalArrangement = Arrangement.Center) {
            SectionTitle("Allow the camera", "The app needs it to record. The clip stays on this phone.")
            PrimaryButton("Allow camera", { ask.launch(Manifest.permission.CAMERA) }, Modifier.fillMaxWidth())
            Spacer(Modifier.height(10.dp))
            GhostButton("Cancel", onCancel, Modifier.fillMaxWidth())
        }
        return
    }

    // Bind the camera exactly once per camera choice.
    //
    // This was originally done inside AndroidView's update block, which writes Compose state
    // (capture, error) — that triggers recomposition, which re-runs update, which unbinds and
    // rebinds the camera, forever. The encoder was torn down and rebuilt on every frame of state
    // change, so by the time Record was pressed the VideoCapture was already being released and
    // recording never started. Binding from a keyed effect breaks that loop.
    val previewView = remember {
        PreviewView(ctx).apply { scaleType = PreviewView.ScaleType.FIT_CENTER }
    }
    LaunchedEffect(backCamera, granted) {
        if (!granted) return@LaunchedEffect
        val provider = ProcessCameraProvider.getInstance(ctx).get()
        val preview = Preview.Builder().build()
            .also { it.setSurfaceProvider(previewView.surfaceProvider) }
        val vc = VideoCapture.withOutput(
            Recorder.Builder().setQualitySelector(QualitySelector.from(Quality.HD)).build()
        )
        try {
            provider.unbindAll()
            provider.bindToLifecycle(
                owner,
                if (backCamera) CameraSelector.DEFAULT_BACK_CAMERA else CameraSelector.DEFAULT_FRONT_CAMERA,
                preview, vc
            )
            capture = vc
            error = null
        } catch (e: Exception) {
            capture = null
            error = "Couldn't open that camera (${e.message ?: "unknown"})."
        }
    }

    // Full-height column: the preview takes whatever is left after the controls. It used to be a
    // fixed 320dp box inside the main scrolling page, so the viewfinder scrolled away while you
    // were trying to frame the shot.
    Column(Modifier.fillMaxSize()) {
    AndroidView(
        modifier = Modifier.fillMaxWidth().weight(1f),
        factory = { previewView }
    )

    Column(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 14.dp)) {
        error?.let {
            Text(it, color = P.red, style = MaterialTheme.typography.bodySmall)
            Spacer(Modifier.height(10.dp))
        }
        Text(
            if (recording != null) "Recording · ${seconds}s of $MAX_SECONDS"
            else "Phone beside the bike, square to your side, at hip height. Pedal steadily. " +
                "It stops by itself at ${MAX_SECONDS}s.",
            color = if (recording != null) Color.White else Color(0xFFA3A8B0),
            style = MaterialTheme.typography.bodySmall,
            fontWeight = if (recording != null) FontWeight.Bold else FontWeight.Normal
        )
        Spacer(Modifier.height(12.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            DarkButton("Cancel", { recording?.stop(); onCancel() }, Modifier.weight(1f))
            Spacer(Modifier.width(10.dp))
            PrimaryButton(
                if (recording != null) "Stop" else "Record",
                {
                    // never fail silently: if the camera isn't bound yet, say so
                    val vc = capture
                    if (vc == null) { error = "The camera isn't ready yet. Give it a second."; return@PrimaryButton }
                    if (recording != null) { recording?.stop(); recording = null; return@PrimaryButton }
                    val file = File(ctx.cacheDir, "recording.mp4")
                    if (file.exists()) file.delete()
                    val opts = FileOutputOptions.Builder(file).build()
                    try {
                        recording = vc.output.prepareRecording(ctx, opts)
                            .start(ContextCompat.getMainExecutor(ctx)) { ev ->
                                if (ev is VideoRecordEvent.Finalize) {
                                    recording = null
                                    if (ev.hasError()) error = "Recording failed (${ev.error})."
                                    else onRecorded(Uri.fromFile(file))
                                }
                            }
                        error = null
                    } catch (e: Exception) {
                        error = "Couldn't start recording (${e.message ?: "unknown"})."
                    }
                },
                Modifier.weight(1.3f),
                container = if (recording != null) P.red else P.accent,
                ink = if (recording != null) Color.White else P.accentInk,
            )
            Spacer(Modifier.width(10.dp))
            // switching mid-recording would drop the clip
            DarkButton(if (backCamera) "Rear" else "Front", { backCamera = !backCamera }, Modifier.weight(1f),
                enabled = recording == null)
        }
    }
    }
}

/** Outlined button for the black camera screen, which stays dark in both themes. */
@Composable
private fun DarkButton(text: String, onClick: () -> Unit, modifier: Modifier = Modifier, enabled: Boolean = true) {
    OutlinedButton(
        onClick = onClick, enabled = enabled, modifier = modifier.heightIn(min = 52.dp),
        shape = RoundedCornerShape(12.dp), border = BorderStroke(1.dp, Color(0xFF3A3D42)),
        colors = ButtonDefaults.outlinedButtonColors(containerColor = Color(0xFF1C1E21),
            contentColor = Color(0xFFEEF0F2), disabledContentColor = Color(0xFF6B7280)),
        contentPadding = PaddingValues(horizontal = 10.dp),
    ) { Text(text, style = MaterialTheme.typography.labelLarge, color = LocalContentColor.current) }
}

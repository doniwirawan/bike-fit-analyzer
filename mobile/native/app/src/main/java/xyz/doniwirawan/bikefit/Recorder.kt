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
        Column(Modifier.fillMaxWidth().padding(vertical = 12.dp)) {
            Text("Camera permission is needed to record.", color = Color(0xFFDFE6F0), fontSize = 13.sp)
            Spacer(Modifier.height(8.dp))
            Row {
                Button(onClick = { ask.launch(Manifest.permission.CAMERA) }) { Text("Allow camera") }
                Spacer(Modifier.width(8.dp))
                OutlinedButton(onClick = onCancel) { Text("Cancel") }
            }
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

    AndroidView(
        modifier = Modifier.fillMaxWidth().height(320.dp),
        factory = { previewView }
    )

    Spacer(Modifier.height(8.dp))
    error?.let { Text(it, color = Color(0xFFDC2626), fontSize = 12.sp); Spacer(Modifier.height(6.dp)) }

    Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
        Button(
            onClick = {
                // never fail silently: if the camera isn't bound yet, say so
                val vc = capture
                if (vc == null) { error = "Camera isn't ready yet — give it a second."; return@Button }
                if (recording != null) { recording?.stop(); recording = null; return@Button }
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
            colors = ButtonDefaults.buttonColors(
                containerColor = if (recording != null) Color(0xFFDC2626) else Color(0xFF4D8BFF)
            )
        ) { Text(if (recording != null) "Stop (${seconds}s)" else "Record") }

        Spacer(Modifier.width(8.dp))
        OutlinedButton(
            onClick = { backCamera = !backCamera },
            enabled = recording == null       // switching mid-recording would drop the clip
        ) { Text(if (backCamera) "Rear camera" else "Front camera") }

        Spacer(Modifier.width(8.dp))
        OutlinedButton(onClick = { recording?.stop(); onCancel() }) { Text("Cancel") }
    }
    Spacer(Modifier.height(6.dp))
    Text(
        "Put the phone beside the bike, square to your side, roughly at hip height. " +
            "Pedal steadily. Stops automatically at ${MAX_SECONDS}s.",
        color = Color(0xFF8B97A8), fontSize = 11.sp
    )
}

package xyz.doniwirawan.bikefit

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private const val SITE = "https://bikefit.doniwirawan.xyz"

/**
 * About, FAQ, the research the target zones come from, and the privacy/terms summary.
 *
 * The sources listed here are the ones in files/bikefit-research-ranges.md — the same file the
 * zones in [Fit] are derived from. If a zone changes there, the citation here has to still
 * support it. Nothing on this screen is a claim the repo cannot back up.
 *
 * Links open in the browser via an intent. That works without the INTERNET permission, because
 * it is the browser that fetches the page, not this app.
 */
@Composable
fun AboutScreen(onBack: () -> Unit) {
    val ctx = LocalContext.current
    fun open(url: String) =
        ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        })

    Column(
        Modifier.fillMaxSize().background(BG).padding(18.dp).verticalScroll(rememberScrollState())
    ) {
        Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
            Image(painterResource(R.mipmap.ic_launcher), null, Modifier.size(34.dp))
            Spacer(Modifier.width(10.dp))
            Text("ABOUT", color = FG, fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold, letterSpacing = 2.sp, fontSize = 14.sp)
        }
        Spacer(Modifier.height(14.dp))

        Text(
            "Bike Fit Analyzer measures your riding position from a short side-on video of you " +
                "pedalling. Everything runs on this phone.",
            color = FG, fontSize = 14.sp
        )
        Spacer(Modifier.height(6.dp))
        Text(
            "It is a 2D side-view estimate, not a professional bike fit, and not medical advice. " +
                "Saddle height (knee) is the most reliable number it gives you; reach is the softest.",
            color = MUT, fontSize = 12.sp
        )

        Section("HOW TO FILM")
        Bullet("Phone beside the bike, square to your side, roughly at hip height.")
        Bullet("20–30 seconds, pedalling at a steady rhythm as you normally would.")
        Bullet("A turbo trainer is easiest, but any steady pedalling works.")
        Bullet("If the clip is not square-on, the app says so — reach stretches the most when it isn't.")

        Section("FAQ")
        Qa("Is my video uploaded anywhere?",
            "No. This app holds no internet permission at all, so it cannot send your video, your " +
                "measurements or anything else anywhere. The pose model is bundled inside the app, " +
                "so it works with no connection. Your clip and saved results stay in the app's own " +
                "private storage, and uninstalling deletes them.")
        Qa("Which bikes does it work with?",
            "Almost any — road, MTB, gravel, TT/triathlon, hybrid, commuter or e-bike. What gets " +
                "analyzed is your body position, not the bike. Only the torso target changes with " +
                "the bike you pick; saddle height (knee) is the same on any of them.")
        Qa("How accurate is it, really?",
            "Accurate enough to find the obvious problems, like a saddle clearly too high or too " +
                "low. The knee angle is the most consistent measurement; reach is the softest. " +
                "A phone video only resolves to a few degrees, so the app uses a ~2.5° edge " +
                "tolerance and takes the median across several pedal strokes rather than trusting " +
                "any single frame.")
        Qa("Can it replace a professional bike fit?",
            "No. It is built to help you run a basic check and find clearly visible problems, " +
                "before you adjust anything yourself or book a session with a fitter.")
        Qa("Why does the stroke count differ from the website?",
            "The app samples about 15 frames a second while the website walks every frame, so it " +
                "finds slightly fewer strokes. The angles are medians across the strokes it does " +
                "find, so this doesn't move them meaningfully.")
        Qa("Is it free?",
            "Yes. The source is published so you can check every privacy claim here for yourself. " +
                "It is source-available rather than open source: you may read it, learn from it and " +
                "use the tool, but not build a competing product from it.")

        Section("THE TARGET ZONES")
        Text(
            "These are the green zones the app grades against. They are dynamic ranges — measured " +
                "while pedalling on video — which run a few degrees higher than static goniometer " +
                "numbers taken on a stationary rider.",
            color = MUT, fontSize = 12.sp
        )
        Spacer(Modifier.height(8.dp))
        ZoneRow("Knee at bottom (BDC)", "30–40°", "over ~42 saddle too low · under ~28 too high")
        ZoneRow("Torso from horizontal", "40–50°", "road endurance; moves with the bike type")
        ZoneRow("Elbow bend", "15–30°", "near 0 = locked out")
        ZoneRow("Shoulder (reach)", "80–95°", "much lower = closed, scrunched cockpit")

        Section("RESEARCH")
        Text(
            "The zones above come from the following sources. Tap one to open it.",
            color = MUT, fontSize = 12.sp
        )
        Spacer(Modifier.height(8.dp))
        Paper(
            "Holmes method — knee angle at the bottom of the stroke",
            "The clinical standard this app's knee zone follows. Reports joint-angle averages of " +
                "knee 36 ± 7° and elbow 19 ± 8°.",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC9219349/", ::open
        )
        Paper(
            "Dynamic vs static measurement validity",
            "Angles measured while pedalling on video run about 8° higher than static goniometer " +
                "numbers. This is why the knee zone here is a dynamic 30–40° rather than a static 25–35°.",
            "https://pubmed.ncbi.nlm.nih.gov/24499342/", ::open
        )
        Paper(
            "Cycling kinematics in healthy adults (31 adults, saddle at 85.5% inseam)",
            "Source of the healthy frontal-plane movement figures: pelvis coronal ROM 7.1 ± 2.5°, " +
                "knee coronal ROM 6.6 ± 2.7°. A correctly-fitted rider does rock.",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC8675512/", ::open
        )
        Paper(
            "Knee alignment and frontal-plane knee biomechanics in cycling",
            "Peak knee adduction by alignment group — varus 10.3 ± 4.8°, neutral 5.2°, valgus −2.2°.",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC5950749/", ::open
        )
        Paper(
            "Reliability of 2D video assessment of frontal-plane knee valgus",
            "SEM 2.72–3.01°, smallest detectable difference 7.54–8.93°. This is the measurement " +
                "floor under any 2D video threshold, no matter how good the pose model is.",
            "https://pubmed.ncbi.nlm.nih.gov/22104115/", ::open
        )
        Paper(
            "Practitioner cross-check for the full joint set",
            "Used to sanity-check the torso, shoulder and hip ranges against fitting practice.",
            "https://www.bikefitadviser.com/blog/not-basic-bike-fit-part-3-bike-fit-joint-angles", ::open
        )

        Section("PRIVACY")
        Text(
            "This app collects nothing. It has no internet permission, so it cannot send your " +
                "video, measurements or anything else anywhere — not to us, not to anyone. Camera " +
                "access is only requested when you press Record. Your clip and your saved results " +
                "live in the app's private storage on this phone; uninstalling the app deletes them.",
            color = FG, fontSize = 13.sp
        )
        Spacer(Modifier.height(8.dp))
        LinkButton("Read the full privacy policy") { open("$SITE/privacy") }

        Section("TERMS")
        Text(
            "Free to use, with no warranty. The readings are an estimate to work from, not a " +
                "professional fit and not medical advice — what you change on your bike is your " +
                "decision. The source is published to read and learn from, but not to build a " +
                "competing product from.",
            color = FG, fontSize = 13.sp
        )
        Spacer(Modifier.height(8.dp))
        LinkButton("Read the full terms") { open("$SITE/terms") }

        Section("THE PROJECT")
        Text("By Doni Wirawan. The web version of this analyzer runs the same grading rules.",
            color = FG, fontSize = 13.sp)
        Spacer(Modifier.height(8.dp))
        LinkButton("bikefit.doniwirawan.xyz") { open(SITE) }
        Spacer(Modifier.height(4.dp))
        LinkButton("Source on GitHub") { open("https://github.com/doniwirawan/bike-fit-analyzer") }

        Spacer(Modifier.height(24.dp))
        Button(onClick = onBack, modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(containerColor = ACCENT)) { Text("Back") }
        Spacer(Modifier.height(24.dp))
    }
}

@Composable
private fun Section(title: String) {
    Spacer(Modifier.height(24.dp))
    Text(title, color = MUT, fontFamily = FontFamily.Monospace,
        fontSize = 11.sp, letterSpacing = 1.sp)
    Spacer(Modifier.height(8.dp))
}

@Composable
private fun Bullet(text: String) {
    Text("• $text", color = FG, fontSize = 13.sp, modifier = Modifier.padding(bottom = 5.dp))
}

@Composable
private fun Qa(q: String, a: String) {
    Column(
        Modifier.fillMaxWidth().padding(bottom = 8.dp)
            .background(CARD, RoundedCornerShape(12.dp)).padding(12.dp)
    ) {
        Text(q, color = FG, fontSize = 13.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(4.dp))
        Text(a, color = MUT, fontSize = 12.sp)
    }
}

@Composable
private fun ZoneRow(label: String, target: String, note: String) {
    Column(
        Modifier.fillMaxWidth().padding(bottom = 6.dp)
            .background(CARD, RoundedCornerShape(10.dp)).padding(10.dp)
    ) {
        Row(Modifier.fillMaxWidth()) {
            Text(label, color = FG, fontSize = 12.sp, modifier = Modifier.weight(1f))
            Text(target, color = GREEN, fontFamily = FontFamily.Monospace,
                fontSize = 12.sp, fontWeight = FontWeight.Bold)
        }
        Text(note, color = MUT, fontSize = 11.sp)
    }
}

@Composable
private fun Paper(title: String, what: String, url: String, open: (String) -> Unit) {
    Column(
        Modifier.fillMaxWidth().padding(bottom = 8.dp)
            .background(CARD, RoundedCornerShape(12.dp))
            .clickable { open(url) }.padding(12.dp)
    ) {
        Text(title, color = FG, fontSize = 13.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(4.dp))
        Text(what, color = MUT, fontSize = 12.sp)
        Spacer(Modifier.height(6.dp))
        Text(url, color = ACCENT, fontSize = 11.sp, fontFamily = FontFamily.Monospace,
            textDecoration = TextDecoration.Underline)
    }
}

@Composable
private fun LinkButton(label: String, onClick: () -> Unit) {
    OutlinedButton(onClick = onClick, modifier = Modifier.fillMaxWidth()) {
        Text(label, color = FG, fontSize = 13.sp)
    }
}

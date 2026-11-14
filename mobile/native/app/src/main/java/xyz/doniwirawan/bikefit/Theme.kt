package xyz.doniwirawan.bikefit

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * The website's design system (web/base.css), carried over so the app and the site read as one
 * product. Same tokens, same rule: the brand blue is for the primary action and links, green /
 * amber / red are grades and nothing else, everything else is neutral.
 *
 * Mona Sans is SIL OFL 1.1, the same family the site self-hosts. Android can't read the site's
 * variable woff2, so the app bundles the static cuts it uses: four weights at normal width, and
 * SemiExpanded ExtraBold for the big measured numbers (the site sets those at font-stretch 118%).
 */
data class Palette(
    val bg: Color, val card: Color, val fg: Color, val mut: Color, val line: Color, val grid: Color,
    val accent: Color, val accentInk: Color,
    val green: Color, val amber: Color, val red: Color, val gray: Color,
    val dark: Boolean,
)

private val Light = Palette(
    bg = Color(0xFFF4F5F7), card = Color(0xFFFFFFFF), fg = Color(0xFF0D1015), mut = Color(0xFF545D6B),
    line = Color(0xFFE1E4EA), grid = Color(0xFFECEEF2),
    accent = Color(0xFF2D4FE0), accentInk = Color(0xFFFFFFFF),
    green = Color(0xFF15803D), amber = Color(0xFFB45309), red = Color(0xFFD1282A), gray = Color(0xFF6B7280),
    dark = false,
)

private val Dark = Palette(
    bg = Color(0xFF141517), card = Color(0xFF1C1E21), fg = Color(0xFFEEF0F2), mut = Color(0xFFA3A8B0),
    line = Color(0xFF2D3035), grid = Color(0xFF232529),
    accent = Color(0xFF8299FF), accentInk = Color(0xFF101114),
    green = Color(0xFF3FB950), amber = Color(0xFFE3A33B), red = Color(0xFFF26B5B), gray = Color(0xFF8D929A),
    dark = true,
)

private val LocalPalette = staticCompositionLocalOf { Dark }

/** The current theme's colours. */
val P: Palette @Composable @ReadOnlyComposable get() = LocalPalette.current

val Mona = FontFamily(
    Font(R.font.monasans_regular, FontWeight.Normal),
    Font(R.font.monasans_semibold, FontWeight.SemiBold),
    Font(R.font.monasans_bold, FontWeight.Bold),
    Font(R.font.monasans_extrabold, FontWeight.ExtraBold),
)

/** Wide and heavy, for numbers and the big headings. */
val MonaWide = FontFamily(Font(R.font.monasanssemiexpanded_extrabold, FontWeight.ExtraBold))

val RADIUS = 14.dp
val RADIUS_SM = 10.dp

@Composable
fun BikeFitTheme(content: @Composable () -> Unit) {
    val p = if (isSystemInDarkTheme()) Dark else Light
    val scheme = if (p.dark)
        darkColorScheme(background = p.bg, surface = p.card, onSurface = p.fg, onBackground = p.fg,
            primary = p.accent, onPrimary = p.accentInk, outline = p.line, surfaceVariant = p.grid,
            onSurfaceVariant = p.mut, error = p.red)
    else
        lightColorScheme(background = p.bg, surface = p.card, onSurface = p.fg, onBackground = p.fg,
            primary = p.accent, onPrimary = p.accentInk, outline = p.line, surfaceVariant = p.grid,
            onSurfaceVariant = p.mut, error = p.red)
    val base = TextStyle(fontFamily = Mona, color = p.fg)
    CompositionLocalProvider(LocalPalette provides p) {
        MaterialTheme(
            colorScheme = scheme,
            typography = Typography(
                bodyLarge = base.copy(fontSize = 16.sp, lineHeight = 24.sp),
                bodyMedium = base.copy(fontSize = 15.sp, lineHeight = 22.sp),
                bodySmall = base.copy(fontSize = 13.sp, lineHeight = 19.sp),
                labelLarge = base.copy(fontSize = 15.sp, fontWeight = FontWeight.SemiBold),
                labelMedium = base.copy(fontSize = 13.sp, fontWeight = FontWeight.SemiBold),
            ),
        ) { ProvideTextStyle(MaterialTheme.typography.bodyMedium, content) }
    }
}

fun Palette.gradeColor(g: String) = when (g) {
    "GREEN" -> green; "AMBER" -> amber; "RED" -> red; else -> gray
}

/* ------------------------------------------------------------------ pieces */

/** A bordered card on the page ground, like .mcard on the site. */
@Composable
fun Card(modifier: Modifier = Modifier, pad: Dp = 16.dp, content: @Composable ColumnScope.() -> Unit) {
    Column(
        modifier.fillMaxWidth()
            .background(P.card, RoundedCornerShape(RADIUS))
            .border(1.dp, P.line, RoundedCornerShape(RADIUS))
            .padding(pad),
        content = content
    )
}

/** Section heading: sentence case and weight, never a tracked uppercase label. */
@Composable
fun SectionTitle(text: String, sub: String? = null) {
    Text(text, fontFamily = MonaWide, fontWeight = FontWeight.ExtraBold, fontSize = 19.sp,
        letterSpacing = (-0.3).sp, color = P.fg)
    sub?.let {
        Spacer(Modifier.height(3.dp))
        Text(it, color = P.mut, style = MaterialTheme.typography.bodySmall)
    }
    Spacer(Modifier.height(12.dp))
}

@Composable
fun PrimaryButton(text: String, onClick: () -> Unit, modifier: Modifier = Modifier, enabled: Boolean = true,
                  container: Color = P.accent, ink: Color = P.accentInk) {
    Button(
        onClick = onClick, enabled = enabled,
        modifier = modifier.heightIn(min = 52.dp),
        shape = RoundedCornerShape(RADIUS_SM + 2.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = container, contentColor = ink,
            disabledContainerColor = P.grid, disabledContentColor = P.mut),
        contentPadding = PaddingValues(horizontal = 20.dp),
    ) { Text(text, style = MaterialTheme.typography.labelLarge, color = LocalContentColor.current) }
}

@Composable
fun GhostButton(text: String, onClick: () -> Unit, modifier: Modifier = Modifier, enabled: Boolean = true) {
    OutlinedButton(
        onClick = onClick, enabled = enabled,
        modifier = modifier.heightIn(min = 52.dp),
        shape = RoundedCornerShape(RADIUS_SM + 2.dp),
        border = BorderStroke(1.dp, P.line),
        colors = ButtonDefaults.outlinedButtonColors(containerColor = P.card, contentColor = P.fg,
            disabledContentColor = P.mut),
        contentPadding = PaddingValues(horizontal = 18.dp),
    ) { Text(text, style = MaterialTheme.typography.labelLarge, color = LocalContentColor.current) }
}

@Composable
fun GradeDot(grade: String, size: Dp = 10.dp) {
    Box(Modifier.size(size).background(P.gradeColor(grade), RoundedCornerShape(50)))
}

/**
 * Where a reading sits against its target: a neutral track, the green band, and a marker at the
 * value. The track spans the red edges plus one green-band width either side, so a reading
 * well into the red still lands on the bar.
 */
@Composable
fun RangeBar(value: Float?, z: Fit.Zone) {
    val pad = (z.gHi - z.gLo).toFloat()
    val lo = z.rLo - pad; val hi = z.rHi + pad
    fun at(v: Float) = ((v - lo) / (hi - lo)).coerceIn(0f, 1f)
    val track = P.grid; val band = P.green.copy(alpha = .55f); val mark = P.fg
    Canvas(Modifier.fillMaxWidth().height(16.dp)) {
        val y = size.height / 2; val h = 6.dp.toPx(); val r = CornerRadius(h / 2)
        drawRoundRect(track, Offset(0f, y - h / 2), Size(size.width, h), r)
        val x0 = at(z.gLo.toFloat()) * size.width; val x1 = at(z.gHi.toFloat()) * size.width
        drawRoundRect(band, Offset(x0, y - h / 2), Size(x1 - x0, h), r)
        if (value != null && !value.isNaN()) {
            val w = 4.dp.toPx(); val x = at(value) * size.width
            drawRoundRect(mark, Offset((x - w / 2).coerceIn(0f, size.width - w), 0f), Size(w, size.height),
                CornerRadius(w / 2))
        }
    }
    Box(Modifier.fillMaxWidth().padding(top = 2.dp)) {
        // the green band's edges, labelled under the bar
        BoxWithConstraints(Modifier.fillMaxWidth()) {
            listOf(z.gLo, z.gHi).forEach { v ->
                Text("$v°", color = P.mut, fontSize = 11.sp, fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.offset(x = maxWidth * at(v.toFloat()) - 10.dp))
            }
        }
    }
}

@Composable
fun Divider() = HorizontalDivider(thickness = 1.dp, color = P.line)

@Composable
fun Header(title: String, action: String? = null, onAction: () -> Unit = {}) {
    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
        androidx.compose.foundation.Image(
            androidx.compose.ui.res.painterResource(R.mipmap.ic_launcher), null,
            Modifier.size(32.dp).clip(RoundedCornerShape(8.dp))
        )
        Spacer(Modifier.width(10.dp))
        Text(title, fontWeight = FontWeight.ExtraBold, fontSize = 17.sp, letterSpacing = (-0.2).sp,
            modifier = Modifier.weight(1f))
        action?.let {
            TextButton(onClick = onAction, modifier = Modifier.heightIn(min = 44.dp)) {
                Text(it, color = P.fg, style = MaterialTheme.typography.labelMedium)
            }
        }
    }
}

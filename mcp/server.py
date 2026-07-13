"""MCP server for Bike Fit Analyzer.

Wraps the existing YOLO-pose pipeline (files/analyze_bikefit.py) so a clip can be
graded from a chat client instead of a browser.

Honest caveat, surfaced in every result: this path uses YOLO pose, while the web
app at bikefit.doniwirawan.xyz uses MediaPipe. The grading zones are identical,
but the two pose models can disagree by a few degrees on the same clip. The web
app is the reference.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / ".venv" / "Scripts" / "python.exe"
if not PY.exists():
    PY = Path(sys.executable)
SCRIPT = ROOT / "files" / "analyze_bikefit.py"
MODEL = ROOT / "yolo11x-pose.pt"

# Torso target by bike type — the same numbers the web app grades against, so the two
# cannot drift apart. (green_lo, green_hi, red_lo, red_hi)
BIKE_TORSO = {
    "road_endurance": (40, 50, 34, 56),
    "road_race":      (32, 42, 28, 48),
    "tt_tri":         (12, 28,  8, 34),
    "gravel":         (42, 52, 36, 58),
    "mtb":            (46, 58, 40, 64),
    "city":           (55, 70, 48, 78),
}
ORDER = {"GRAY": 0, "GREEN": 1, "AMBER": 2, "RED": 3}

mcp = FastMCP("bike-fit-analyzer")


def _grade(value, zone):
    if value is None:
        return "GRAY"
    g_lo, g_hi, r_lo, r_hi = zone
    if g_lo <= value <= g_hi:
        return "GREEN"
    if value < r_lo or value > r_hi:
        return "RED"
    return "AMBER"


@mcp.tool()
def list_bike_types() -> dict:
    """List the bike types, and the torso angle each one is graded against.

    Saddle height (knee), elbow and shoulder targets are the same on every bike —
    only the torso target moves, because that is what changes when a position gets
    more or less aggressive.
    """
    return {
        "bike_types": {k: f"{v[0]}-{v[1]}° (red outside {v[2]}-{v[3]}°)"
                       for k, v in BIKE_TORSO.items()},
        "fixed_on_every_bike": {
            "knee_flexion_bdc": "30-40°",
            "elbow_flexion": "15-30°",
            "shoulder_angle": "80-95°",
        },
    }


@mcp.tool()
def analyze_bike_fit(video_path: str,
                     bike_type: str = "road_endurance",
                     start_sec: float | None = None,
                     end_sec: float | None = None) -> dict:
    """Grade a side-on cycling clip: knee, torso, elbow and shoulder angles.

    Give it a video of yourself pedalling, filmed square-on from the side at roughly
    hip height. Angles are measured at the bottom of every pedal stroke and reported
    as the median, then graded green / amber / red against bike-fitting research.

    video_path: path to the clip (.mp4, .mov, .webm)
    bike_type:  one of road_endurance, road_race, tt_tri, gravel, mtb, city
    start_sec / end_sec: optionally trim to a steady section of the clip
    """
    src = Path(video_path).expanduser()
    if not src.exists():
        return {"error": f"No such video: {src}"}
    if bike_type not in BIKE_TORSO:
        return {"error": f"Unknown bike_type {bike_type!r}. Options: {', '.join(BIKE_TORSO)}"}

    with tempfile.TemporaryDirectory() as tmp:
        cmd = [str(PY), str(SCRIPT), "--input", str(src), "--out", tmp, "--model", str(MODEL)]
        if start_sec is not None:
            cmd += ["--start", str(start_sec)]
        if end_sec is not None:
            cmd += ["--end", str(end_sec)]
        run = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
        results_file = Path(tmp) / "report.json"
        if not results_file.exists():
            tail = (run.stderr or run.stdout or "").strip().splitlines()[-6:]
            return {"error": "Analysis failed.", "detail": "\n".join(tail)}
        data = json.loads(results_file.read_text(encoding="utf-8"))

    angles = data["angles"]
    grades = dict(data["grades"])

    # Re-grade the torso against the chosen bike; the script only knows road-endurance.
    torso = angles.get("torso_from_horiz")
    zone = BIKE_TORSO[bike_type]
    grades["torso_from_horiz"] = _grade(torso, zone)
    overall = max(grades.values(), key=lambda g: ORDER[g])
    verdict = {"GREEN": "Dialed", "AMBER": "Minor tweaks",
               "RED": "Fix needed", "GRAY": "Incomplete"}[overall]

    knee = angles.get("knee_flexion_bdc")
    advice = []
    if knee is not None and grades["knee_flexion_bdc"] != "GREEN":
        mm = min(20, round(abs(knee - 35) * 1.5))
        if knee > 40:
            advice.append(f"Saddle looks low — knee still bent {knee:.0f}° at the bottom "
                          f"(aim 30–40°). Raise it about {mm}mm, in 2–3mm steps, and re-film. "
                          f"This is the most reliable reading here.")
        else:
            advice.append(f"Saddle looks high — leg nearly straight ({knee:.0f}°) at the bottom "
                          f"(aim 30–40°). Lower it about {mm}mm, in 2–3mm steps, and re-film. "
                          f"This is the most reliable reading here.")
    if torso is not None and grades["torso_from_horiz"] != "GREEN":
        advice.append(f"Torso {torso:.0f}° against a {zone[0]}–{zone[1]}° target for a "
                      f"{bike_type.replace('_', ' ')} position.")
    advice += [f for f in data.get("fixes", []) if "addle" not in f and "orso" not in f]
    if not advice:
        advice = ["Everything's in range — nice fit. Re-film if you change anything."]

    return {
        "verdict": verdict,
        "bike_type": bike_type,
        "angles_deg": {k: (round(v, 1) if isinstance(v, (int, float)) else v)
                       for k, v in angles.items()},
        "grades": grades,
        "targets": {
            "knee_flexion_bdc": "30-40",
            "torso_from_horiz": f"{zone[0]}-{zone[1]}",
            "elbow_flexion": "15-30",
            "shoulder_angle": "80-95",
        },
        "advice": advice,
        "caveats": [
            "2D side-view estimate, not a professional 3D bike fit. Not medical advice.",
            "Saddle height (knee) is the most reliable number; reach/shoulder is the softest — "
            "don't change a stem off one clip.",
            "This tool uses YOLO pose; the web app at bikefit.doniwirawan.xyz uses MediaPipe. "
            "The grading zones are identical, but the two models can differ by a few degrees "
            "on the same clip. The web app is the reference.",
        ],
    }


if __name__ == "__main__":
    mcp.run()

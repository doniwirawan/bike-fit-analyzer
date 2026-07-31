"""
Bike Fit Analyzer — desktop.

Opens web/app.html in a native window and hands the analysis to Python instead of to
MediaPipe. It is deliberately the *same* HTML file the website serves: the report cards,
the saved-results list, the exports and both languages are whatever is live on the site,
with no second copy to keep in step. The page notices it is running inside pywebview
(window.pywebview exists) and switches its file picker and analysis over; in a browser
none of that code runs.

    python desktop/bikefit.py            # open the window
    python desktop/bikefit.py CLIP.mp4   # open it and analyze CLIP.mp4 straight away

Needs: pywebview, ultralytics, opencv-python, numpy  (see requirements-desktop.txt)
"""

import json
import os
import sys
from pathlib import Path

import webview

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine  # noqa: E402

FROZEN = getattr(sys, "frozen", False)
ROOT = Path(sys._MEIPASS) if FROZEN else Path(__file__).resolve().parent.parent
UI = ROOT / "web" / "app.html"

# Saved results have to outlive the app. A frozen bundle unpacks to a temp directory that is
# deleted on exit, so the browser profile must live somewhere the user owns instead.
DATA = (Path(os.environ.get("LOCALAPPDATA", Path.home())) / "BikeFitAnalyzer"
        if FROZEN else ROOT / ".desktop-data")

VIDEO_TYPES = ("Video files (*.mp4;*.mov;*.webm;*.avi;*.mkv;*.m4v)", "All files (*.*)")


class Api:
    """Everything the page is allowed to ask this computer to do."""

    def __init__(self):
        self.window = None

    # --- called from the page ---

    def pick_video(self):
        """Native file dialog. The page can't read a dropped file's path from inside a
        webview, so choosing a file is the one route in."""
        paths = self.window.create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=False, file_types=VIDEO_TYPES)
        return paths[0] if paths else None

    def analyze(self, path, view="side"):
        try:
            return {"ok": True, **engine.analyze(path, view, self._progress)}
        except Exception as exc:                      # surfaced in the page's error box
            return {"ok": False, "error": str(exc)}

    # --- pushed to the page ---

    def _progress(self, stage, pct):
        """The page maps the stage to its own translated string, so progress is reported
        in whichever language the UI is set to rather than in English from here."""
        if not self.window:
            return
        try:
            self.window.evaluate_js(
                f"window.__nativeProgress && window.__nativeProgress({json.dumps(stage)},{int(pct)})")
        except Exception:
            pass                                       # window closed mid-run


def selftest(clip):
    """Analyse a clip and print the numbers, without opening a window.

        BikeFitAnalyzer.exe --selftest CLIP.mp4

    A packaged build is otherwise only testable by looking at it, which says nothing about
    whether torch, OpenCV and the pose model actually survived being frozen. This runs the
    whole pipeline and prints the result, so a build can be checked from a terminal or a CI
    job. Compare the angles against the same clip in the browser build.
    """
    result = engine.analyze(clip, "side", lambda stage, pct: print(f"  {stage} {pct}%", flush=True))
    print("\nengine :", result["engine"])
    print("strokes:", result["strokes"], " off-axis:", result["offAxis"])
    for metric, value in result["R"].items():
        print(f"  {metric:20} {value if value is None else round(value, 1)}")
    print("  hip at top          ", None if result["hipTop"] is None else round(result["hipTop"], 1))
    return 0


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--selftest":
        # console=False means there is no attached console in a packaged build; redirect
        # stdout when running it (build.ps1 and the README both show how).
        sys.exit(selftest(sys.argv[2]))

    if not UI.exists():
        sys.exit(f"UI not found at {UI} — run this from the repo, not a copy of desktop/.")

    api = Api()
    # Hand pywebview the path, not a file:// URI, so http_server below can serve it from
    # 127.0.0.1. A file:// page is an opaque origin: localStorage is unreliable there, and
    # localStorage is where every saved result lives.
    window = webview.create_window(
        "Bike Fit Analyzer", str(UI), js_api=api,
        width=1200, height=920, min_size=(880, 640))
    api.window = window

    # A path on the command line analyses immediately, which makes "right-click a clip,
    # open with Bike Fit" work and gives a one-liner to test with.
    if len(sys.argv) > 1:
        clip = str(Path(sys.argv[1]).resolve())

        # pywebview passes the window to loaded handlers in some versions and nothing in
        # others; take whatever comes and use the window we already hold.
        def kickoff(*_):
            window.evaluate_js(f"window.__nativeRun && window.__nativeRun({json.dumps(clip)})")

        window.events.loaded += kickoff

    # private_mode defaults to True, which throws away localStorage when the window closes —
    # every saved result would vanish between runs. storage_path keeps them beside the app.
    webview.start(http_server=True, private_mode=False,
                  storage_path=str(DATA))


if __name__ == "__main__":
    main()

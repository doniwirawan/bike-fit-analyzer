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
import sys
from pathlib import Path

import webview

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
UI = ROOT / "web" / "app.html"

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

    def analyze(self, path):
        try:
            return {"ok": True, **engine.analyze(path, self._progress)}
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


def main():
    if not UI.exists():
        sys.exit(f"UI not found at {UI} — run this from the repo, not a copy of desktop/.")

    api = Api()
    window = webview.create_window(
        "Bike Fit Analyzer", UI.as_uri(), js_api=api,
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

    webview.start()


if __name__ == "__main__":
    main()

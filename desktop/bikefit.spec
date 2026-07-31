# PyInstaller spec for the desktop app.  Build with desktop/build.ps1, not by hand.
#
# One-folder, not one-file: a one-file build unpacks ~800MB to a temp directory on every
# launch, which takes the better part of a minute before the window even appears. The folder
# build starts immediately and is what gets zipped for release.

from pathlib import Path
import sys

ROOT = Path(SPECPATH).parent

datas = [
    # The UI is the website's own app.html plus everything it links — fonts, base.css,
    # open-props, theme.js. Shipping the whole folder keeps the desktop build from needing
    # its own copy of any of it.
    (str(ROOT / "web"), "web"),
    # analyze_bikefit.py is imported at runtime via sys.path, so it travels as data.
    (str(ROOT / "files" / "analyze_bikefit.py"), "files"),
    (str(ROOT / "yolo11x-pose.pt"), "."),
]

hiddenimports = [
    "webview.platforms.edgechromium",   # the Windows backend, loaded by name at runtime
    "clr_loader",
    "pythonnet",
]

# Ultralytics reads its own metadata and config at import time.
try:
    from PyInstaller.utils.hooks import collect_data_files
    datas += collect_data_files("ultralytics")
except Exception:
    pass

a = Analysis(
    [str(ROOT / "desktop" / "bikefit.py")],
    pathex=[str(ROOT / "desktop")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    # Only rival GUI toolkits, which nothing in this dependency tree imports.
    #
    # Everything else that looked excludable turned out not to be. `from ultralytics import
    # YOLO` reaches torch.utils.data.dataloader (which imports torch.distributed
    # unconditionally) and ultralytics.models.yolo.semantic.train (which imports
    # matplotlib.pyplot at module level). Both excludes produced a build that launched and
    # then died with ModuleNotFoundError the moment a clip was analysed. The size they save
    # is not worth a broken app — the real fix for size is dropping torch entirely, see the
    # ONNX note in README.md.
    excludes=["tkinter", "PySide6", "PyQt5", "PyQt6", "IPython", "notebook"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="BikeFitAnalyzer",
    console=False,                      # no terminal window behind the app
    icon=str(ROOT / "web" / "logo-64.png") if (ROOT / "web" / "logo-64.png").exists() else None,
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=False,             # UPX on torch DLLs is a reliable way to break them
    name="BikeFitAnalyzer",
)

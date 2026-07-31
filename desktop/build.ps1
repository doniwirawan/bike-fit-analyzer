# Builds the installable Windows app.
#
#   pwsh -File desktop\build.ps1
#
# Output: dist\BikeFitAnalyzer\BikeFitAnalyzer.exe  (a folder — ship the whole folder, or
# the zip this script leaves next to it).
#
# It is large. Torch is ~490MB, OpenCV ~110MB and the YOLO11x pose model ~113MB, and all
# three are genuinely needed for the accuracy this build exists to provide. Expect ~800MB
# unzipped. If that matters more than the last degree of precision, see the note at the
# bottom of desktop/README.md about the ONNX build.

$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$py = Join-Path $root '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) { throw "No .venv at $root — see desktop/README.md for setup." }
foreach ($need in 'yolo11x-pose.pt', 'web\app.html', 'files\analyze_bikefit.py') {
    if (-not (Test-Path (Join-Path $root $need))) { throw "Missing $need — build from the repo root." }
}

& $py -m pip show pyinstaller *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Installing PyInstaller...'
    & $py -m pip install pyinstaller
}

Push-Location $root
try {
    & $py -m PyInstaller --noconfirm --clean desktop\bikefit.spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed (exit $LASTEXITCODE)" }

    $out = Join-Path $root 'dist\BikeFitAnalyzer'
    $mb = [math]::Round(((Get-ChildItem $out -Recurse -File | Measure-Object Length -Sum).Sum / 1MB), 0)
    Write-Host ""
    Write-Host "Built: $out  ($mb MB)"

    $zip = Join-Path $root 'dist\BikeFitAnalyzer-windows.zip'
    if (Test-Path $zip) { Remove-Item $zip }
    Compress-Archive -Path $out -DestinationPath $zip
    $zmb = [math]::Round(((Get-Item $zip).Length / 1MB), 0)
    Write-Host "Zipped: $zip  ($zmb MB)"
    Write-Host ""
    Write-Host "Too big for git and for Vercel — attach the zip to a GitHub Release."
} finally { Pop-Location }

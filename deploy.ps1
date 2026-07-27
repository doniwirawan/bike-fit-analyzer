# Deploys the site to Vercel production, then checks the live URLs.
#
# Always run this instead of calling `vercel` by hand. It resolves web/ relative
# to its own location, so it cannot deploy the repo root by mistake — that is
# what happened on 2026-07-22, and it left https://bikefit.doniwirawan.xyz/
# serving a 404 for five days (everything ended up nested under /web/).
#
#   pwsh -File deploy.ps1              # deploy, then verify
#   pwsh -File deploy.ps1 -VerifyOnly  # just check the live site is up

param([switch]$VerifyOnly)

$ErrorActionPreference = 'Stop'

$web  = Join-Path $PSScriptRoot 'web'
$site = 'https://bikefit.doniwirawan.xyz'

foreach ($f in 'index.html', 'app.html', 'vercel.json') {
    if (-not (Test-Path (Join-Path $web $f))) {
        throw "$f is missing from $web — refusing to deploy the wrong directory."
    }
}

if (-not $VerifyOnly) {
    Push-Location $web
    try { vercel deploy --prod --yes } finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { throw "vercel deploy failed (exit $LASTEXITCODE)" }
}

$broken = @()
foreach ($path in '/', '/app', '/privacy', '/terms', '/og.png') {
    $code = (Invoke-WebRequest -Uri "$site$path" -Method Head -SkipHttpErrorCheck).StatusCode
    Write-Host ("  {0}  {1}" -f $code, $path)
    if ($code -ne 200) { $broken += $path }
}

if ($broken) { throw "live site is broken at: $($broken -join ', ')" }
Write-Host "OK - $site is live"

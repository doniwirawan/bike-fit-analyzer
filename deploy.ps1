# Deploys the site to Vercel production, then checks the live URLs.
#
# Pushing to main also deploys, because the GitHub repo is connected to the
# Vercel project. Both paths rely on the project's **Root Directory = web**
# setting to pick the site out of this repo, so deploys run from the repo root,
# not from web/. That setting was unset until 2026-07-27, which meant every push
# published the repo root and served a 404 at / — it went unnoticed for five days.
#
#   pwsh -File deploy.ps1              # deploy, then verify
#   pwsh -File deploy.ps1 -VerifyOnly  # just check the live site is up

param([switch]$VerifyOnly)

$ErrorActionPreference = 'Stop'

$web  = Join-Path $PSScriptRoot 'web'
$site = 'https://bikefit.doniwirawan.xyz'

foreach ($f in 'index.html', 'app.html', 'vercel.json', 'sitemap.xml', 'blog/index.html') {
    if (-not (Test-Path (Join-Path $web $f))) {
        throw "$f is missing from $web — is this the right repo?"
    }
}

if (-not $VerifyOnly) {
    Push-Location $PSScriptRoot
    try { vercel deploy --prod --yes } finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { throw "vercel deploy failed (exit $LASTEXITCODE)" }
}

$broken = @()
# One blog post is enough of a canary: if web/blog/ fails to publish it fails as a
# whole directory, so listing every post here would only be something to forget to
# update. /sitemap.xml and /robots.txt are checked because nothing else would notice
# them 404ing — no visitor ever opens them.
foreach ($path in '/', '/app', '/blog', '/blog/what-to-adjust-first',
                  '/privacy', '/terms', '/og.png', '/sitemap.xml', '/robots.txt') {
    $code = (Invoke-WebRequest -Uri "$site$path" -Method Head -SkipHttpErrorCheck).StatusCode
    Write-Host ("  {0}  {1}" -f $code, $path)
    if ($code -ne 200) { $broken += $path }
}

if ($broken) { throw "live site is broken at: $($broken -join ', ')" }
Write-Host "OK - $site is live"

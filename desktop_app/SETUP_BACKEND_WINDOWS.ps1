$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$vendor = Join-Path $root 'vendor'
$target = Join-Path $vendor 'EM-solver'
# Prefer the version validated by the backend team. Python 3.13 fallback is available
# for machines where the desktop app already works but Python 3.12 is absent.
# Probe Python without allowing a missing 3.12 launcher to terminate the script.
# PowerShell 5.1 can treat native stderr as an exception under Stop.
$version = $null
foreach ($candidate in @('3.12', '3.13')) {
  try {
    $probe = & py ('-' + $candidate) -c 'import sys; print(sys.version)' 2>&1
    if ($LASTEXITCODE -eq 0) {
      $version = $candidate
      Write-Host "Valgt Python $version" -ForegroundColor Cyan
      break
    }
  } catch {
    # Normal when a candidate version is not installed. Try the next one.
  }
}
if (-not $version) {
  throw 'Kunne ikke finde Python 3.12 eller 3.13 via py launcher. Proev: py -0p'
}
if ($version -eq '3.13') {
  Write-Warning 'Backend er testet med Python 3.12. Vi proever Python 3.13.'
}
$environmentName = if ($version -eq '3.12') {'backend312'} else {'backend313'}
$pythonEnv = Join-Path $env:LOCALAPPDATA ('EM1\' + $environmentName)
$py = Join-Path $pythonEnv 'Scripts\python.exe'
$branch = 'desktop-integration-2026-11-05'
$repo = 'pdamkier-del/EM-solver'
Write-Host 'EM1: Installerer en separat, versionsfast backend...' -ForegroundColor Cyan
if (-not (Test-Path (Join-Path $target 'em1_solver\backend_client.py'))) {
  New-Item -ItemType Directory -Path $vendor -Force | Out-Null
  $temp = Join-Path $env:TEMP ('em1-backend-' + [guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Path $temp | Out-Null
  try {
    $ref = Invoke-RestMethod -Headers @{ 'User-Agent'='EM1Desktop' } -Uri "https://api.github.com/repos/$repo/branches/$branch"
    $commit = $ref.commit.sha
    if ($commit -notmatch '^[0-9a-f]{40}$') { throw 'Ugyldigt GitHub commit' }
    $url = "https://github.com/$repo/archive/$commit.zip"
    $zip = Join-Path $temp 'backend.zip'
    Write-Host "Downloader integrationscommit $commit ..."
    Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    Expand-Archive -Path $zip -DestinationPath $temp -Force
    $found = Get-ChildItem -Path $temp -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'em1_solver\backend_client.py') } | Select-Object -First 1
    if (-not $found) { throw 'GitHub-arkivet mangler backend_client.py' }
    Move-Item -Path $found.FullName -Destination $target
    Set-Content -Path (Join-Path $target 'EM1_DESKTOP_PINNED_COMMIT.txt') -Value $commit -Encoding ascii
  } finally { Remove-Item -Recurse -Force $temp -ErrorAction SilentlyContinue }
} else { Write-Host 'Eksisterende backendversion beholdes (opdateres ikke automatisk).' }
& py ('-' + $version) --version
if (-not (Test-Path $py)) {
  New-Item -ItemType Directory -Path (Split-Path $pythonEnv) -Force | Out-Null
  & py ('-' + $version) -m venv $pythonEnv
  if ($LASTEXITCODE -ne 0) { throw 'Kunne ikke oprette Python 3.12-miljoe' }
}
& $py -m pip install --disable-pip-version-check -r (Join-Path $target 'requirements-backend-lock.txt')
if ($LASTEXITCODE -ne 0) { throw 'Installation af backend-afhaengigheder fejlede' }
Push-Location $target
try {
  & $py -c "from em1_solver.backend_client import run_text; print('Backend import OK')"
  if ($LASTEXITCODE -ne 0) { throw 'Backend kan ikke importeres' }
} finally { Pop-Location }
Write-Host 'Backend er installeret og klar. Start nu EM1 Solver med START_WINDOWS.bat.' -ForegroundColor Green

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host 'Python 3.13: bruger den samlede lokale appinstallation; ingen separat backend downloades.'
& (Join-Path $root 'INSTALL_WINDOWS.bat')
if ($LASTEXITCODE -ne 0) { throw 'Installation fejlede; se WINDOWS_INTEGRATED.md.' }

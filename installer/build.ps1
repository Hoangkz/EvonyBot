<#
build.ps1 — build the EvonyBot installer (replaces the PyInstaller build).

Stages everything the installer ships into build\app:
  python\                  Python embeddable runtime + Lib\site-packages
  main.py, database.py, version.py, updater.py, bot\, ui\, Images\
  Tesseract-OCR\           only if a Tesseract-OCR folder exists in the project root
then compiles installer\EvonyBot.iss with Inno Setup into dist\EvonyBot-Setup-<version>.exe.

The installer installs per-user (no admin) into %LOCALAPPDATA%\EvonyBot.

Requirements: the project venv (Python 3.12, 64-bit) and Inno Setup 6
(https://jrsoftware.org/isdl.php).

The version comes from version.py (__version__) — bump it before building.

Usage:  powershell -ExecutionPolicy Bypass -File installer\build.ps1
        (from Git Bash: installer/build.ps1)
#>

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Version = (Select-String -Path (Join-Path $Root "version.py") -Pattern '__version__\s*=\s*"([^"]+)"').Matches[0].Groups[1].Value
if (-not $Version) { throw "__version__ not found in version.py" }
Write-Host "Building EvonyBot $Version"
$PyVersion = "3.12.10"   # must match the venv's major.minor so the wheels fit
$Build = Join-Path $Root "build"
$App = Join-Path $Build "app"
$PyDir = Join-Path $App "python"
$SitePackages = Join-Path $PyDir "Lib\site-packages"
$EmbedZip = Join-Path $Build "python-$PyVersion-embed-amd64.zip"
$HostPy = Join-Path $Root "venv\Scripts\python.exe"

# ---- Inno Setup compiler --------------------------------------------
$Iscc = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Iscc) {
    $cmd = Get-Command iscc -ErrorAction SilentlyContinue
    if ($cmd) { $Iscc = $cmd.Source }
}
if (-not $Iscc) { throw "Inno Setup 6 (ISCC.exe) not found. Install it from https://jrsoftware.org/isdl.php" }

# ---- host Python (used only to pip-install the wheels) ---------------
if (-not (Test-Path $HostPy)) { throw "venv not found: $HostPy" }
$hostVer = (& $HostPy -c "import sys; print('%d.%d' % sys.version_info[:2])").Trim()
$embedVer = ($PyVersion -split '\.')[0..1] -join '.'
if ($hostVer -ne $embedVer) { throw "venv is Python $hostVer but the embedded runtime is $embedVer" }

# ---- fresh staging folder --------------------------------------------
if (Test-Path $App) { Remove-Item $App -Recurse -Force }
New-Item -ItemType Directory -Force $PyDir | Out-Null

# ---- Python embeddable runtime ---------------------------------------
if (-not (Test-Path $EmbedZip)) {
    Write-Host "Downloading Python $PyVersion embeddable..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest "https://www.python.org/ftp/python/$PyVersion/python-$PyVersion-embed-amd64.zip" -OutFile $EmbedZip
}
Expand-Archive $EmbedZip -DestinationPath $PyDir -Force

# The ._pth file fixes sys.path for the embedded runtime: add
# site-packages and the app folder (parent of python\) so main.py's
# imports of bot/ui/database resolve.
$pth = Get-ChildItem $PyDir -Filter "python*._pth" | Select-Object -First 1
Set-Content $pth.FullName -Encoding ascii -Value @(
    "$($pth.BaseName).zip",
    ".",
    "Lib\site-packages",
    "..",
    "import site"
)

# ---- libraries -------------------------------------------------------
Write-Host "Installing requirements into the embedded runtime..."
& $HostPy -m pip install --no-warn-script-location --target $SitePackages -r (Join-Path $Root "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

# ---- app source + images ---------------------------------------------
foreach ($f in @("main.py", "database.py", "version.py", "updater.py")) {
    Copy-Item (Join-Path $Root $f) $App
}
foreach ($d in @("bot", "ui", "Images", "Tesseract-OCR")) {
    $src = Join-Path $Root $d
    if (Test-Path $src) { Copy-Item $src (Join-Path $App $d) -Recurse }
}
Get-ChildItem $App -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# ---- installer -------------------------------------------------------
Write-Host "Compiling installer..."
& $Iscc "/DAppVersion=$Version" (Join-Path $PSScriptRoot "EvonyBot.iss")
if ($LASTEXITCODE -ne 0) { throw "ISCC failed" }
Write-Host "Done: $(Join-Path $Root "dist\EvonyBot-Setup-$Version.exe")"

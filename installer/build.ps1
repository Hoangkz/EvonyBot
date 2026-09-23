<#
build.ps1 — build the EvonyBot installer (replaces the PyInstaller build).

Stages everything the installer ships into build\app:
  python\                  Python embeddable runtime + Lib\site-packages
  main.cp312-win_amd64.pyd all app code (main, database, version, updater,
                           bot\, ui\) compiled by Nuitka into this one file
  EvonyBot.pyw             launcher stub (from main import main)
  ui\assets\, Images\
  Tesseract-OCR\           only if a Tesseract-OCR folder exists in the project root
then compiles installer\EvonyBot.iss with Inno Setup into dist\EvonyBot-Setup-<version>.exe.

The installer installs per-user (no admin) into %LOCALAPPDATA%\EvonyBot.

Requirements: the project venv (Python 3.12, 64-bit) with nuitka installed,
a C compiler - the MSVC C++ Build Tools
(https://visualstudio.microsoft.com/visual-cpp-build-tools/, workload
"Desktop development with C++"); without it Nuitka downloads MinGW itself -
and Inno Setup 6 (https://jrsoftware.org/isdl.php).

The version comes from version.py (__version__) — bump it before building.

Usage:  powershell -ExecutionPolicy Bypass -File installer\build.ps1
        (from Git Bash: installer/build.ps1)
#>

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Version = (Select-String -Path (Join-Path $Root "version.py") -Pattern '__version__\s*=\s*"([^"]+)"').Matches[0].Groups[1].Value
if (-not $Version) { throw "__version__ not found in version.py" }
Write-Host "Building EvonyBot $Version"
$PyVersion = "3.12.10"   # must match the venv's major.minor so its packages fit
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

# ---- venv (its site-packages is shipped as the libraries) ------------
if (-not (Test-Path $HostPy)) { throw "venv not found: $HostPy" }
$hostVer = (& $HostPy -c "import sys; print('%d.%d' % sys.version_info[:2])").Trim()
$embedVer = ($PyVersion -split '\.')[0..1] -join '.'
if ($hostVer -ne $embedVer) { throw "venv is Python $hostVer but the embedded runtime is $embedVer" }
& $HostPy -c "import nuitka"
if ($LASTEXITCODE -ne 0) { throw "Nuitka missing in the venv: venv\Scripts\python -m pip install nuitka" }

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
# Copied straight from the venv (same Python major.minor, checked above),
# so whatever is installed there is what ships - run
# `pip install -r requirements.txt` in the venv first. Build-only tools
# (pip, setuptools, PyInstaller, Nuitka and their deps) are left out.
Write-Host "Copying libraries from the venv..."
$VenvSite = Join-Path $Root "venv\Lib\site-packages"
$excludeDirs = @(
    "__pycache__", "pip", "pip-*", "setuptools", "setuptools-*", "_distutils_hack", "pkg_resources",
    "PyInstaller", "pyinstaller-*", "_pyinstaller_hooks_contrib", "pyinstaller_hooks_contrib-*",
    "altgraph", "altgraph-*", "pefile-*", "ordlookup", "win32ctypes", "pywin32_ctypes-*",
    "nuitka", "Nuitka-*", "ordered_set", "ordered_set-*", "zstandard", "zstandard-*",
    "Cython", "cython-*", "pyximport"
)
$excludeFiles = @("distutils-precedence.pth", "pefile.py", "peutils.py", "cython.py")
robocopy $VenvSite $SitePackages /E /MT:16 /NFL /NDL /NJH /NJS /NP /XD $excludeDirs /XF $excludeFiles | Out-Null
if ($LASTEXITCODE -ge 8) { throw "copying site-packages failed (robocopy exit $LASTEXITCODE)" }

# ---- app code -> one .pyd (no readable .py shipped) ------------------
# Nuitka module mode compiles main.py plus every included module/package
# into a single extension; third-party libraries are not followed and
# load from python\Lib\site-packages as usual. Compiled modules keep
# their __file__ (e.g. <app>\bot\context.py), so paths built from it
# (Images\, ui\assets\) still resolve.
Write-Host "Compiling app code with Nuitka..."
$NuitkaOut = Join-Path $Build "nuitka"
if (Test-Path $NuitkaOut) { Remove-Item $NuitkaOut -Recurse -Force }
Push-Location $Root
try {
    & $HostPy -m nuitka --module main.py `
        --include-module=database --include-module=updater --include-module=version `
        --include-package=bot --include-package=ui `
        --output-dir=$NuitkaOut --remove-output --no-pyi-file --assume-yes-for-downloads
    if ($LASTEXITCODE -ne 0) { throw "Nuitka compile failed" }
} finally {
    Pop-Location
}
Copy-Item (Join-Path $NuitkaOut "main*.pyd") $App

# ---- data files ------------------------------------------------------
New-Item -ItemType Directory -Force (Join-Path $App "ui") | Out-Null
Copy-Item (Join-Path $Root "ui\assets") (Join-Path $App "ui\assets") -Recurse
foreach ($d in @("Images", "Tesseract-OCR")) {
    $src = Join-Path $Root $d
    if (Test-Path $src) { Copy-Item $src (Join-Path $App $d) -Recurse }
}

# A .pyd can't be run as a script, so the shortcut starts this stub.
Set-Content (Join-Path $App "EvonyBot.pyw") -Encoding ascii -Value @(
    "from main import main",
    "main()"
)

# ---- installer -------------------------------------------------------
Write-Host "Compiling installer..."
& $Iscc "/DAppVersion=$Version" (Join-Path $PSScriptRoot "EvonyBot.iss")
if ($LASTEXITCODE -ne 0) { throw "ISCC failed" }
Write-Host "Done: $(Join-Path $Root "dist\EvonyBot-Setup-$Version.exe")"

# Английский тренажёр: сборка одного самодостаточного CTEnglishTutor.exe.
# Windows build script — produces a single self-contained CTEnglishTutor.exe
# Usage:  powershell -ExecutionPolicy Bypass -File english\windows\build.ps1
#         powershell -ExecutionPolicy Bypass -File english\windows\build.ps1 -Console -Arch arm64
param(
    [string]$Out = "dist",
    [string]$Arch = "amd64",
    [switch]$Console
)
$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path   # english/windows
$root = Join-Path $here ".."                              # english
$repo = Join-Path $here "../.."                           # корень репозитория

Write-Host "==> building the English content bank and syncing it into the app"
if (Get-Command python -ErrorAction SilentlyContinue) {
    $env:CT_SUBJECT = "english"
    python (Join-Path $root "tools/build_content.py")
    python (Join-Path $repo "tools/sync_assets.py")
} else {
    Write-Warning "python not found: using the assets already committed in english/windows/web"
}

$env:CGO_ENABLED = "0"
$env:GOOS = "windows"
$env:GOARCH = $Arch

$stamp = Get-Date -Format "yyyyMMddHHmm"
$ldflags = "-s -w -X main.buildStamp=$stamp"
if (-not $Console) { $ldflags = "$ldflags -H=windowsgui" }

$outDir = Join-Path $root $Out
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$exe = Join-Path $outDir "CTEnglishTutor-$Arch.exe"

Push-Location $here
try {
    Write-Host "==> go build (windows/$Arch)"
    go build -trimpath -ldflags "$ldflags" -o $exe .
    Write-Host "==> built $exe"
} finally {
    Pop-Location
}

# Windows build script — produces a single self-contained CTRussianTutor.exe
# Usage:  powershell -ExecutionPolicy Bypass -File windows\build.ps1
#         powershell -ExecutionPolicy Bypass -File windows\build.ps1 -Console -Arch arm64
param(
    [string]$Out = "dist",
    [string]$Arch = "amd64",
    [switch]$Console
)
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Join-Path $root ".."

Write-Host "==> syncing shared web assets and content bank"
if (Get-Command python -ErrorAction SilentlyContinue) {
    python (Join-Path $root "tools/build_content.py")
    python (Join-Path $root "tools/sync_assets.py")
} else {
    Write-Warning "python not found: using the assets already committed in windows/web"
}

$env:CGO_ENABLED = "0"
$env:GOOS = "windows"
$env:GOARCH = $Arch

$stamp = Get-Date -Format "yyyyMMddHHmm"
$ldflags = "-s -w -X main.buildStamp=$stamp"
if (-not $Console) { $ldflags = "$ldflags -H=windowsgui" }

$outDir = Join-Path $root $Out
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$exe = Join-Path $outDir "CTRussianTutor-$Arch.exe"

Push-Location (Join-Path $root "windows")
try {
    Write-Host "==> go build (windows/$Arch)"
    go build -trimpath -ldflags "$ldflags" -o $exe .
    Write-Host "==> built $exe"
} finally {
    Pop-Location
}

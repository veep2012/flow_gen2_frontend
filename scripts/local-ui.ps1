$ErrorActionPreference = "Stop"

param(
    [string]$PidFile = ".local\vite.pid",
    [string]$ProjectPath = "ui",
    [string]$UiPort = "5558"
)

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$uiDir = Join-Path $root $ProjectPath

if (-not (Test-Path $uiDir)) {
    Write-Error "UI directory not found at $uiDir"
}

if (-not $env:VITE_API_BASE_URL) {
    $env:VITE_API_BASE_URL = "http://localhost:5556"
}

$proc = Start-Process -NoNewWindow -PassThru -FilePath "npm" -ArgumentList "run","dev","--","--host","0.0.0.0","--port",$UiPort -WorkingDirectory $uiDir
if ($PidFile) {
    $pidDir = Split-Path -Parent $PidFile
    if ($pidDir -and -not (Test-Path $pidDir)) {
        New-Item -ItemType Directory -Path $pidDir | Out-Null
    }
    Set-Content -Path $PidFile -Value $proc.Id
}

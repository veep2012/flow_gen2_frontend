$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$uiDir = Join-Path $root "ui"

if (-not (Test-Path $uiDir)) {
    Write-Error "UI directory not found at $uiDir"
}

if (-not $env:VITE_API_BASE_URL) {
    $env:VITE_API_BASE_URL = "http://localhost:5556/api/v1"
}

Start-Process -NoNewWindow -FilePath "npm" -ArgumentList "run","dev" -WorkingDirectory $uiDir

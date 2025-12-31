$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")

$presetDatabaseUrl = $env:DATABASE_URL
$presetApiHost = $env:API_HOST
$presetApiPort = $env:API_PORT
$presetMinioEndpoint = $env:MINIO_ENDPOINT
$presetMinioBucket = $env:MINIO_BUCKET
$presetMinioRootUser = $env:MINIO_ROOT_USER
$presetMinioRootPassword = $env:MINIO_ROOT_PASSWORD
$presetMinioSecure = $env:MINIO_SECURE

# Load .env into process env
$envPath = Join-Path $root ".env"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match '^\s*([^#=\s]+)\s*=\s*(.*)\s*$') {
            $name = $matches[1]
            $val = $matches[2]
            Set-Item -Path "Env:$name" -Value $val
        }
    }
}

if ($presetDatabaseUrl) {
    $env:DATABASE_URL = $presetDatabaseUrl
}
if ($presetApiHost) {
    $env:API_HOST = $presetApiHost
}
if ($presetApiPort) {
    $env:API_PORT = $presetApiPort
}
if ($presetMinioEndpoint) {
    $env:MINIO_ENDPOINT = $presetMinioEndpoint
}
if ($presetMinioBucket) {
    $env:MINIO_BUCKET = $presetMinioBucket
}
if ($presetMinioRootUser) {
    $env:MINIO_ROOT_USER = $presetMinioRootUser
}
if ($presetMinioRootPassword) {
    $env:MINIO_ROOT_PASSWORD = $presetMinioRootPassword
}
if ($presetMinioSecure) {
    $env:MINIO_SECURE = $presetMinioSecure
}

$minioEndpoint = $env:MINIO_ENDPOINT
if ($minioEndpoint) {
    $env:MINIO_ENDPOINT = $minioEndpoint.Replace("host.containers.internal", "localhost")
}

$venvPy = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    Write-Error ".venv not found; run 'make local-venv' first."
}

$env:PYTHONPATH = "api"
Start-Process -NoNewWindow -FilePath $venvPy -ArgumentList "-m","uvicorn","api.main:app","--host","0.0.0.0","--port","5556","--reload"

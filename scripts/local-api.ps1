$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")

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

$venvPy = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    Write-Error ".venv not found; run 'make local-venv' first."
}

$env:PYTHONPATH = "api"
Start-Process -NoNewWindow -FilePath $venvPy -ArgumentList "-m","uvicorn","api.main:app","--host","0.0.0.0","--port","5556","--reload"

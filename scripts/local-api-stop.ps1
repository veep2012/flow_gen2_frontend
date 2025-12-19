$ErrorActionPreference = "Stop"

param(
    [string]$PidFile = ".local\uvicorn.pid"
)

if (Test-Path $PidFile) {
    $pid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($pid) {
        try { Stop-Process -Id $pid -ErrorAction SilentlyContinue } catch {}
    }
    Remove-Item -Path $PidFile -ErrorAction SilentlyContinue
} else {
    Get-Process -Name python -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -like "*\venv\Scripts\python.exe" -and $_.StartInfo.Arguments -like "*uvicorn*api.main:app*" } |
        ForEach-Object { try { $_.Kill() } catch {} }
}

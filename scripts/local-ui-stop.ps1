$ErrorActionPreference = "Stop"

param(
    [string]$PidFile = ".local\vite.pid"
)

if (Test-Path $PidFile) {
    $pid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($pid) {
        try { Stop-Process -Id $pid -ErrorAction SilentlyContinue } catch {}
    }
    Remove-Item -Path $PidFile -ErrorAction SilentlyContinue
} else {
    Get-Process -Name node -ErrorAction SilentlyContinue |
        Where-Object { $_.StartInfo.Arguments -like "*vite*5558*" -or $_.Path -like "*\node_modules\vite*" } |
        ForEach-Object { try { $_.Kill() } catch {} }
}

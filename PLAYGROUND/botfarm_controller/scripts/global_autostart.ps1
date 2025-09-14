param([string]$Workspace = "")

$ErrorActionPreference = "Stop"
$bot = "C:\Code\Bots\botfarm_controller"
$py  = "C:\Users\Norbi\Ultimate_Norbi_Assistant\.venv\Scripts\python.exe"
$port = 8000

function Test-Port($p){ try { (Test-NetConnection 127.0.0.1 -Port $p -InformationLevel Quiet) } catch { $false } }

# 1) API (einmalig)
if (-not (Test-Port $port)) {
  Start-Process -FilePath $py `
    -ArgumentList @("-m","uvicorn","main:app","--host","127.0.0.1","--port",$port,"--reload") `
    -WorkingDirectory $bot -WindowStyle Minimized
  Write-Host "[autostart] API started on :$port"
} else {
  Write-Host "[autostart] API already running on :$port"
}

# 2) Self-Work Loop (optional, wenn nicht eingefroren)
$freeze = Join-Path $bot "OPS\flags\freeze.txt"
if (-not (Test-Path $freeze)) {
  Start-Process -FilePath "powershell" `
    -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass",
      "-File",(Join-Path $bot "scripts\self_work_loop.ps1"),
      "-IntervalSec","120") `
    -WorkingDirectory $bot -WindowStyle Minimized
  Write-Host "[autostart] Self-Work loop started."
} else {
  Write-Host "[autostart] Self-Work frozen (freeze.txt present)."
}

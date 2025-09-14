# === Schritt 6: Guardrails & Policy-Sync (Preview-first) – Wrapper (Python-Worker) ===
$ErrorActionPreference = 'Stop'
$base = "C:\Users\Norbi\Ultimate_Norbi_Assistant"
$proj = Join-Path $base "PLAYGROUND\botfarm_controller"
$logs = Join-Path $base "OPS\logs"
New-Item -ItemType Directory -Force $logs | Out-Null

param(
  [switch]$Apply,
  [ValidateSet("yaml","json")][string]$Source = "yaml"
)

$jsonPath = Join-Path $proj "policy_lock.json"
$yamlPath = Join-Path $base "POLICIES\codegen_policy.yaml"
$py = Join-Path $base ".venv\Scripts\python.exe"
$worker = Join-Path $proj "OPS\scripts\policy_sync_worker.py"

if (-not (Test-Path $jsonPath)) { throw "Fehlt: $jsonPath" }
if (-not (Test-Path $yamlPath)) { throw "Fehlt: $yamlPath" }

# Build simple invocation to Python worker
$src = if ($Source) { $Source } else { "yaml" }
$applyFlag = if ($Apply) { "1" } else { "0" }

$log = Join-Path $logs "policy_sync.log"
& $py $worker $jsonPath $yamlPath $applyFlag $src | Tee-Object -FilePath $log -Append

Write-Host "[DONE] policy_sync complete. Log: $log"
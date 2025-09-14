param(
  [string]$SpecPath = "$(Join-Path $PSScriptRoot '..\prompts\example_spec.md')",
  [switch]$Dry
)
$ErrorActionPreference = 'Stop'
$base = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$logs = Join-Path $base "OPS\logs"
New-Item -ItemType Directory -Force $logs | Out-Null
$logFile = Join-Path $logs "codeops_runs.log"

function Run-Step($name, [scriptblock]$sb) {
  $t = Measure-Command { & $sb }
  $msg = "[{0}] {1}={2:N1}s" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $name, $t.TotalSeconds
  $msg | Tee-Object -FilePath $logFile -Append
  Write-Host $msg
}

Run-Step "env_check" {
  "$($PSVersionTable.PSVersion) • $((Get-Command python,py -ErrorAction SilentlyContinue | Select-Object -First 1 -Expand Source))" | Out-Null
}

# Optionaler Codegen-Preview, wenn Generator existiert
$cg = Join-Path $base "OPS\scripts\run_codegen.ps1"
if (Test-Path $cg) {
  Run-Step "codegen_preview" {
    powershell -NoProfile -ExecutionPolicy Bypass -File $cg -SpecPath $SpecPath -Dry
  }
} else {
  Run-Step "noop" { Start-Sleep -Milliseconds 50 }
}

# Digest aktualisieren
$digest = Join-Path $logs "codeops_digest.txt"
"=== CODEOPS DIGEST $(Get-Date) ===" | Out-File -Encoding UTF8 $digest
"Letzte Runs:" | Add-Content -Encoding UTF8 $digest
Get-Content $logFile -Tail 10 | Add-Content -Encoding UTF8 $digest

# scripts/kpi_digest.ps1  (v2: schreibt nach <proj>\OPS\reports)
$ErrorActionPreference='Stop'

# Projekt-Root = Ordner über "scripts"
$projRoot = (Get-Item $PSScriptRoot).Parent.FullName
$log     = Join-Path $projRoot 'OPS\logs\codegen_runs.log'
$repDir  = Join-Path $projRoot 'OPS\reports'
New-Item -ItemType Directory -Force $repDir | Out-Null
$out     = Join-Path $repDir 'codegen_kpi.txt'

if (-not (Test-Path $log)) {
  "no data (log fehlt)" | Out-File $out -Encoding UTF8
  Write-Host $out
  exit 0
}

$lines = Get-Content $log -ErrorAction SilentlyContinue
if (-not $lines -or $lines.Count -eq 0) {
  "no data" | Out-File $out -Encoding UTF8
  Write-Host $out
  exit 0
}

$tot       = $lines.Count
$approved  = ($lines | Select-String 'status=APPROVED').Count
$preview   = ($lines | Select-String 'status=PREVIEW_ONLY').Count
$errors    = ($lines | Select-String 'BLOCKED_RED|status=ERROR').Count
$changes   = $lines | ForEach-Object {
  if ($_ -match 'adds=(\d+)\s+rems=(\d+)') { [int]$matches[1]+[int]$matches[2] }
}
$avgChange = if ($changes) { [math]::Round((($changes | Measure-Object -Average).Average),1) } else { 0 }

@"
Runs: $tot
Approved: $approved
Preview-only: $preview
Errors/Reds: $errors
Avg lines changed: $avgChange

Last 5:
$(($lines | Select-Object -Last 5) -join "`n")
"@ | Out-File $out -Encoding UTF8

Write-Host $out

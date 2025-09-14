$log = Join-Path $PSScriptRoot '..\logs\codegen_runs.log' | Resolve-Path
$out = Join-Path $PSScriptRoot '..\reports\codegen_kpi.txt'
New-Item -ItemType Directory -Force (Split-Path $out) | Out-Null

$lines = Get-Content $log -ErrorAction SilentlyContinue
if (-not $lines -or $lines.Count -eq 0) {
  "no data" | Out-File $out -Encoding UTF8
  exit 0
}
$tot  = $lines.Count
$green= ($lines | Select-String "status=APPROVED").Count
$err  = ($lines | Select-String "status=ERROR|BLOCKED_RED").Count
$chg  = @()
foreach ($ln in $lines) {
  if ($ln -match "adds=(\d+)\s+rems=(\d+)") { $chg += [int]$matches[1]+[int]$matches[2] }
}
$avg = if ($chg.Count) { [math]::Round((($chg | Measure-Object -Average).Average),1) } else { 0 }
"Runs: $tot`nGreen: $green`nErrors/Reds: $err`nAvg lines changed: $avg" | Out-File $out -Encoding UTF8

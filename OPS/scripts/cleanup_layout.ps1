param([switch]$Approve)

$ErrorActionPreference = "Stop"
$base    = "C:\Users\Norbi\Ultimate_Norbi_Assistant"
$ts      = Get-Date -Format "yyyyMMdd_HHmmss"
$archive = Join-Path $base "ARCHIVE"
New-Item -ItemType Directory -Force $archive | Out-Null

$targets = @(
  @{ type="flatten"; nested=Join-Path $base "ultimate_assistant_scripts\ultimate_assistant_scripts"; parent=Join-Path $base "ultimate_assistant_scripts" },
  @{ type="flatten"; nested=Join-Path $base "ultimate_assistant_skeletons\ultimate_assistant_skeletons"; parent=Join-Path $base "ultimate_assistant_skeletons" },
  @{ type="archive"; path=Join-Path $base "pilot_agent_repo_updated" },
  @{ type="archive"; path=Join-Path $base "pilot_inputs_bundle" },
  @{ type="archive"; path=Join-Path $base "previews" },
  @{ type="archive"; path=Join-Path $base "RAW" }
)

# Plan erstellen (als Liste von Strings)
$plan = New-Object System.Collections.Generic.List[string]
foreach ($t in $targets) {
  if ($t.type -eq "flatten" -and (Test-Path $t.nested)) {
    $count = (Get-ChildItem -Force $t.nested | Measure-Object).Count
    $plan.Add(("FLATTEN: '{0}\*' -> '{1}\'  ({2} Einträge)" -f $t.nested, $t.parent, $count))
  } elseif ($t.type -eq "archive" -and (Test-Path $t.path)) {
    $size = (Get-ChildItem -Recurse -Force $t.path | Measure-Object Length -Sum).Sum
    $mb   = [math]::Round(($size/1MB),1)
    $plan.Add(("ARCHIVE: '{0}'  (~{1} MB) -> ARCHIVE\{2}_{3}.zip" -f $t.path, $mb, (Split-Path $t.path -Leaf), $ts))
  }
}

if (-not $Approve) {
  Write-Host "=== CLEANUP WHAT-IF ==="
  if ($plan.Count -gt 0) { $plan | ForEach-Object { Write-Host $_ } } else { Write-Host "(nichts zu tun)" }
  Write-Host "`n---`nOK? -> Rerun:"
  Write-Host "powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Approve"
  exit 0
}

# ===== APPLY (sicher, Originale bleiben bestehen) =====
# 1) Backup der Archive-Ziele
$to_backup = @()
foreach ($t in $targets) {
  if ($t.type -eq "archive" -and (Test-Path $t.path)) { $to_backup += $t.path }
}
if ($to_backup.Count -gt 0) {
  $snap = Join-Path $archive ("pre_cleanup_{0}.zip" -f $ts)
  Compress-Archive -Path $to_backup -DestinationPath $snap -Force
  Write-Host "[BACKUP] $snap"
}

# 2) Flatten
foreach ($t in $targets) {
  if ($t.type -eq "flatten" -and (Test-Path $t.nested)) {
    New-Item -ItemType Directory -Force $t.parent | Out-Null
    Get-ChildItem -Force $t.nested | ForEach-Object {
      Move-Item -Force -Path $_.FullName -Destination $t.parent
    }
    Remove-Item -Force -Recurse $t.nested
    Write-Host "[FLATTEN] $($t.nested) -> $($t.parent)"
  }
}

# 3) Archive-ZIPs erzeugen (Originale bleiben)
foreach ($t in $targets) {
  if ($t.type -eq "archive" -and (Test-Path $t.path)) {
    $zip = Join-Path $archive ("{0}_{1}.zip" -f (Split-Path $t.path -Leaf), $ts)
    Compress-Archive -Path (Join-Path $t.path "*") -DestinationPath $zip -Force
    Write-Host "[ARCHIVE] $($t.path) -> $zip"
  }
}
Write-Host "`nFertig. Originale NICHT gelöscht. ZIPs in ARCHIVE\."

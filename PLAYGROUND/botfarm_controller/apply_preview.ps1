param(
  [Parameter(Mandatory=$true)][string]$PreviewPath,
  [string]$Target = "generated_module.py",
  [switch]$Approve
)

$ErrorActionPreference = 'Stop'
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path

# Auflösen der Pfade
$preview = Resolve-Path $PreviewPath
if (-not $preview) { throw "preview_path nicht gefunden: $PreviewPath" }

$targetPath = $Target
if (-not [System.IO.Path]::IsPathRooted($Target)) {
  $targetPath = Join-Path $ROOT $Target
}
$resTarget = Resolve-Path -LiteralPath $targetPath -ErrorAction SilentlyContinue
if ($null -ne $resTarget) {
  $targetPath = $resTarget
}

# Guard: nie auf main.py anwenden
if ([System.IO.Path]::GetFileName($targetPath) -ieq "main.py") {
  throw "Applying auf main.py ist blockiert. Nutze z.B. generated_module.py."
}

# Read contents
$old = if (Test-Path $targetPath) { Get-Content -Raw -LiteralPath $targetPath } else { "" }
$new = Get-Content -Raw -LiteralPath $preview

# Changes zählen (einfach über Compare-Object)
$oldLines = $old -split "`r`n|`n"
$newLines = $new -split "`r`n|`n"
$diff = Compare-Object -ReferenceObject $oldLines -DifferenceObject $newLines -IncludeEqual:$false
$adds = @($diff | Where-Object { $_.SideIndicator -eq '=>' }).Count
$rems = @($diff | Where-Object { $_.SideIndicator -eq '<=' }).Count

Write-Host "--- WHAT-IF ---"
Write-Host ("Target     : {0}" -f $targetPath)
Write-Host ("Preview    : {0}" -f $preview)
Write-Host ("Changes    : +{0} / -{1}" -f $adds, $rems)
Write-Host ""
Write-Host "--- HEAD(30) PREVIEW ---"
$head = $newLines | Select-Object -First 30
$head | ForEach-Object { Write-Host $_ }
Write-Host "---------------"
Write-Host ""

if (-not $Approve) {
  Write-Host "[INFO] Dry run only. To apply, rerun with -Approve and optional -Target."
  exit 0
}

# Backup & Write
$bakDir = Join-Path $ROOT "_backup"
New-Item -ItemType Directory -Force -Path $bakDir | Out-Null
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
if (Test-Path $targetPath) {
  $bakPath = Join-Path $bakDir ("{0}.{1}.bak" -f [IO.Path]::GetFileName($targetPath), $ts)
  $old | Set-Content -Encoding UTF8 -LiteralPath $bakPath
  Write-Host ("[Backup] -> {0}" -f $bakPath)
}

$dir = Split-Path -Parent $targetPath
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$new | Set-Content -Encoding UTF8 -LiteralPath $targetPath
Write-Host ("[WRITE] {0} -> {1}" -f $PreviewPath, $targetPath)
Write-Host "[OK] Applied."

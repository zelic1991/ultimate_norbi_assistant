param(
  [switch]$Apply,          # ohne -Apply: nur Bericht (safe)
  [string]$Root = $(Get-Location).Path
)

$ErrorActionPreference = "Stop"
Write-Host "Root: $Root"

# 1) Suchmuster
$needleHyphen = "norbi-assistant"
$needleSnake  = "norbi_assistant"
$replacementHyphen = "ultimate-norbi-assistant"
$replacementSnake  = "ultimate_norbi_assistant"

# 2) Audit: Ordner, Dateien mit Treffern
$folders = @()
$folders += Get-ChildItem -Path $Root -Recurse -Directory -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -in @($needleHyphen,$needleSnake) }

$filesWithHits = @()
$includes = @("*.json","*.yml","*.yaml","*.toml","*.py","*.md",".env",".env.example","package.json","pyproject.toml","setup.cfg","*.ps1")
Get-ChildItem -Path $Root -Recurse -File -Force -ErrorAction SilentlyContinue -Include $includes | ForEach-Object {
  $hit = Select-String -Path $_.FullName -SimpleMatch -Pattern @($needleHyphen,$needleSnake) -Quiet -ErrorAction SilentlyContinue
  if ($hit) { $filesWithHits += $_.FullName }
}

Write-Host "---- AUDIT ----"
Write-Host "Ordner, die entfernt werden können:" -ForegroundColor Cyan
$folders | ForEach-Object { "  - $($_.FullName)" }
Write-Host ""
Write-Host "Dateien mit Referenzen:" -ForegroundColor Cyan
$filesWithHits | Sort-Object | ForEach-Object { "  - $_" }
Write-Host "----------------"

if (-not $Apply) {
  Write-Host "`n[What-If] Nichts geändert. Starte mit:  pwsh -File scripts\migrate_norbi_to_ultimate.ps1 -Apply" -ForegroundColor Yellow
  exit 0
}

# 3) Entferne alte Ordnernamen-Varianten
foreach($d in $folders){
  try {
    Remove-Item -LiteralPath $d.FullName -Recurse -Force -ErrorAction Stop
    Write-Host "[DEL] $($d.FullName)"
  } catch {
    Write-Warning "[SKIP] $($d.FullName): $($_.Exception.Message)"
  }
}

# 4) .vscode/settings.json & mcp.json bereinigen
function Remove-McpServerKey($jsonPath, $keyName){
  if (-not (Test-Path $jsonPath)) { return }
  try {
    $obj = Get-Content -Raw $jsonPath | ConvertFrom-Json -Depth 100
  } catch {
    Write-Warning "[WARN] $jsonPath ist kein valides JSON – übersprungen."
    return
  }
  $dirty = $false
  if ($obj."mcp.servers" -and $obj."mcp.servers".$keyName) {
    $obj."mcp.servers".PsObject.Properties.Remove($keyName) | Out-Null
    $dirty = $true
    Write-Host "[MCP] Entfernt '$keyName' aus $jsonPath"
  }
  if ($dirty) {
    $obj | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 $jsonPath
  }
}
$settingsJson = Join-Path $Root ".vscode\settings.json"
$mcpJson      = Join-Path $Root "mcp.json"
Remove-McpServerKey $settingsJson $needleHyphen
Remove-McpServerKey $mcpJson      $needleHyphen

# 5) In Dateien Strings ersetzen
foreach($f in $filesWithHits | Sort-Object -Unique){
  try {
    $txt = Get-Content -Raw -LiteralPath $f -ErrorAction Stop
    $new = $txt -replace [regex]::Escape($needleHyphen), $replacementHyphen
    $new = $new -replace [regex]::Escape($needleSnake),  $replacementSnake
    if ($new -ne $txt) {
      Set-Content -LiteralPath $f -Encoding UTF8 -Value $new
      Write-Host "[REWRITE] $f"
    }
  } catch {
    Write-Warning "[SKIP] $f: $($_.Exception.Message)"
  }
}

# 6) venv: altes Package deinstallieren
$venvPip = Join-Path $Root ".venv\Scripts\pip.exe"
if (Test-Path $venvPip) {
  & $venvPip uninstall -y norbi-assistant 2>$null | Out-Null
  & $venvPip uninstall -y norbi_assistant  2>$null | Out-Null
  Write-Host "[PIP] Uninstall versucht: norbi-assistant / norbi_assistant"
}

# 7) Caches/Logs putzen (nur offensichtliche)
Get-ChildItem -Path $Root -Recurse -Directory -Force -ErrorAction SilentlyContinue -Filter "__pycache__" |
  ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue; Write-Host "[CLEAN] $($_.FullName)" }

# 8) Rest-Check
$left = Select-String -Path (Join-Path $Root "*") -Recurse -SimpleMatch -Pattern @($needleHyphen,$needleSnake) -ErrorAction SilentlyContinue
if ($left) {
  Write-Warning "Es gibt noch Treffer (prüfen):"
  $left | Select-Object -ExpandProperty Path -Unique | ForEach-Object { "  - $_" }
} else {
  Write-Host "[OK] Migration abgeschlossen. Keine verbleibenden Referenzen gefunden." -ForegroundColor Green
}

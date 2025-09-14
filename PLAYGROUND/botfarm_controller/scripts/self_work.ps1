param(
  [string]$Spec,
  [switch]$WhatIf,
  [switch]$ApproveLast,
  [switch]$ForceYellow
)
$ErrorActionPreference = "Stop"
$base = "http://127.0.0.1:8000"
$root = Split-Path -Parent $PSScriptRoot
$root = Split-Path -Parent $root
$drafts = Join-Path $root "OPS\drafts"
New-Item -ItemType Directory -Force $drafts | Out-Null

function New-DraftFromPreview($specText) {
  $body = @{
    spec_text = $specText
    target    = "generated_module.py"
    lang      = "py"
  } | ConvertTo-Json -Depth 6
  $prev = Invoke-RestMethod -Uri "$base/preview" -Method POST -ContentType 'application/json' -Body $body

  $code = Get-Content -Raw $prev.preview_path
  $ts = Get-Date -Format "yyyyMMdd_HHmmss"
  $draft = @{
    status       = "PREVIEW_ONLY"
    ts           = $ts
    model        = "gpt-5-mini"
    target       = $prev.target
    preview_path = $prev.preview_path
    adds         = $prev.adds
    rems         = $prev.rems
    rationale    = "self_work"
    risk_note    = "heuristic"
    patch        = @(@{
      path = "C:\Code\Bots\botfarm_controller\generated_module.py"
      text = $code
    })
  }
  $out = Join-Path $drafts ("draft_{0}.json" -f $ts)
  ($draft | ConvertTo-Json -Depth 20) | Set-Content -Encoding UTF8 $out
  return $out
}

function Apply-Draft($path, [switch]$OnlyWhatIf) {
  Write-Host ("Draft:   {0}" -f $path)
  $obj = Get-Content -Raw $path | ConvertFrom-Json
  Write-Host ("Preview: {0}" -f $obj.preview_path)
  Write-Host ("Target:  {0}" -f $obj.target)
  Write-Host ("Delta:   +{0} / -{1}" -f $obj.adds, $obj.rems)
  Write-Host ("Status:  {0}" -f $obj.status)
  $py = (Get-Command python).Source
  if ($OnlyWhatIf) {
    & $py "$root\apply_draft.py" --draft $path --whatif
  } else {
    $args = @("--draft",$path,"--approve")
    if ($ForceYellow) { $args += "--force-yellow" }
    & $py "$root\apply_draft.py" @args
  }
}

if ($ApproveLast) {
  $last = Get-ChildItem $drafts -Filter "draft_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $last) { throw "Kein Draft gefunden." }
  Apply-Draft -path $last.FullName -OnlyWhatIf:$WhatIf
  if (-not $WhatIf) {
    powershell -NoProfile -ExecutionPolicy Bypass -File "$root\scripts\run_smoke.ps1"
    powershell -NoProfile -ExecutionPolicy Bypass -File "$root\scripts\kpi_digest.ps1"
  }
  exit 0
}

if (-not $Spec) { throw "Gib -Spec <pfad zur .md/.txt> oder -ApproveLast an." }
$specText = Get-Content -Raw $Spec
$draftPath = New-DraftFromPreview -specText $specText
Apply-Draft -path $draftPath -OnlyWhatIf:$WhatIf
if (-not $WhatIf) {
  powershell -NoProfile -ExecutionPolicy Bypass -File "$root\scripts\run_smoke.ps1"
  powershell -NoProfile -ExecutionPolicy Bypass -File "$root\scripts\kpi_digest.ps1"
}

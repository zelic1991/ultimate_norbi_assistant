param(
  [Parameter(Mandatory=$true)][string]$Draft,
  [switch]$WhatIf,
  [switch]$Approve,
  [string]$ApproveSecret,
  [switch]$ForceYellow
)
$ErrorActionPreference = "Stop"

function Get-Prop($o,$name,$default=$null){
  if($null -ne $o -and $o.PSObject.Properties[$name]){ return $o.$name } else { return $default }
}
function Resolve-Full([string]$p, [string]$root){
  if([IO.Path]::IsPathRooted($p)){ return [IO.Path]::GetFullPath($p) }
  else{ return [IO.Path]::GetFullPath((Join-Path $root $p)) }
}
function Test-Under([string]$full, [string[]]$roots){
  foreach($r in $roots){
    if($full.StartsWith($r,[System.StringComparison]::InvariantCultureIgnoreCase)){ return $true }
  }
  return $false
}
function Like-Any([string]$rel, [string[]]$globs){
  $n = $rel -replace '\\','/'
  foreach($g in $globs){
    $pat = ($g -replace '\\','/').Replace('**/','*')
    if($n -like $pat){ return $true }
  }
  return $false
}

$proj = Split-Path -Parent $PSScriptRoot
$ts   = Get-Date -Format 'yyyyMMdd_HHmmss'

# Draft lesen
$draftObj = Get-Content -Raw $Draft | ConvertFrom-Json
$patch    = @($draftObj.patch)
if(-not $patch -or $patch.Count -eq 0){ throw "Patch ist leer." }

$adds   = [int](Get-Prop $draftObj 'adds' 0)
$rems   = [int](Get-Prop $draftObj 'rems' 0)
$model  = Get-Prop $draftObj 'model' 'n/a'
$tokens = Get-Prop $draftObj 'tokens' 'n/a'
$target = Get-Prop $draftObj 'target' (Get-Prop $patch[0] 'path')

# Policy laden
$policyPath = Join-Path $proj 'OPS\self_edit.policy.json'
if(Test-Path $policyPath){ $policy = Get-Content -Raw $policyPath | ConvertFrom-Json }
else{
  $policy = [pscustomobject]@{
    allow_dirs=@(".")
    deny_globs=@("**/apply_preview.ps1","**/policy*.json",".git/**",".secrets/**")
    limits = @{ max_files=7; max_lines_changed=400 }
    approval = @{ red_blocks_write=$true; yellow_needs_approval=$true }
  }
}
# Allow-Roots (voll qualifiziert)
$allowRoots = @()
foreach($ad in $policy.allow_dirs){
  $p = Resolve-Full $ad $proj
  $allowRoots += $p
}

# Critic (Ampel)
$filesCount = $patch.Count
$totalLines = $adds + $rems
$level   = 'Green'
$reasons = New-Object System.Collections.Generic.List[string]

if($totalLines -gt $policy.limits.max_lines_changed -or $filesCount -gt $policy.limits.max_files){
  $level='Red'; $reasons.Add('size')
}
# deny_globs?
if($level -ne 'Red'){
  $denyHit = $false
  foreach($ch in $patch){
    $full = Resolve-Full (Get-Prop $ch 'path') $proj
    $rel  = $full.Substring($proj.Length).TrimStart('\','/')
    if(Like-Any $rel $policy.deny_globs){ $denyHit=$true; break }
  }
  if($denyHit){ $level='Red'; $reasons.Add('deny_glob') }
}
if($level -eq 'Green' -and $totalLines -gt 150){ $level='Yellow'; $reasons.Add('large') }

# Logging-Ziel
$logDir = Join-Path $proj 'OPS\logs'
$null = New-Item -ItemType Directory -Force -Path $logDir
$log = Join-Path $logDir 'codegen_runs.log'

# WHAT-IF
if($WhatIf -and -not $Approve){
  Write-Host '--- WHAT-IF ---'
  Write-Host ("Status   : {0}" -f (Get-Prop $draftObj 'status' 'PREVIEW_ONLY'))
  Write-Host ("Target   : {0}" -f (Resolve-Full $target $proj))
  Write-Host ("Preview  : {0}" -f (Get-Prop $draftObj 'preview_path' '(n/a)'))
  Write-Host ("Changes  : +{0} / -{1}" -f $adds,$rems)
  Write-Host ("Critic   : {0} ({1})" -f $level, (($reasons.ToArray()) -join ','))

  $line = ("[{0}] status=PREVIEW_ONLY model={1} tokens={2} target={3} adds={4} rems={5} critic={6}" -f `
           $ts, $model, $tokens, (Resolve-Full $target $proj), $adds, $rems, $level)
  Add-Content -Path $log -Value $line -Encoding UTF8
  Write-Host "[INFO] Dry run only."
  exit 0
}

# APPROVE / Write
if($Approve){
  if($level -eq 'Red' -and $policy.approval.red_blocks_write){
    $line = ("[{0}] status=BLOCKED_RED model={1} target={2} adds={3} rems={4} critic={5}" -f `
             $ts,$model,(Resolve-Full $target $proj),$adds,$rems,$level)
    Add-Content -Path $log -Value $line -Encoding UTF8
    throw "BLOCKED: Critic=Red ($($reasons -join ','))"
  }
  if($level -eq 'Yellow' -and $policy.approval.yellow_needs_approval -and -not $ForceYellow){
    $envSecret = $env:APPROVAL_SECRET
    if(-not $ApproveSecret -or ($envSecret -and $ApproveSecret -ne $envSecret)){
      $line = ("[{0}] status=BLOCKED_YELLOW model={1} target={2} adds={3} rems={4} critic={5}" -f `
               $ts,$model,(Resolve-Full $target $proj),$adds,$rems,$level)
      Add-Content -Path $log -Value $line -Encoding UTF8
      throw "YELLOW approval required. Pass -ApproveSecret <secret> or -ForceYellow."
    }
  }

  $backupDir = Join-Path $proj '_backup'
  $null = New-Item -ItemType Directory -Force -Path $backupDir

  foreach($ch in $patch){
    $tgt = Resolve-Full (Get-Prop $ch 'path') $proj
    if(-not (Test-Under $tgt $allowRoots)){ throw "Target außerhalb allow_dirs: $tgt" }

    if(Test-Path $tgt){
      $bak = Join-Path $backupDir ("{0}.{1}.bak" -f (Split-Path -Leaf $tgt), $ts)
      Copy-Item $tgt $bak -Force
      Write-Host "[Backup] $bak"
    }
    $dir = Split-Path -Parent $tgt
    New-Item -ItemType Directory -Force -Path $dir | Out-Null

    $txt = Get-Prop $ch 'text'
    if($null -ne $txt){
      Set-Content -Path $tgt -Value $txt -Encoding UTF8
    } elseif($ch.PSObject.Properties['content_b64']) {
      [IO.File]::WriteAllBytes($tgt, [Convert]::FromBase64String($ch.content_b64))
    } else {
      throw "Patch ohne 'text' oder 'content_b64': $($ch | ConvertTo-Json -Compress)"
    }
    Write-Host "[WRITE]  $tgt"
  }

  $line = ("[{0}] status=APPROVED model={1} target={2} adds={3} rems={4} critic={5}" -f `
           $ts,$model,(Resolve-Full $target $proj),$adds,$rems,$level)
  Add-Content -Path $log -Value $line -Encoding UTF8
  Write-Host "[OK] Applied."
  exit 0
}

Write-Host "[INFO] Nothing done. Use -WhatIf or -Approve."
exit 0
# apply_draft.ps1 — v0.3 (Critic-Gate + WhatIf/Approve + KPI-Log)
# Usage:
#   pwsh -File .\apply_draft.ps1 -Draft .\OPS\drafts\*.json -WhatIf
#   pwsh -File .\apply_draft.ps1 -Draft .\OPS\drafts\*.json -Approve [-ForceYellow] [-ApproveSecret "..."]
param(
  [Parameter(Mandatory=$true)][string]$Draft,
  [switch]$WhatIf,
  [switch]$Approve,
  [switch]$ForceYellow,
  [string]$ApproveSecret
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSCommandPath
$logsDir = Join-Path $root "OPS\logs"
$reportsDir = Join-Path $root "OPS\reports"
$backupDir = Join-Path $root "_backup"
New-Item -ItemType Directory -Force $logsDir,$reportsDir,$backupDir | Out-Null

function Write-LogLine($kv) {
  $ts = Get-Date -Format "yyyyMMdd_HHmmss"
  $line = "[$ts] " + ($kv.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" } | Sort-Object | -join " ")
  Add-Content -Path (Join-Path $logsDir "codegen_runs.log") -Value $line -Encoding UTF8
}

function Read-Json($path) {
  Get-Content -Raw -Path $path | ConvertFrom-Json -Depth 100
}

function Is-ForbiddenPath($p, [string[]]$denyGlobs) {
  foreach($g in $denyGlobs){
    if ([System.Management.Automation.WildcardPattern]::new($g, 'IgnoreCase').IsMatch($p)) { return $true }
  }
  return $false
}

# --- Draft laden ---
if (-not (Test-Path $Draft)) { throw "Draft not found: $Draft" }
$draftObj = Read-Json $Draft
$target   = $draftObj.target
$adds     = [int]($draftObj.adds | ForEach-Object {$_})  # robust
$rems     = [int]($draftObj.rems | ForEach-Object {$_})
$status0  = "$( $draftObj.status )"
$patch    = @($draftObj.patch)
$preview  = "$( $draftObj.preview_path )"

# --- Critic ermitteln (aus Draft oder heuristisch) ---
$denyGlobs = @("**/apply_preview.ps1","**/policy*.json","**/.git/**","**/secrets/**")
$level = $null
$reasons = New-Object System.Collections.Generic.List[string]

if ($draftObj.PSObject.Properties.Name -contains "critic" -and $draftObj.critic.level) {
  $level = "$( $draftObj.critic.level )"
  if ($draftObj.critic.reasons) { $reasons.AddRange([string[]]$draftObj.critic.reasons) }
}
if (-not $level) {
  $total = $adds + $rems
  $paths = @()
  foreach($chg in $patch) { if ($chg.path) { $paths += "$( $chg.path )" } }
  $unique = ($paths | Select-Object -Unique)
  $isRed = $false
  foreach($p in $paths){ if (Is-ForbiddenPath $p $denyGlobs){ $isRed=$true; $reasons.Add("forbidden:$p") } }
  if ($unique.Count -gt 7 -or $total -gt 400) { $isRed=$true; $reasons.Add("size") }
  if ($isRed) { $level = "Red" }
  elseif ($total -gt 150) { $level = "Yellow"; $reasons.Add("large") }
  else { $level = "Green" }
}

Write-Host "--- WHAT-IF ---"
Write-Host ("Status   : {0}" -f $status0)
Write-Host ("Target   : {0}" -f $target)
Write-Host ("Preview  : {0}" -f $preview)
Write-Host ("Changes  : +{0} / -{1}" -f $adds, $rems)
Write-Host ("Critic   : {0} ({1})" -f $level, ($(if($reasons.Count){$reasons -join ", "}else{"-"})))
Write-Host "---"

# Immer WHAT-IF Ausgabe (diff je Datei)
foreach($chg in $patch){
  $tgt = $chg.path
  $newText = $chg.text
  if (-not $tgt -or -not $newText){ continue }
  Write-Host "[WHAT-IF] $tgt"
  if (Test-Path $tgt) {
    $old = Get-Content -Raw $tgt
    $diff = Compare-Object ($old -split "`r?`n") ($newText -split "`r?`n") -IncludeEqual:$false
    $addsC = ($diff | Where-Object {$_.SideIndicator -eq "=>"}).Count
    $remsC = ($diff | Where-Object {$_.SideIndicator -eq "<="}).Count
    Write-Host ("  adds={0} rems={1}" -f $addsC, $remsC)
  } else {
    Write-Host "  (new file)"
  }
}

if ($WhatIf -and -not $Approve) {
  Write-Host "[INFO] Dry run only."
  Write-LogLine(@{ status="PREVIEW_ONLY"; model=$draftObj.model; tokens=($draftObj.tokens ?? "n/a"); target=$target; adds=$adds; rems=$rems; critic=$level })
  exit 0
}

# --- Approval Gate ---
if ($Approve) {
  if ($level -eq "Red") {
    Write-Host "[BLOCK] Critic=Red -> Write blocked."
    Write-LogLine(@{ status="BLOCKED_RED"; model=$draftObj.model; target=$target; adds=$adds; rems=$rems; critic=$level })
    exit 2
  }
  if ($level -eq "Yellow" -and -not $ForceYellow) {
    $sec = if ($ApproveSecret) { $ApproveSecret } else { $env:APPROVAL_SECRET }
    if (-not $sec) {
      Write-Host "[DENY] Yellow needs approval: set -ApproveSecret or env:APPROVAL_SECRET."
      Write-LogLine(@{ status="DENIED_YELLOW"; model=$draftObj.model; target=$target; adds=$adds; rems=$rems; critic=$level })
      exit 3
    }
  }

  # --- Apply (mit Backup) ---
  foreach($chg in $patch){
    $tgt = $chg.path
    $newText = $chg.text
    if (-not $tgt -or -not $newText){ continue }
    $abs = (Resolve-Path -LiteralPath $tgt -ErrorAction SilentlyContinue)
    if (-not $abs) {
      $abs = Resolve-Path -LiteralPath (Join-Path $root (Split-Path -Leaf $tgt)) -ErrorAction SilentlyContinue
    }
    $outPath = $tgt
    if (-not [System.IO.Path]::IsPathRooted($outPath)) {
      $outPath = Join-Path $root $tgt
    }
    $outDir = Split-Path -Parent $outPath
    New-Item -ItemType Directory -Force $outDir | Out-Null

    if (Test-Path $outPath) {
      $ts = Get-Date -Format "yyyyMMdd_HHmmss"
      $bak = Join-Path $backupDir ("{0}.{1}.bak" -f (Split-Path -Leaf $outPath), $ts)
      Copy-Item -LiteralPath $outPath -Destination $bak -Force
      Write-Host "[Backup] $bak"
    }
    Set-Content -Path $outPath -Value $newText -Encoding UTF8
    Write-Host "[WRITE]  $outPath"
  }

  Write-Host "[OK] Applied."
  Write-LogLine(@{ status="APPROVED"; model=$draftObj.model; target=$target; adds=$adds; rems=$rems; critic=$level })
  exit 0
}

Write-Host "[INFO] Nothing done. Use -WhatIf or -Approve."
exit 0
param(
  [Parameter(Mandatory=$true)][string]$Draft,
  [switch]$WhatIf,
  [switch]$Approve
)

$ErrorActionPreference = 'Stop'
$root   = Split-Path -Parent $PSCommandPath
$backup = Join-Path $root "_backup"
New-Item -ItemType Directory -Force $backup | Out-Null

if (-not (Test-Path $Draft)) { throw "Draft nicht gefunden: $Draft" }
$data = Get-Content $Draft -Raw | ConvertFrom-Json

Write-Host '--- WHAT-IF ---'
Write-Host ('Status   : {0}' -f $data.status)
Write-Host ('Target   : {0}' -f $data.target)
Write-Host ('Preview  : {0}' -f $data.preview_path)
Write-Host ('Changes  : +{0} / -{1}' -f $data.adds, $data.rems)
Write-Host '---'

foreach ($p in $data.patch) {
  $tgt = $p.path
  if (-not [System.IO.Path]::IsPathRooted($tgt)) {
    $tgt = (Resolve-Path (Join-Path $root $tgt)).Path
  }
  $old = if (Test-Path $tgt) { Get-Content $tgt -Raw -ErrorAction SilentlyContinue } else { "" }
  $new = [string]$p.text

  if ($WhatIf -and -not $Approve) {
    Write-Host ("[WHAT-IF] {0}" -f $tgt)
    $ol = $old -split "`r?`n"
    $nl = $new -split "`r?`n"
    $adds = (@(Compare-Object $ol $nl | Where-Object {$_.SideIndicator -eq '=>'})).Count
    $rems = (@(Compare-Object $ol $nl | Where-Object {$_.SideIndicator -eq '<='})).Count
    Write-Host ("  adds={0} rems={1}" -f $adds, $rems)
    continue
  }

  if ($Approve) {
    $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
    if (Test-Path $tgt) {
      $bak = Join-Path $backup ("{0}.{1}.bak" -f ([IO.Path]::GetFileName($tgt)), $ts)
      Set-Content -Encoding UTF8 -Path $bak -Value $old
      Write-Host ("[Backup] {0}" -f $bak)
    }
    New-Item -ItemType Directory -Force ([IO.Path]::GetDirectoryName($tgt)) | Out-Null
    Set-Content -Encoding UTF8 -Path $tgt -Value $new
    Write-Host ("[WRITE]  {0}" -f $tgt)
    # --- Log entry (APPROVED) ---
    try {
      # Projekt-Root robust aus Ziel-Datei ableiten
      $projRoot = Split-Path -Parent $data.target
      if (-not $projRoot) { $projRoot = Split-Path -Parent $PSCommandPath }

      $opsLogs = Join-Path $projRoot 'OPS\logs'
      New-Item -ItemType Directory -Force $opsLogs | Out-Null
      $log = Join-Path $opsLogs 'codegen_runs.log'

      # Felder defensiv aus $data
      $ts    = if ($data.ts)    { $data.ts }    else { Get-Date -Format "yyyyMMdd_HHmmss" }
      $model = if ($data.model) { $data.model } else { "n/a" }
      $adds  = if ($null -ne $data.adds) { [int]$data.adds } else { 0 }
      $rems  = if ($null -ne $data.rems) { [int]$data.rems } else { 0 }

      $line = "[{0}] status=APPROVED model={1} target={2} adds={3} rems={4}" -f $ts, $model, $data.target, $adds, $rems
      Add-Content -Path $log -Value $line -Encoding UTF8
    } catch {
      Write-Warning ("[LOG] failed: {0}" -f $_.Exception.Message)
    }
  }
}

if ($Approve) { Write-Host "[OK] Applied." } else { Write-Host "[INFO] Dry run only." }

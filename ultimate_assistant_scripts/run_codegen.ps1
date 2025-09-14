param(
  [Parameter(Mandatory=$true)][string]$Spec,
  [Parameter(Mandatory=$true)][string]$Filename,
  [string]$OutDir = "CURRENT",
  [switch]$Dry
)
$ErrorActionPreference = "Stop"
Set-Location "C:\\Users\\Norbi\\Ultimate_Norbi_Assistant"
if (-not $env:OPENAI_API_KEY) { Write-Error "OPENAI_API_KEY fehlt. Beispiel: `setx OPENAI_API_KEY <key>` und neues Terminal öffnen."; exit 2 }
$cmd = ".\\.venv\\Scripts\\python.exe .\\tools\\codegen.py --spec \"$Spec\" --filename \"$Filename\" --outdir \"$OutDir\""
if ($Dry) { $cmd += " --dry" }
Write-Host "RUN:" $cmd
Invoke-Expression $cmd

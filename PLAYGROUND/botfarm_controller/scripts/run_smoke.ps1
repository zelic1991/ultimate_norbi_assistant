$ErrorActionPreference = "Stop"
$proj = Split-Path -Parent $PSScriptRoot
Push-Location $proj
try {
  $env:PYTHONPATH = $proj
  $fail = 0
  python -m pytest tests/smoke/test_generated_module.py -q
  if ($LASTEXITCODE -ne 0) { $fail = 1 }
  if ($fail -eq 1) { Write-Host "SMOKE=FAIL"; exit 1 } else { Write-Host "SMOKE=GREEN"; exit 0 }
}
finally { Pop-Location }

$ErrorActionPreference = 'Stop'
Set-Location "C:\Users\Norbi\Ultimate_Norbi_Assistant"
$env:PYTHONPATH = (Get-Location).Path

function Run-Step([string]$label, [string[]]$cmd) {
  Write-Host $label
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  & .\.venv\Scripts\python.exe ".\main.py" @cmd
  $sw.Stop()
  $sec = [math]::Round($sw.Elapsed.TotalSeconds, 1)
  Write-Host ("    fertig in {0:N1}s" -f $sec)
  return $sec
}

$k1 = Run-Step "[1/3] COMPRESS" @("compress")
$k2 = Run-Step "[2/3] DEDUPE"   @("dedupe","--confirm")
$k3 = Run-Step "[3/3] VALIDATE" @("validate")

$stamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
$line  = "[Run $stamp] compress=${k1}s; dedupe=${k2}s; validate=${k3}s"
Add-Content -Path ".\logs\maintenance_runs.log" -Value $line

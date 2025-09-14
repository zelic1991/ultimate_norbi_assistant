$ErrorActionPreference = 'Stop'
Set-Location "C:\Users\Norbi\Ultimate_Norbi_Assistant"
$log = ".\logs\maintenance_runs.log"
if (!(Test-Path $log)) { Write-Host "Keine Logs gefunden." ; exit 0 }

$since = (Get-Date).AddHours(-24)
$lines = Get-Content $log
$entries = foreach ($line in $lines) {
    if ($line -match '^\[Run (?<ts>[\d-]+\s[\d:]+)\]\s+(?<rest>.*)$') {
        $ts = Get-Date $Matches.ts
        if ($ts -ge $since) {
            [pscustomobject]@{Ts=$ts; Line=$line}
        }
    }
}
if (!$entries) { Write-Host "Keine Runs in den letzten 24h." ; exit 0 }

$compressNone = ($entries | Where-Object { $_.Line -match 'compress=Keine Dateien' }).Count
$dedupeNone   = ($entries | Where-Object { $_.Line -match 'dedupe=Keine Duplikate' }).Count

function ExtractSec($s, $key) {
    if ($s -match "$key=.*?([0-9]+(\.[0-9]+)?)s") { return [double]$Matches[1] } else { return $null }
}

$compSecs = @(); $deduSecs = @(); $valiSecs = @()
foreach ($e in $entries) {
    $compSecs += (ExtractSec $e.Line 'compress')
    $deduSecs += (ExtractSec $e.Line 'dedupe')
    $valiSecs += (ExtractSec $e.Line 'validate')
}
$avg = @{
    compress = "{0:N1}" -f (($compSecs | Where-Object {$_ -ne $null} | Measure-Object -Average).Average)
    dedupe   = "{0:N1}" -f (($deduSecs | Where-Object {$_ -ne $null} | Measure-Object -Average).Average)
    validate = "{0:N1}" -f (($valiSecs | Where-Object {$_ -ne $null} | Measure-Object -Average).Average)
}

Write-Host "=== Digest (letzte 24h) ==="
Write-Host ("Runs: {0}" -f $entries.Count)
Write-Host ("compress (Ø s): {0} | leer: {1}" -f $avg.compress, $compressNone)
Write-Host ("dedupe   (Ø s): {0} | leer: {1}" -f $avg.dedupe,   $dedupeNone)
Write-Host ("validate (Ø s): {0}" -f $avg.validate)
Write-Host ""
Write-Host "Letzte 5:"
$entries | Sort-Object Ts -Descending | Select-Object -First 5 | ForEach-Object { $_.Line }

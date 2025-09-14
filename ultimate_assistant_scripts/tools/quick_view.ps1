param(
  [Parameter(Mandatory=$true)][string]$Path,
  [int]$Rows = 10
)

$ErrorActionPreference = 'Stop'
$base   = "C:\\Users\\Norbi\\Ultimate_Norbi_Assistant"
$python = Join-Path $base ".venv\\Scripts\\python.exe"

if (-not (Test-Path $Path)) { Write-Error "Datei nicht gefunden: $Path"; exit 1 }
$fi = Get-Item $Path
$ext = $fi.Extension.ToLower()
$full = $fi.FullName

function Show-Stopwatch([scriptblock]$sb) {
  $sw=[Diagnostics.Stopwatch]::StartNew()
  & $sb
  $sw.Stop()
  Write-Host ("fertig in {0:N1}s" -f $sw.Elapsed.TotalSeconds)
}

function View-CsvGz($fullPath, $rows) {
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $fs = [IO.File]::OpenRead($fullPath)
  try {
    $gz = New-Object IO.Compression.GZipStream($fs,[IO.Compression.CompressionMode]::Decompress)
    $sr = New-Object IO.StreamReader($gz,[Text.Encoding]::UTF8)
    $i=0
    $header = $sr.ReadLine()
    if ($null -eq $header) { Write-Host "(leer)"; return }
    Write-Host $header
    while (($line = $sr.ReadLine()) -ne $null -and $i -lt $rows) {
      Write-Host $line
      $i++
    }
  } finally {
    $sr.Dispose(); $gz.Dispose(); $fs.Dispose()
  }
}

function Decompress-Gz-ToTemp($fullPath) {
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $tmp = [System.IO.Path]::ChangeExtension([System.IO.Path]::GetTempFileName(), (Get-Item $fullPath).BaseName + ".parquet").Replace(".tmp",".parquet")
  $in  = [IO.File]::OpenRead($fullPath)
  $gz  = New-Object IO.Compression.GZipStream($in,[IO.Compression.CompressionMode]::Decompress)
  $out = [IO.File]::Create($tmp)
  try { $gz.CopyTo($out) } finally { $gz.Dispose(); $out.Dispose(); $in.Dispose() }
  return $tmp
}

function View-Parquet($parquetPath, $rows) {
  $py = @"
import sys, pyarrow.parquet as pq
p = r'$parquetPath'
t = pq.read_table(p)
print(f'Rows={t.num_rows}, Cols={t.num_columns}')
print('Columns:', ', '.join(t.schema.names) if t.num_columns>0 else '(none)')
n = min($rows, t.num_rows)
if n>0:
    import pandas as pd
    print('\nHead:')
    print(t.slice(0,n).to_pandas().to_csv(index=False))
"@
  $null = $py | & $python -
}

Show-Stopwatch {
  switch ($ext) {
    '.csv'         { Write-Host "CSV:" $full; Get-Content -Path $full -TotalCount ($Rows+1) | ForEach-Object { $_ } }
    '.gz'          {
                      if ($full.ToLower().EndsWith('.csv.gz')) {
                        Write-Host "CSV.GZ:" $full
                        View-CsvGz -fullPath $full -rows $Rows
                      } elseif ($full.ToLower().EndsWith('.parquet.gz')) {
                        Write-Host "PARQUET.GZ:" $full
                        $tmp = Decompress-Gz-ToTemp $full
                        try { View-Parquet -parquetPath $tmp -rows $Rows } finally { Remove-Item $tmp -ErrorAction SilentlyContinue }
                      } else {
                        Write-Error "Unbekanntes .gz-Format: $full"
                      }
                    }
    '.parquet'     { Write-Host "PARQUET:" $full; View-Parquet -parquetPath $full -rows $Rows }
    default        { Write-Error "Nicht unterstützt: $ext"; exit 2 }
  }
}

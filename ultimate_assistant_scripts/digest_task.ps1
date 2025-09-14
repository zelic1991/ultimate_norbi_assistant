$ErrorActionPreference = 'Stop'
Set-Location "C:\\Users\\Norbi\\Ultimate_Norbi_Assistant"
./digest.ps1 | Out-File -Encoding UTF8 "./logs/digest_last.txt"

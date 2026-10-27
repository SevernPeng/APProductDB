[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$DataRoot = (Resolve-Path (Join-Path $ProjectDir '..')).Path
if (-not $DataRoot.StartsWith('D:\APProductDB', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Runtime data must remain on D:.' }
$Python = Join-Path $ProjectDir '.venv\Scripts\python.exe'
$LogDir = Join-Path $DataRoot 'logs'
$LogFile = Join-Path $LogDir 'backup.log'
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
if ((Test-Path -LiteralPath $LogFile) -and (Get-Item -LiteralPath $LogFile).Length -ge 10MB) {
    Move-Item -LiteralPath $LogFile -Destination (Join-Path $LogDir ("backup-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss')))
}
Set-Location -LiteralPath $ProjectDir
"$(Get-Date -Format o) Backup started" | Out-File -LiteralPath $LogFile -Append -Encoding utf8
& $Python manage.py backup_database *>> $LogFile
$exitCode = $LASTEXITCODE
"$(Get-Date -Format o) Backup finished with code $exitCode" | Out-File -LiteralPath $LogFile -Append -Encoding utf8
if ($exitCode -eq 0) {
    $priceMarker = Join-Path $DataRoot 'data\syscom-price-last-success.txt'
    $priceScript = Join-Path $ProjectDir 'scripts\sync_syscom_prices.ps1'
    $priceDue = -not (Test-Path -LiteralPath $priceMarker)
    if (-not $priceDue) {
        $priceDue = (Get-Item -LiteralPath $priceMarker).LastWriteTime -le (Get-Date).AddDays(-7)
    }
    if ($priceDue) {
        "$(Get-Date -Format o) SYSCOM price sync fallback is due" | Out-File -LiteralPath $LogFile -Append -Encoding utf8
        & $priceScript
        $priceExitCode = $LASTEXITCODE
        "$(Get-Date -Format o) SYSCOM price sync fallback finished with code $priceExitCode" | Out-File -LiteralPath $LogFile -Append -Encoding utf8
    }
}
exit $exitCode

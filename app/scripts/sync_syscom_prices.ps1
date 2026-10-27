[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$DataRoot = (Resolve-Path (Join-Path $ProjectDir '..')).Path
if (-not $DataRoot.StartsWith('D:\APProductDB', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Runtime data must remain on D:.'
}
$Python = Join-Path $ProjectDir '.venv\Scripts\python.exe'
$CredentialFile = Join-Path $DataRoot 'credentials\syscom.xml'
$LogDir = Join-Path $DataRoot 'runtime\logs'
$LogFile = Join-Path $LogDir 'syscom-prices.log'
$SuccessMarker = Join-Path $DataRoot 'data\syscom-price-last-success.txt'
if (-not (Test-Path -LiteralPath $CredentialFile)) { throw "Credential file not found: $CredentialFile" }
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
if ((Test-Path -LiteralPath $LogFile) -and (Get-Item -LiteralPath $LogFile).Length -ge 10MB) {
    Move-Item -LiteralPath $LogFile -Destination (Join-Path $LogDir ("syscom-prices-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss')))
}
$Credential = Import-Clixml -LiteralPath $CredentialFile
$env:SYSCOM_USERNAME = $Credential.UserName
$env:SYSCOM_PASSWORD = $Credential.GetNetworkCredential().Password
$env:PYTHONUNBUFFERED = '1'
try {
    Set-Location -LiteralPath $ProjectDir
    "$(Get-Date -Format o) SYSCOM price sync started" | Out-File -LiteralPath $LogFile -Append -Encoding utf8
    & $Python manage.py sync_syscom_prices *>> $LogFile
    $exitCode = $LASTEXITCODE
    "$(Get-Date -Format o) SYSCOM price sync finished with code $exitCode" | Out-File -LiteralPath $LogFile -Append -Encoding utf8
    if ($exitCode -eq 0) {
        [System.IO.File]::WriteAllText($SuccessMarker, (Get-Date).ToString('o'), [System.Text.Encoding]::UTF8)
    }
    if ($exitCode -ne 0) { throw "SYSCOM price synchronization failed with exit code $exitCode" }
} finally {
    Remove-Item Env:SYSCOM_USERNAME -ErrorAction SilentlyContinue
    Remove-Item Env:SYSCOM_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:PYTHONUNBUFFERED -ErrorAction SilentlyContinue
}

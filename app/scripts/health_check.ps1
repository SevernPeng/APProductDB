[CmdletBinding()]
param(
    [string]$Url = 'http://127.0.0.1:8000/health/'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$DataRoot = (Resolve-Path (Join-Path $ProjectDir '..')).Path
$LogDir = Join-Path $DataRoot 'logs'
$LogFile = Join-Path $LogDir 'health-check.log'
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
try {
    $response = Invoke-RestMethod -Uri $Url -TimeoutSec 10
    if ($response.status -ne 'ok' -or $response.database -ne 'ok') { throw 'Health response was not OK.' }
    "$(Get-Date -Format o) OK $Url" | Out-File -LiteralPath $LogFile -Append -Encoding utf8
    exit 0
} catch {
    "$(Get-Date -Format o) ERROR $Url $($_.Exception.Message)" | Out-File -LiteralPath $LogFile -Append -Encoding utf8
    exit 1
}

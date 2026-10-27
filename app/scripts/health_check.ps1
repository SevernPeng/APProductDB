[CmdletBinding()]
param(
    [string]$Url = 'http://127.0.0.1:8000/health/',
    [string]$ServerTaskName = 'APProductDB-Server',
    [ValidateRange(10, 180)]
    [int]$RecoveryTimeoutSeconds = 90
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$DataRoot = (Resolve-Path (Join-Path $ProjectDir '..')).Path
$LogDir = Join-Path $DataRoot 'runtime\logs'
$LogFile = Join-Path $LogDir 'health-check.log'
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
try {
    $response = Invoke-RestMethod -Uri $Url -TimeoutSec 10
    if ($response.status -ne 'ok' -or $response.database -ne 'ok') { throw 'Health response was not OK.' }
    "$(Get-Date -Format o) OK $Url" | Out-File -LiteralPath $LogFile -Append -Encoding utf8
    exit 0
} catch {
    $initialError = $_.Exception.Message
    "$(Get-Date -Format o) ERROR $Url $initialError; starting automatic recovery." |
        Out-File -LiteralPath $LogFile -Append -Encoding utf8
}

$RestartScript = Join-Path $PSScriptRoot 'restart_server.ps1'
try {
    & $RestartScript `
        -TaskName $ServerTaskName `
        -HealthUrl $Url `
        -StartupTimeoutSeconds $RecoveryTimeoutSeconds 2>&1 |
        Out-File -LiteralPath $LogFile -Append -Encoding utf8
    if ($LASTEXITCODE -ne 0) {
        throw "Restart script exited with code $LASTEXITCODE."
    }
    $response = Invoke-RestMethod -Uri $Url -TimeoutSec 10
    if ($response.status -ne 'ok' -or $response.database -ne 'ok') {
        throw 'Health response was not OK after restart.'
    }
    "$(Get-Date -Format o) RECOVERED $Url" |
        Out-File -LiteralPath $LogFile -Append -Encoding utf8
    exit 0
} catch {
    "$(Get-Date -Format o) RECOVERY_FAILED $Url $($_.Exception.Message)" |
        Out-File -LiteralPath $LogFile -Append -Encoding utf8
    exit 1
}

[CmdletBinding()]
param(
    [ValidateSet('Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday')]
    [string]$DayOfWeek = 'Sunday',
    [string]$At = '02:00'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$DataRoot = (Resolve-Path (Join-Path $ProjectDir '..')).Path
if (-not $DataRoot.StartsWith('D:\APProductDB', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'APProductDB must stay on D:.'
}
$syncScript = Join-Path $PSScriptRoot 'sync_syscom_prices.ps1'
$credentialFile = Join-Path $DataRoot 'credentials\syscom.xml'
if (-not (Test-Path -LiteralPath $syncScript)) { throw "Sync script not found: $syncScript" }
if (-not (Test-Path -LiteralPath $credentialFile)) { throw "Credential file not found: $credentialFile" }

$PowerShellExe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$action = New-ScheduledTaskAction -Execute $PowerShellExe -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$syncScript`""
$runAt = [DateTime]::Today.Add([TimeSpan]::Parse($At))
$trigger = New-ScheduledTaskTrigger -Weekly -WeeksInterval 1 -DaysOfWeek $DayOfWeek -At $runAt
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 6) -MultipleInstances IgnoreNew
$userId = "$env:USERDOMAIN\$env:USERNAME"
$taskPrincipal = New-ScheduledTaskPrincipal -UserId $userId -LogonType S4U -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $taskPrincipal
Register-ScheduledTask -TaskName 'APProductDB-SyscomPrices' -InputObject $task -Force | Out-Null
Write-Output "Installed APProductDB-SyscomPrices: every $DayOfWeek at $At."

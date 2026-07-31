[CmdletBinding()]
param(
    [string]$LanSubnet = '192.168.68.0/22',
    [string]$DailyBackupTime = '23:00',
    [switch]$SkipPowerSettings
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this script from an elevated PowerShell window.'
}
$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$DataRoot = (Resolve-Path (Join-Path $ProjectDir '..')).Path
if (-not $DataRoot.StartsWith('D:\APProductDB', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'APProductDB must stay on D:.' }
$currentSid = $identity.User.Value
function Protect-DataTree([string]$Path) {
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
    & icacls.exe $Path /inheritance:r /grant:r "*$($currentSid):(OI)(CI)F" '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Failed to protect data directory: $Path" }
    $children = Join-Path $Path '*'
    & icacls.exe $children /inheritance:r /grant:r "*$($currentSid):F" '*S-1-5-18:F' '*S-1-5-32-544:F' /T /C | Out-Null
    if ($LASTEXITCODE -notin @(0, 3)) { throw "Failed to protect existing data files: $Path" }
}
foreach ($directory in @('data','media','backups','logs','restore-tests')) {
    Protect-DataTree (Join-Path $DataRoot $directory)
}
$environmentFile = Join-Path $ProjectDir '.env'
& icacls.exe $environmentFile /inheritance:r /grant:r "*$($currentSid):F" '*S-1-5-18:F' '*S-1-5-32-544:F' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Failed to protect the .env file.' }
$PowerShellExe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
function New-ScriptAction([string]$ScriptName) {
    $path = Join-Path $PSScriptRoot $ScriptName
    New-ScheduledTaskAction -Execute $PowerShellExe -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$path`""
}

$ruleName = 'APProductDB-LAN-8000'
Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue | Remove-NetFirewallRule
New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000 -RemoteAddress $LanSubnet -Profile Domain,Private | Out-Null

$userId = "$env:USERDOMAIN\$env:USERNAME"
$taskPrincipal = New-ScheduledTaskPrincipal -UserId $userId -LogonType S4U -RunLevel Highest
$serverSettings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5) -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero)
$serverTask = New-ScheduledTask -Action (New-ScriptAction 'start_server.ps1') -Trigger (New-ScheduledTaskTrigger -AtStartup) -Settings $serverSettings -Principal $taskPrincipal
Register-ScheduledTask -TaskName 'APProductDB-Server' -InputObject $serverTask -Force | Out-Null

$backupAt = [DateTime]::Today.Add([TimeSpan]::Parse($DailyBackupTime))
$backupSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$backupTask = New-ScheduledTask -Action (New-ScriptAction 'backup.ps1') -Trigger (New-ScheduledTaskTrigger -Daily -At $backupAt) -Settings $backupSettings -Principal $taskPrincipal
Register-ScheduledTask -TaskName 'APProductDB-Backup' -InputObject $backupTask -Force | Out-Null

$healthTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 3650)
$healthSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 2)
$healthTask = New-ScheduledTask -Action (New-ScriptAction 'health_check.ps1') -Trigger $healthTrigger -Settings $healthSettings -Principal $taskPrincipal
Register-ScheduledTask -TaskName 'APProductDB-HealthCheck' -InputObject $healthTask -Force | Out-Null

if (-not $SkipPowerSettings) {
    powercfg /change standby-timeout-ac 0 | Out-Null
    powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 0 | Out-Null
    powercfg /setactive SCHEME_CURRENT | Out-Null
}
Write-Output "Installed firewall rule for $LanSubnet and three APProductDB scheduled tasks."

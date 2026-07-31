[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this script from an elevated PowerShell window.'
}

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$DataRoot = (Resolve-Path (Join-Path $ProjectDir '..')).Path
if (-not $DataRoot.StartsWith('D:\APProductDB', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "APProductDB must run from D:\APProductDB. Resolved: $DataRoot"
}

$Ollama = Join-Path $DataRoot 'tools\ollama\ollama.exe'
if (-not (Test-Path -LiteralPath $Ollama)) {
    throw "Ollama executable not found: $Ollama"
}

$PowerShellExe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$StartScript = Join-Path $PSScriptRoot 'start_ollama.ps1'
$action = New-ScheduledTaskAction `
    -Execute $PowerShellExe `
    -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$StartScript`""
$trigger = New-ScheduledTaskTrigger -AtStartup
$taskPrincipal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew
$task = New-ScheduledTask `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $taskPrincipal
Register-ScheduledTask `
    -TaskName 'APProductDB-Ollama' `
    -InputObject $task `
    -Description 'Local Ollama service for APProductDB datasheet extraction.' `
    -Force |
    Out-Null

Start-ScheduledTask -TaskName 'APProductDB-Ollama'
$marker = Join-Path $DataRoot 'logs\ollama-task-install.log'
"$(Get-Date -Format o) APProductDB-Ollama task registered and started." |
    Out-File -LiteralPath $marker -Append -Encoding utf8

[CmdletBinding()]
param(
    [string]$TaskName = 'APProductDB-Server',
    [int]$Port = 8000,
    [string]$HealthUrl = 'http://127.0.0.1:8000/health/',
    [ValidateRange(10, 300)]
    [int]$StartupTimeoutSeconds = 60
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$DataRoot = (Resolve-Path (Join-Path $ProjectDir '..')).Path
if (-not $DataRoot.StartsWith('D:\APProductDB', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "APProductDB must run from D:\APProductDB. Resolved: $DataRoot"
}

$Waitress = Join-Path $ProjectDir '.venv\Scripts\waitress-serve.exe'
$LogDir = Join-Path $DataRoot 'logs'
$RestartLog = Join-Path $LogDir 'restart-server.log'
if (-not (Test-Path -LiteralPath $Waitress)) {
    throw "Waitress executable not found: $Waitress"
}
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

function Write-RestartLog([string]$Message) {
    $line = "$(Get-Date -Format o) $Message"
    $line | Out-File -LiteralPath $RestartLog -Append -Encoding utf8
    Write-Output $line
}

function Get-WaitressProcesses {
    @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object {
        $_.CommandLine -and
        $_.CommandLine.IndexOf($Waitress, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 -and
        $_.CommandLine.IndexOf('config.wsgi:application', [System.StringComparison]::OrdinalIgnoreCase) -ge 0
    })
}

function Get-PortListeners {
    @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Test-ApplicationHealth {
    try {
        $response = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 5
        return $response.status -eq 'ok' -and $response.database -eq 'ok'
    } catch {
        return $false
    }
}

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
$originalListenerPids = @(
    Get-PortListeners | Select-Object -ExpandProperty OwningProcess -Unique
)
Write-RestartLog "Full restart requested for scheduled task $TaskName."

if ($task.State -eq 'Running') {
    Write-RestartLog "Stopping scheduled task $TaskName."
    Stop-ScheduledTask -TaskName $TaskName
}

$taskStopDeadline = (Get-Date).AddSeconds(15)
do {
    $task = Get-ScheduledTask -TaskName $TaskName
    if ($task.State -ne 'Running') {
        break
    }
    Start-Sleep -Milliseconds 500
} while ((Get-Date) -lt $taskStopDeadline)

$staleProcesses = @(Get-WaitressProcesses)
foreach ($process in $staleProcesses) {
    Write-RestartLog "Stopping residual Waitress PID $($process.ProcessId)."
    Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
}

$listeners = @(Get-PortListeners)
foreach ($listener in $listeners) {
    $listenerProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
    if ($listenerProcess.Name -notin @('python.exe', 'waitress-serve.exe')) {
        throw (
            "TCP port $Port is occupied by unexpected process " +
            "$($listenerProcess.Name) PID $($listener.OwningProcess); it was not stopped."
        )
    }
    Write-RestartLog (
        "Stopping residual port listener $($listenerProcess.Name) " +
        "PID $($listener.OwningProcess)."
    )
    try {
        Stop-Process -Id $listener.OwningProcess -Force -ErrorAction Stop
    } catch {
        Write-RestartLog (
            "Direct stop was denied for PID $($listener.OwningProcess); " +
            "delegating cleanup to the elevated scheduled-task launcher."
        )
    }
}

$processStopDeadline = (Get-Date).AddSeconds(15)
do {
    $remainingProcesses = @(Get-WaitressProcesses)
    $remainingListeners = @(Get-PortListeners)
    if ($remainingProcesses.Count -eq 0 -and $remainingListeners.Count -eq 0) {
        break
    }
    Start-Sleep -Milliseconds 500
} while ((Get-Date) -lt $processStopDeadline)
if ($remainingProcesses.Count -ne 0) {
    Write-RestartLog (
        "Waitress PID(s) still present before launch: " +
        "$($remainingProcesses.ProcessId -join ', ')."
    )
}
if ($remainingListeners.Count -ne 0) {
    Write-RestartLog (
        "TCP port $Port is still held by old PID(s) " +
        "$($remainingListeners.OwningProcess -join ', '); launcher cleanup is required."
    )
}

Write-RestartLog "Starting scheduled task $TaskName."
Start-ScheduledTask -TaskName $TaskName

$healthDeadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
do {
    if (Test-ApplicationHealth) {
        $runningListeners = @(Get-PortListeners)
        $replacementListeners = @(
            $runningListeners | Where-Object {
                $_.OwningProcess -notin $originalListenerPids
            }
        )
        if ($originalListenerPids.Count -gt 0 -and $replacementListeners.Count -eq 0) {
            Start-Sleep -Seconds 1
            continue
        }
        $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
        Write-RestartLog (
            "Restart completed; health check passed; listener PID(s): " +
            "$($runningListeners.OwningProcess -join ', '); last task result: $($taskInfo.LastTaskResult)."
        )
        exit 0
    }
    Start-Sleep -Seconds 1
} while ((Get-Date) -lt $healthDeadline)

$task = Get-ScheduledTask -TaskName $TaskName
$taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
throw (
    "Service did not become healthy within $StartupTimeoutSeconds seconds. " +
    "Task state: $($task.State); last task result: $($taskInfo.LastTaskResult). " +
    "Check $RestartLog and $(Join-Path $LogDir 'waitress-runtime.log')."
)

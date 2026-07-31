[CmdletBinding()]
param(
    [string]$TaskName = 'APProductDB-Ollama',
    [int]$Port = 11434,
    [ValidateRange(10, 180)]
    [int]$StartupTimeoutSeconds = 60
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$DataRoot = (Resolve-Path (Join-Path $ProjectDir '..')).Path
if (-not $DataRoot.StartsWith('D:\APProductDB', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "APProductDB must run from D:\APProductDB. Resolved: $DataRoot"
}

$Ollama = Join-Path $DataRoot 'tools\ollama\ollama.exe'
$LogDir = Join-Path $DataRoot 'logs'
$RestartLog = Join-Path $LogDir 'restart-ollama.log'
if (-not (Test-Path -LiteralPath $Ollama)) {
    throw "Ollama executable not found: $Ollama"
}
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

function Write-RestartLog([string]$Message) {
    $line = "$(Get-Date -Format o) $Message"
    $line | Out-File -LiteralPath $RestartLog -Append -Encoding utf8
    Write-Output $line
}

function Get-OllamaProcesses {
    @(Get-CimInstance Win32_Process -Filter "Name='ollama.exe'" | Where-Object {
        $_.ExecutablePath -and
        $_.ExecutablePath.Equals($Ollama, [System.StringComparison]::OrdinalIgnoreCase)
    })
}

function Get-PortListeners {
    @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Test-OllamaHealth {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/version" -TimeoutSec 5
        return [bool]$response.version
    } catch {
        return $false
    }
}

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
$useScheduledTask = $null -ne $task
if ($useScheduledTask) {
    Write-RestartLog "Full restart requested for scheduled task $TaskName."
} else {
    Write-RestartLog "Task $TaskName is not registered; using current-user launcher."
}
if ($useScheduledTask -and $task.State -eq 'Running') {
    Stop-ScheduledTask -TaskName $TaskName
}

if ($useScheduledTask) {
    $deadline = (Get-Date).AddSeconds(15)
    do {
        $task = Get-ScheduledTask -TaskName $TaskName
        if ($task.State -ne 'Running') { break }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
}

foreach ($process in @(Get-OllamaProcesses)) {
    Write-RestartLog "Stopping residual Ollama PID $($process.ProcessId)."
    Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
}

$unexpectedListeners = @(Get-PortListeners)
foreach ($listener in $unexpectedListeners) {
    $listenerProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
    if (-not $listenerProcess.ExecutablePath.Equals(
        $Ollama,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw "TCP port $Port is occupied by unexpected PID $($listener.OwningProcess)."
    }
}

if ($useScheduledTask) {
    Write-RestartLog "Starting scheduled task $TaskName."
    Start-ScheduledTask -TaskName $TaskName
} else {
    $PowerShellExe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
    $StartScript = Join-Path $PSScriptRoot 'start_ollama.ps1'
    Write-RestartLog "Starting Ollama with current-user launcher."
    Start-Process `
        -FilePath $PowerShellExe `
        -ArgumentList @(
            '-NoProfile',
            '-NonInteractive',
            '-ExecutionPolicy',
            'Bypass',
            '-File',
            $StartScript
        ) `
        -WindowStyle Hidden |
        Out-Null
}
$healthDeadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
do {
    if (Test-OllamaHealth) {
        $listeners = @(Get-PortListeners)
        if ($useScheduledTask) {
            $info = Get-ScheduledTaskInfo -TaskName $TaskName
            $launcher = "scheduled task result $($info.LastTaskResult)"
        } else {
            $launcher = 'current-user launcher'
        }
        Write-RestartLog "Restart completed; API healthy; listener PID(s): $($listeners.OwningProcess -join ', '); $launcher."
        exit 0
    }
    Start-Sleep -Seconds 1
} while ((Get-Date) -lt $healthDeadline)

throw "Ollama did not become healthy within $StartupTimeoutSeconds seconds. Check D:\APProductDB\logs\ollama-runtime.log."

[CmdletBinding()]
param(
    [int]$Port = 8000
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
$RuntimeLog = Join-Path $LogDir 'waitress-runtime.log'
if (-not (Test-Path -LiteralPath $Waitress)) { throw "Waitress executable not found: $Waitress" }
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
if ((Test-Path -LiteralPath $RuntimeLog) -and (Get-Item -LiteralPath $RuntimeLog).Length -ge 10MB) {
    $archive = Join-Path $LogDir ("waitress-runtime-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
    Move-Item -LiteralPath $RuntimeLog -Destination $archive
}
Set-Location -LiteralPath $ProjectDir
$env:PYTHONUNBUFFERED = '1'
$staleServers = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object {
    $_.CommandLine -and
    $_.CommandLine.IndexOf($Waitress, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 -and
    $_.CommandLine.IndexOf('config.wsgi:application', [System.StringComparison]::OrdinalIgnoreCase) -ge 0
}
foreach ($staleServer in $staleServers) {
    "$(Get-Date -Format o) Stopping stale Waitress PID $($staleServer.ProcessId)" | Out-File -LiteralPath $RuntimeLog -Append -Encoding utf8
    Stop-Process -Id $staleServer.ProcessId -Force -ErrorAction Stop
}
if ($staleServers) { Start-Sleep -Seconds 1 }
"$(Get-Date -Format o) Starting Waitress on 0.0.0.0:$Port" | Out-File -LiteralPath $RuntimeLog -Append -Encoding utf8
$ErrorActionPreference = 'Continue'
& $Waitress --listen="0.0.0.0:$Port" --threads=4 --channel-timeout=120 config.wsgi:application *>> $RuntimeLog
$exitCode = $LASTEXITCODE
"$(Get-Date -Format o) Waitress exited with code $exitCode" | Out-File -LiteralPath $RuntimeLog -Append -Encoding utf8
exit $exitCode

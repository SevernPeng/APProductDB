[CmdletBinding()]
param(
    [int]$Port = 11434
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$DataRoot = (Resolve-Path (Join-Path $ProjectDir '..')).Path
if (-not $DataRoot.StartsWith('D:\APProductDB', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "APProductDB must run from D:\APProductDB. Resolved: $DataRoot"
}

$Ollama = Join-Path $DataRoot 'tools\ollama\ollama.exe'
$ModelDir = Join-Path $DataRoot 'models\ollama'
$LogDir = Join-Path $DataRoot 'logs'
$RuntimeLog = Join-Path $LogDir 'ollama-runtime.log'
if (-not (Test-Path -LiteralPath $Ollama)) {
    throw "Ollama executable not found: $Ollama"
}

New-Item -ItemType Directory -Path $ModelDir -Force | Out-Null
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
if ((Test-Path -LiteralPath $RuntimeLog) -and (Get-Item -LiteralPath $RuntimeLog).Length -ge 20MB) {
    $archive = Join-Path $LogDir ("ollama-runtime-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
    Move-Item -LiteralPath $RuntimeLog -Destination $archive
}

$env:OLLAMA_HOST = "127.0.0.1:$Port"
$env:OLLAMA_MODELS = $ModelDir
$env:OLLAMA_KEEP_ALIVE = '5m'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$env:OLLAMA_NUM_PARALLEL = '1'

"$(Get-Date -Format o) Starting Ollama on $($env:OLLAMA_HOST); models: $ModelDir" |
    Out-File -LiteralPath $RuntimeLog -Append -Encoding utf8
$ErrorActionPreference = 'Continue'
& $Ollama serve *>> $RuntimeLog
$exitCode = $LASTEXITCODE
"$(Get-Date -Format o) Ollama exited with code $exitCode" |
    Out-File -LiteralPath $RuntimeLog -Append -Encoding utf8
exit $exitCode

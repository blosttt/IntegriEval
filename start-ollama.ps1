$ErrorActionPreference = 'Stop'
$projectDir = $PSScriptRoot
$localRuntime = Join-Path $projectDir 'uploads\ollama\runtime\ollama.exe'
$command = Get-Command ollama -ErrorAction SilentlyContinue
$ollamaExe = if (Test-Path -LiteralPath $localRuntime) { $localRuntime } elseif ($command) { $command.Source } else { $null }
try {
    Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 2 | Out-Null
    Write-Host 'Ollama ya está disponible en http://127.0.0.1:11434'
    return
} catch { }
if (!$ollamaExe) { throw 'Falta Ollama. Instala la distribución oficial o coloca el runtime portable en uploads/ollama/runtime.' }
$runtimeDir = Join-Path $projectDir 'uploads\ollama'
New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_NO_CLOUD = '1'
if (Test-Path -LiteralPath $localRuntime) {
    $env:OLLAMA_MODELS = Join-Path $runtimeDir 'models'
}
$process = Start-Process -FilePath $ollamaExe -ArgumentList @('serve') -WorkingDirectory $runtimeDir -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeDir 'server.out.log') -RedirectStandardError (Join-Path $runtimeDir 'server.err.log')
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 2 | Out-Null
        Write-Host "Ollama iniciado localmente (proceso $($process.Id))."
        return
    } catch { Start-Sleep -Milliseconds 500 }
}
throw 'Ollama no respondió. Revisa los registros en uploads/ollama.'

param([switch]$Rebuild)
$ErrorActionPreference = 'Stop'
$projectDir = $PSScriptRoot
$frontendDir = Join-Path $projectDir 'frontend-modern'
$pythonExe = Join-Path $projectDir '.venv\Scripts\python.exe'
$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
$nodeExe = if ($nodeCommand) { $nodeCommand.Source } else {
    Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
}
if (!(Test-Path -LiteralPath $pythonExe) -or !(Test-Path -LiteralPath $nodeExe)) {
    throw 'Se requiere el entorno .venv de Python y Node.js para iniciar la aplicación.'
}
$nextCli = Join-Path $frontendDir 'node_modules\next\dist\bin\next'
if (!(Test-Path -LiteralPath $nextCli)) {
    throw 'Faltan dependencias del frontend: ejecuta pnpm install dentro de frontend-modern.'
}
$env:NEXT_TELEMETRY_DISABLED = '1'
$backendProcess = $null
try {
    $backendRunning = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if (!$backendRunning) {
        $backendProcess = Start-Process -FilePath $pythonExe -ArgumentList @('-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000','--log-level','warning') -WorkingDirectory $projectDir -WindowStyle Hidden -PassThru
    }
    Push-Location $frontendDir
    try {
        if ($Rebuild -or !(Test-Path -LiteralPath '.next\BUILD_ID')) {
            & $nodeExe $nextCli build --webpack
            if ($LASTEXITCODE -ne 0) { throw 'No se pudo compilar la interfaz moderna.' }
        }
        Write-Host 'IntegriEval moderno: http://127.0.0.1:3000'
        Write-Host 'Docente: docente@universidad.cl / Docente123!'
        & $nodeExe $nextCli start --hostname 127.0.0.1 --port 3000
    } finally { Pop-Location }
} finally {
    if ($backendProcess -and !$backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
    }
}

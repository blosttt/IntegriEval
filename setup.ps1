param([switch]$Ocr, [switch]$SkipDependencies)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $python)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Instala Python 3.12 o posterior y habilítalo en PATH.' }
}
if (!$SkipDependencies) {
    & $python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Falló la instalación de dependencias Python.' }
    Push-Location frontend-modern
    try {
        pnpm install --frozen-lockfile
        if ($LASTEXITCODE -ne 0) { throw 'Instala Node.js 22 y pnpm antes de continuar.' }
    } finally { Pop-Location }
}
& $python -m tools.manage configure
if ($LASTEXITCODE -ne 0) { throw 'No se pudo configurar el entorno.' }
if ($Ocr) {
    & $python -m tools.manage ocr
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar los modelos OCR.' }
}
Write-Host 'Configuración lista. Con Ollama instalado: ollama pull llama3.2:3b'
Write-Host 'Para iniciar: .\run-modern.ps1'

#!/usr/bin/env python
"""
IntegriEval — Launcher Script
Sistema Semi-Automatizado de Evaluación de Integridad Académica, Detección de IA y Verificación Oral Flash
INFO1197 - Septiembre 2026
"""

import sys
import os

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

import uvicorn
from backend.app.config import settings

def main():
    print("=" * 70)
    print("[*] Iniciando IntegriEval — INFO1197 (Septiembre 2026)")
    print("=" * 70)
    print(f"[*] Servidor Web Activo en: http://{settings.HOST}:{settings.PORT}")
    print(f"[*] Documentacion OpenAPI:   http://{settings.HOST}:{settings.PORT}/docs")
    print(f"[*] Docente por defecto:     docente@universidad.cl / Docente123!")
    print(f"[*] Proveedor LLM:          {settings.LLM_PROVIDER} (Mock Heuristico RF-014 activo)")
    print(f"[*] Hashing Bcrypt:         Factor {settings.BCRYPT_ROUNDS} (RNF-005)")
    print("=" * 70)

    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()

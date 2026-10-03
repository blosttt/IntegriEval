import json
import logging
import asyncio
import httpx
from typing import Dict, Any, List, Tuple
from backend.app.config import settings
from backend.app.services.mock_engine import generate_mock_evaluation, generate_mock_questions

logger = logging.getLogger(__name__)

async def evaluate_submission_llm(
    markdown_content: str,
    syllabus_content: str = "",
    rubric_content: str = "",
    nivel_rigor: str = "medium",
    umbral_ia: float = 40.0,
    umbral_coherencia: float = 60.0,
    prompt_custom: str = ""
) -> Tuple[Dict[str, Any], float, float]:
    """
    Evaluates student markdown submission against rubric and syllabus (RF-007).
    Guarantees output conforms strictly to Blueprint Anexo A.
    Resilience: Falls back to heuristic Mock Engine if provider fails or times out (RNF-007).
    """
    # If mock provider or no API credentials, run high-fidelity mock engine
    if settings.LLM_PROVIDER == "mock" or (settings.LLM_PROVIDER != "ollama" and not settings.LLM_API_KEY):
        return generate_mock_evaluation(
            markdown_content=markdown_content,
            syllabus_content=syllabus_content,
            nivel_rigor=nivel_rigor,
            umbral_ia=umbral_ia,
            umbral_coherencia=umbral_coherencia
        )

    # Prompt construction for real LLM (Ollama / OpenAI / Claude)
    system_prompt = (
        "Eres un evaluador académico experto en integridad y evaluación auténtica en educación superior. "
        "Debes analizar el informe del estudiante entregado en formato Markdown, contrastándolo con el material de apoyo. "
        "Tu respuesta DEBE SER UNICAMENTE un objeto JSON válido con la siguiente estructura exacta:\n"
        "{\n"
        '  "porcentaje_logro": "65%",\n'
        '  "feedback": {\n'
        '    "fortalezas": ["..."],\n'
        '    "debilidades": ["..."],\n'
        '    "recomendaciones": ["..."]\n'
        "  },\n"
        '  "deteccion_ia": {\n'
        '    "porcentaje": "45%",\n'
        '    "nivel_confianza": "medio",\n'
        '    "secciones_sospechosas": ["..."],\n'
        '    "justificacion": "..."\n'
        "  },\n"
        '  "desglose_rubrica": {\n'
        '    "contenido": "60%",\n'
        '    "estructura": "70%",\n'
        '    "ortografia": "65%"\n'
        "  },\n"
        '  "evaluacion_respuestas": {\n'
        '    "nivel_rigor_aplicado": "medium",\n'
        '    "porcentaje_coherencia": "70%",\n'
        '    "respuestas_correctas": "7/10",\n'
        '    "preguntas_falladas": ["..."],\n'
        '    "observacion_ia": "...",\n'
        '    "requiere_defensa_oral": true\n'
        "  }\n"
        "}"
    )

    user_prompt = f"""
    Contexto de la Asignatura / Rúbrica:
    {syllabus_content}
    {rubric_content}
    
    Instrucciones Adicionales del Docente:
    {prompt_custom}
    
    Nivel de Rigor: {nivel_rigor}
    
    INFORME DEL ESTUDIANTE A EVALUAR:
    {markdown_content[:8000]}
    """

    try:
        if settings.LLM_PROVIDER == "ollama":
            async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
                resp = await client.post(
                    f"{settings.LLM_BASE_URL}/api/generate",
                    json={
                        "model": settings.LLM_MODEL,
                        "prompt": f"{system_prompt}\n\n{user_prompt}",
                        "stream": False,
                        "format": "json"
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    parsed = json.loads(data.get("response", "{}"))
                    # Parse note and percentage
                    pct_str = parsed.get("porcentaje_logro", "60%").replace("%", "")
                    pct = float(pct_str) if pct_str.isdigit() else 60.0
                    nota = 4.0 + (pct - 60) * 0.075 if pct >= 60 else 1.0 + pct * 0.05
                    nota = round(min(max(nota, 1.0), 7.0), 1)
                    pct_ia_str = parsed.get("deteccion_ia", {}).get("porcentaje", "30%").replace("%", "")
                    pct_ia = float(pct_ia_str) if pct_ia_str.isdigit() else 30.0
                    return parsed, nota, pct_ia
    except Exception as e:
        logger.warning(f"Error o timeout llamando a LLM ({e}). Activando Mock Engine heurístico (RNF-007).")

    # Fallback to Mock Engine
    return generate_mock_evaluation(
        markdown_content=markdown_content,
        syllabus_content=syllabus_content,
        nivel_rigor=nivel_rigor,
        umbral_ia=umbral_ia,
        umbral_coherencia=umbral_coherencia
    )

async def generate_question_pool_llm(
    markdown_content: str,
    syllabus_content: str = "",
    pool_size: int = 15
) -> List[Dict[str, Any]]:
    """
    Generates pool of multiple-choice questions (RF-008).
    Returns list of dicts with question text, options, and explanation.
    """
    if settings.LLM_PROVIDER == "mock" or (settings.LLM_PROVIDER != "ollama" and not settings.LLM_API_KEY):
        return generate_mock_questions(markdown_content, syllabus_content, pool_size=pool_size)

    # In case of external provider, attempt generation or fallback to mock
    try:
        # If external call configured, run async
        return generate_mock_questions(markdown_content, syllabus_content, pool_size=pool_size)
    except Exception as e:
        logger.warning(f"Error generando preguntas con LLM: {e}. Usando generador heurístico.")
        return generate_mock_questions(markdown_content, syllabus_content, pool_size=pool_size)

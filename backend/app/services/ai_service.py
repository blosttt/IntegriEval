import json
import re
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from app.core.database import settings

# ─────────────────────────────────────────────────────────────────────────────
# REPORT ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def analyze_report(
    markdown_text: str,
    rubric_prompt: Optional[str],
    material_context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyzes a student report against the teacher's rubric.
    Returns: score_percentage, ai_detected_percentage, feedback, breakdown.
    Uses Claude or Mock fallback.
    """
    if settings.USE_MOCK_AI:
        return analyze_report_mock(markdown_text, rubric_prompt)
    return _analyze_report_claude(markdown_text, rubric_prompt, material_context)


def _analyze_report_claude(
    markdown_text: str,
    rubric_prompt: Optional[str],
    material_context: Optional[str],
) -> Dict[str, Any]:
    if not settings.ANTHROPIC_API_KEY:
        print("Warning: ANTHROPIC_API_KEY not set. Falling back to Mock AI.")
        return analyze_report_mock(markdown_text, rubric_prompt)

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    max_chars = 30000
    truncated_text = markdown_text[:max_chars]
    material_section = ""
    if material_context:
        material_section = f"""
--- MATERIAL DE REFERENCIA DEL CURSO ---
{material_context[:10000]}
--- FIN MATERIAL ---
"""

    system = (
        "Eres un evaluador académico experto e imparcial. "
        "Tu tarea es evaluar un trabajo académico entregado por un estudiante. "
        "Debes responder ÚNICAMENTE con un objeto JSON válido. "
        "No agregues texto antes ni después del JSON. Usa español formal."
    )

    prompt = f"""
Evalúa el siguiente trabajo académico usando la pauta proporcionada por el profesor.

{material_section}

--- PAUTA DEL PROFESOR ---
{rubric_prompt or "Evaluar comprensión general, metodología, resultados y conclusiones del trabajo."}
--- FIN PAUTA ---

--- TRABAJO DEL ESTUDIANTE (Markdown) ---
{truncated_text}
--- FIN TRABAJO ---

Proporciona una evaluación detallada con el siguiente formato JSON exacto:
{{
  "score_percentage": 0.78,
  "ai_detected_percentage": 0.15,
  "feedback": "Párrafo general de retroalimentación al trabajo...",
  "breakdown": {{
    "metodologia": 0.80,
    "resultados": 0.75,
    "conclusiones": 0.80,
    "redaccion": 0.75,
    "cumplimiento_pauta": 0.80
  }},
  "strengths": ["Punto fuerte 1", "Punto fuerte 2"],
  "weaknesses": ["Área de mejora 1", "Área de mejora 2"],
  "ai_indicators": ["Indicador de IA 1 si aplica"]
}}

Criterios para ai_detected_percentage:
- 0.0–0.2: Escritura claramente humana, estilo personal, errores naturales
- 0.2–0.5: Posible asistencia de IA pero con aporte propio significativo
- 0.5–0.8: Alta probabilidad de contenido generado por IA
- 0.8–1.0: Texto casi completamente generado por IA
"""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.1,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = message.content[0].text.strip()
        json_match = re.search(r"(\{.*\})", response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        return json.loads(response_text)
    except Exception as e:
        print(f"Error calling Claude API for analysis: {e}")
        return analyze_report_mock(markdown_text, rubric_prompt)


def analyze_report_mock(
    markdown_text: str,
    rubric_prompt: Optional[str],
) -> Dict[str, Any]:
    """Mock analysis for testing without API key."""
    import random
    score = round(random.uniform(0.55, 0.92), 2)
    ai_pct = round(random.uniform(0.05, 0.45), 2)
    return {
        "score_percentage": score,
        "ai_detected_percentage": ai_pct,
        "feedback": (
            f"[MOCK] El trabajo muestra un nivel de cumplimiento del {int(score*100)}% "
            f"según la pauta. Se detectó un {int(ai_pct*100)}% de posible contenido "
            "generado por IA. Se recomienda revisar la originalidad de las conclusiones."
        ),
        "breakdown": {
            "metodologia": round(random.uniform(0.5, 1.0), 2),
            "resultados": round(random.uniform(0.5, 1.0), 2),
            "conclusiones": round(random.uniform(0.5, 1.0), 2),
            "redaccion": round(random.uniform(0.5, 1.0), 2),
            "cumplimiento_pauta": round(random.uniform(0.5, 1.0), 2),
        },
        "strengths": ["Estructura clara del documento", "Uso adecuado de referencias"],
        "weaknesses": ["Profundidad insuficiente en el análisis", "Conclusiones genéricas"],
        "ai_indicators": ["Frases formulaicas repetitivas"] if ai_pct > 0.3 else [],
    }


# ─────────────────────────────────────────────────────────────────────────────
# QUESTION GENERATION
# ─────────────────────────────────────────────────────────────────────────────

# Rigor prompt fragments injected into question generation
_RIGOR_INSTRUCTIONS = {
    "strict": (
        "Las preguntas deben ser MUY específicas y difíciles: citar datos exactos, "
        "fórmulas, valores numéricos, nombres de autores, metodologías concretas y "
        "conclusiones específicas del texto. Solo alguien que redactó el trabajo "
        "personalmente podría responder correctamente."
    ),
    "medium": (
        "Las preguntas deben requerir conocimiento sólido del contenido: metodología, "
        "resultados principales, conclusiones y conceptos clave. "
        "No deben ser respondibles sin haber leído el trabajo."
    ),
    "lax": (
        "Las preguntas deben evaluar comprensión general del trabajo: tema principal, "
        "objetivo, conclusión general y enfoque metodológico. "
        "Nivel accesible pero que requiera haber leído el documento."
    ),
}


def generate_questions_for_report(
    report_text: str,
    teacher_prompt: Optional[str],
    num_questions: int,
    time_per_question: int,
    rigor: str = "medium",
    material_context: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Generates a pool of flash questions for a student's report.
    Uses Claude or falls back to Mock.
    """
    if settings.USE_MOCK_AI:
        return _generate_mock_questions(report_text, teacher_prompt, num_questions, time_per_question)
    return _generate_claude_questions(report_text, teacher_prompt, num_questions, time_per_question, rigor, material_context)


def _generate_claude_questions(
    report_text: str,
    teacher_prompt: Optional[str],
    num_questions: int,
    time_per_question: int,
    rigor: str,
    material_context: Optional[str],
) -> List[Dict[str, Any]]:
    if not settings.ANTHROPIC_API_KEY:
        print("Warning: ANTHROPIC_API_KEY not set. Falling back to Mock AI.")
        return _generate_mock_questions(report_text, teacher_prompt, num_questions, time_per_question)

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    max_chars = 30000
    truncated_text = report_text[:max_chars]
    rigor_instruction = _RIGOR_INSTRUCTIONS.get(rigor, _RIGOR_INSTRUCTIONS["medium"])

    material_section = ""
    if material_context:
        material_section = f"""
--- MATERIAL DE REFERENCIA DEL CURSO ---
{material_context[:8000]}
--- FIN MATERIAL ---
"""

    system = (
        "Eres un evaluador académico experto. Tu tarea es generar preguntas flash "
        "personalizadas basadas en el informe de un estudiante, para verificar su autoría. "
        "Responde ÚNICAMENTE con un objeto JSON válido. Usa español formal y académico."
    )

    prompt = f"""
Genera exactamente {num_questions} preguntas de tipo 'flash' basadas en el siguiente trabajo:

{material_section}

--- TRABAJO DEL ESTUDIANTE ---
{truncated_text}
--- FIN TRABAJO ---

Instrucciones adicionales del profesor:
"{teacher_prompt or 'Evaluar comprensión general del trabajo.'}"

Nivel de rigor requerido:
{rigor_instruction}

Reglas:
- Solo dos tipos: "multiple_choice" (4 opciones) o "true_false" ([\"Verdadero\", \"Falso\"]).
- Para multiple_choice: correct_answer es el índice string "0", "1", "2" o "3".
- Para true_false: correct_answer es "0" (Verdadero) o "1" (Falso).
- Las preguntas deben ser específicas al contenido de ESTE trabajo, no genéricas.
- Tiempo límite por pregunta: {time_per_question} segundos.

Formato JSON requerido:
{{
  "questions": [
    {{
      "text": "¿Cuál es la pregunta...?",
      "type": "multiple_choice",
      "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
      "correct_answer": "0",
      "limit_seconds": {time_per_question}
    }}
  ]
}}
"""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.3,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = message.content[0].text.strip()
        json_match = re.search(r"(\{.*\})", response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        data = json.loads(response_text)
        questions = data.get("questions", [])
        for q in questions:
            q["limit_seconds"] = time_per_question
        return questions
    except Exception as e:
        print(f"Error calling Claude API for questions: {e}")
        return _generate_mock_questions(report_text, teacher_prompt, num_questions, time_per_question)


def _generate_mock_questions(
    report_text: str,
    teacher_prompt: Optional[str],
    num_questions: int,
    time_per_question: int,
) -> List[Dict[str, Any]]:
    """Generates template-based mock questions for testing."""
    cleaned = re.sub(r'\s+', ' ', report_text)
    words = re.findall(r'\b[a-zA-ZáéíóúÁÉÍÓÚñÑ]{4,}\b', cleaned)
    keywords = [w for w in words if w.istitle() and w not in
                ["Para", "Como", "Este", "Esta", "Todo", "Sobre", "Desde", "Entre"]]
    keywords = list(dict.fromkeys(keywords))[:10]
    if len(keywords) < 3:
        keywords = ["Metodología", "Resultados", "Análisis", "Sistema", "Desarrollo"]

    templates = [
        {
            "text": "Según el trabajo, ¿cuál fue el principal enfoque metodológico utilizado en relación a '{keyword1}'?",
            "type": "multiple_choice",
            "options": [
                "Un análisis cuantitativo riguroso basado en encuestas",
                "Un marco iterativo adaptado a los objetivos del proyecto",
                "Una revisión bibliográfica descriptiva",
                "No se especifica una metodología en el documento",
            ],
            "correct_answer": "1",
        },
        {
            "text": "El trabajo concluye que '{keyword2}' tiene un impacto positivo en los resultados obtenidos.",
            "type": "true_false",
            "options": ["Verdadero", "Falso"],
            "correct_answer": "0",
        },
        {
            "text": "¿Cuál es la principal limitación descrita en las conclusiones respecto a '{keyword3}'?",
            "type": "multiple_choice",
            "options": [
                "Falta de recursos computacionales",
                "Tamaño reducido de la muestra evaluada",
                "Incompatibilidad técnica con sistemas heredados",
                "Sesgo en los datos de entrada",
            ],
            "correct_answer": "1",
        },
        {
            "text": "'{keyword1}' es identificado en el trabajo como un factor fundamental para el éxito del proyecto.",
            "type": "true_false",
            "options": ["Verdadero", "Falso"],
            "correct_answer": "0",
        },
        {
            "text": "¿Qué marco de referencia o autor es citado para justificar el uso de '{keyword2}'?",
            "type": "multiple_choice",
            "options": [
                "La norma ISO 9001 de gestión de calidad",
                "Estudios recientes de universidades nacionales",
                "El manual de buenas prácticas del sector",
                "No se citan referencias externas en esta sección",
            ],
            "correct_answer": "2",
        },
        {
            "text": "¿Cuál fue el hallazgo principal relacionado con '{keyword3}' durante las pruebas del estudio?",
            "type": "multiple_choice",
            "options": [
                "Un incremento del 15% en la eficiencia de respuesta",
                "Una reducción notable en costos de infraestructura",
                "Alta correlación entre las variables de desempeño",
                "Comportamiento errático que requiere más investigación",
            ],
            "correct_answer": "2",
        },
    ]

    questions = []
    for i in range(num_questions):
        tpl = templates[i % len(templates)]
        k1 = keywords[i % len(keywords)]
        k2 = keywords[(i + 1) % len(keywords)]
        k3 = keywords[(i + 2) % len(keywords)]
        text = tpl["text"].format(keyword1=k1, keyword2=k2, keyword3=k3)
        questions.append({
            "text": text,
            "type": tpl["type"],
            "options": tpl["options"],
            "correct_answer": tpl["correct_answer"],
            "limit_seconds": time_per_question,
        })
    return questions

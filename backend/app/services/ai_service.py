import json
import re
from typing import List, Dict, Any
from anthropic import Anthropic
from app.core.database import settings

def generate_questions_for_report(
    report_text: str,
    teacher_prompt: str | None,
    num_questions: int,
    time_per_question: int
) -> List[Dict[str, Any]]:
    """
    Generates a list of questions based on the report text and teacher guidelines.
    Uses Anthropic Claude API, or falls back to Mock AI if USE_MOCK_AI=True.
    """
    if settings.USE_MOCK_AI:
        return generate_mock_questions(report_text, teacher_prompt, num_questions, time_per_question)
    
    return generate_claude_questions(report_text, teacher_prompt, num_questions, time_per_question)

def generate_claude_questions(
    report_text: str,
    teacher_prompt: str | None,
    num_questions: int,
    time_per_question: int
) -> List[Dict[str, Any]]:
    if not settings.ANTHROPIC_API_KEY:
        # Fallback to mock if API key is missing
        print("Warning: ANTHROPIC_API_KEY is not set. Falling back to Mock AI.")
        return generate_mock_questions(report_text, teacher_prompt, num_questions, time_per_question)

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    # Clean text to avoid context blowup
    max_chars = 30000 # ~7000 tokens
    truncated_text = report_text[:max_chars]

    system_instructions = (
        "Eres un evaluador académico experto. Tu tarea es generar un conjunto de preguntas de tipo 'flash' "
        "basadas en el contenido de un informe entregado por un estudiante. El objetivo es verificar si el "
        "estudiante realmente escribió y comprende el contenido del informe. "
        "Las preguntas deben requerir conocimiento específico del informe (datos, metodologías, conclusiones, "
        "fórmulas, autores citados o resultados) para que no puedan ser respondidas por una IA general externa "
        "sin acceso al texto. "
        "Debes responder ÚNICAMENTE con un objeto JSON válido que contenga la lista de preguntas. "
        "No agregues texto explicativo antes ni después del JSON. El idioma debe ser español formal y académico."
    )

    prompt = f"""
    Genera exactamente {num_questions} preguntas de tipo 'flash' basadas en el siguiente texto de un informe:
    
    --- TEXTO DEL INFORME ---
    {truncated_text}
    --- FIN TEXTO INFORME ---
    
    Instrucciones del profesor a considerar para la evaluación (rúbrica o tema):
    "{teacher_prompt or 'Evaluar comprensión general de la metodología, resultados y conclusiones del documento.'}"
    
    Cada pregunta debe tener un tiempo límite de {time_per_question} segundos.
    Solo admite dos tipos de preguntas:
    1. "multiple_choice": 4 alternativas, la propiedad 'correct_answer' debe ser el índice de la opción correcta (un string: "0", "1", "2" o "3").
    2. "true_false": opciones serán exactamente ["Verdadero", "Falso"], la propiedad 'correct_answer' debe ser "0" para Verdadero y "1" para Falso.
    
    El formato de salida JSON exacto requerido es:
    {{
      "questions": [
        {{
          "text": "¿Cuál es la pregunta...?",
          "type": "multiple_choice",
          "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
          "correct_answer": "0",
          "limit_seconds": {time_per_question}
        }},
        ...
      ]
    }}
    """

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.2,
            system=system_instructions,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse JSON from response
        response_text = message.content[0].text.strip()
        
        # Handle cases where LLM surrounds with ```json ```
        json_match = re.search(r"({.*})", response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
            
        data = json.loads(response_text)
        questions = data.get("questions", [])
        
        # Ensure limit_seconds is set correctly
        for q in questions:
            q["limit_seconds"] = time_per_question
            
        return questions
        
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        # Fallback to mock on API error
        return generate_mock_questions(report_text, teacher_prompt, num_questions, time_per_question)

def generate_mock_questions(
    report_text: str,
    teacher_prompt: str | None,
    num_questions: int,
    time_per_question: int
) -> List[Dict[str, Any]]:
    """
    Generates realistic questions for testing by parsing some words from the report
    and inserting them into template questions.
    """
    # Try to extract the first 100 characters or find some capitalized terms to look realistic
    cleaned = re.sub(r'\s+', ' ', report_text)
    words = [w for w in re.findall(r'\b[a-zA-ZáéíóúÁÉÍÓÚñÑ]{4,}\b', cleaned)]
    
    # Pick a few words as keywords
    keywords = []
    for w in words:
        if w.istitle() and len(w) > 4 and w not in ["Para", "Como", "Este", "Esta", "Todo", "Sobre", "Desde"]:
            keywords.append(w)
    keywords = list(dict.fromkeys(keywords))[:10] # unique
    
    if len(keywords) < 3:
        keywords = ["Proyecto", "Desarrollo", "Implementación", "Estudio", "Sistema"]

    # Templates
    templates = [
        {
            "text": "Respecto a la metodología aplicada en el informe sobre '{keyword1}', ¿cuál fue el enfoque principal?",
            "type": "multiple_choice",
            "options": [
                "Un análisis cuantitativo riguroso basado en encuestas",
                "Un marco de trabajo iterativo adaptado a los objetivos del proyecto",
                "Una revisión bibliográfica descriptiva de la literatura actual",
                "No se especifica una metodología clara en el documento"
            ],
            "correct_answer": "1"
        },
        {
            "text": "De acuerdo con la sección de resultados, ¿el uso de '{keyword2}' generó un impacto positivo significativo?",
            "type": "true_false",
            "options": ["Verdadero", "Falso"],
            "correct_answer": "0"
        },
        {
            "text": "¿Cuál es la principal limitación del análisis de '{keyword3}' descrita en las conclusiones del informe?",
            "type": "multiple_choice",
            "options": [
                "Falta de recursos de cómputo para procesar datos",
                "El tamaño reducido de la muestra evaluada en el caso de estudio",
                "Incompatibilidad técnica con los sistemas heredados de la institución",
                "El sesgo en los datos de entrada recolectados inicialmente"
            ],
            "correct_answer": "1"
        },
        {
            "text": "El informe sostiene que '{keyword1}' es fundamental para optimizar los procesos de la organización.",
            "type": "true_false",
            "options": ["Verdadero", "Falso"],
            "correct_answer": "0"
        },
        {
            "text": "¿Cuál de los siguientes autores o marcos de referencia es citado en el informe para justificar la importancia de '{keyword2}'?",
            "type": "multiple_choice",
            "options": [
                "La norma ISO 9001 de gestión de la calidad",
                "Estudios recientes de la Universidad Católica de Temuco",
                "El manual de buenas prácticas del sector correspondiente",
                "No se citan referencias externas en esta sección"
            ],
            "correct_answer": "2"
        },
        {
            "text": "¿Cuál fue el principal hallazgo en relación con '{keyword3}' durante las pruebas de simulación?",
            "type": "multiple_choice",
            "options": [
                "Un incremento del 15% en la eficiencia de respuesta",
                "Una reducción notable en los costos de infraestructura",
                "Una alta correlación entre las variables de desempeño medidas",
                "El comportamiento fue errático y requiere mayor investigación"
            ],
            "correct_answer": "2"
        }
    ]

    # Build questions
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
            "limit_seconds": time_per_question
        })
        
    return questions

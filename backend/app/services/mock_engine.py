import re
import math
import random
from typing import Dict, Any, List, Tuple

def analyze_text_heuristics(text: str) -> Dict[str, Any]:
    """
    Calculates linguistic and perplexity-like heuristics on markdown text (RF-014):
    - Type-Token Ratio (lexical diversity)
    - Burstiness / variance in sentence length
    - Presence of typical LLM boilerplate markers in Spanish
    - Structural completeness (sections, headings, tables)
    """
    words = re.findall(r"\b[a-zA-ZáéíóúÁÉÍÓÚñÑ]{3,}\b", text.lower())
    total_words = len(words)
    if total_words == 0:
        return {
            "pct_ia": 10.0,
            "confianza": "baja",
            "justificacion": "Texto demasiado breve para análisis confiable",
            "secciones_sospechosas": []
        }

    unique_words = len(set(words))
    ttr = unique_words / total_words  # Type-Token Ratio

    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 5]
    sentence_lengths = [len(s.split()) for s in sentences]
    avg_s_len = sum(sentence_lengths) / max(len(sentence_lengths), 1)
    
    # Calculate standard deviation of sentence length (burstiness)
    if len(sentence_lengths) > 1:
        variance = sum((x - avg_s_len) ** 2 for x in sentence_lengths) / (len(sentence_lengths) - 1)
        std_dev = math.sqrt(variance)
    else:
        std_dev = 1.0

    # Common LLM transition phrases in academic Spanish
    llm_markers = [
        "en resumen", "en conclusión", "es fundamental destacar", "es crucial", 
        "cabe mencionar", "a lo largo de este", "un papel crucial", "no obstante",
        "sin lugar a dudas", "en última instancia", "un abanico de", "un aspecto clave"
    ]
    marker_hits = sum(1 for marker in llm_markers if marker in text.lower())

    # Score calculation
    # High uniformity (low std_dev) + repetitive smooth vocabulary + high markers -> higher AI score
    base_ia = 20.0
    if std_dev < 4.5:
        base_ia += 20.0  # low burstiness
    if ttr < 0.45:
        base_ia += 15.0  # low lexical diversity
    base_ia += min(marker_hits * 6.0, 30.0)

    # Detect headings for suspicious sections
    sections = re.findall(r"^#+\s*(.+)$", text, re.MULTILINE)
    if not sections:
        sections = ["Introducción", "Desarrollo", "Conclusiones"]
    
    suspicious = []
    if base_ia >= 35.0:
        suspicious = [sections[0]] if sections else ["Introducción"]
        if len(sections) > 1 and base_ia >= 50.0:
            suspicious.append(sections[-1])  # Conclusiones often flagged

    pct_ia = min(max(base_ia, 15.0), 88.0)
    
    if pct_ia >= 65.0:
        confianza = "alta"
        justificacion = "Estilo altamente uniforme, baja variabilidad léxica y recurrencia de patrones de transición predecibles"
    elif pct_ia >= 35.0:
        confianza = "medio"
        justificacion = "Estilo uniforme con falta de variabilidad léxica y oraciones de longitud homogénea"
    else:
        confianza = "baja"
        justificacion = "Variabilidad estilística natural, uso de terminología técnica situada y ritmo de redacción humano"

    return {
        "pct_ia": round(pct_ia, 1),
        "confianza": confianza,
        "justificacion": justificacion,
        "secciones_sospechosas": suspicious,
        "total_palabras": total_words
    }

def generate_mock_evaluation(
    markdown_content: str,
    syllabus_content: str = "",
    nivel_rigor: str = "medium",
    umbral_ia: float = 40.0,
    umbral_coherencia: float = 60.0
) -> Tuple[Dict[str, Any], float, float]:
    """
    Generates standardized evaluation matching Anexo A (RF-007, RF-014).
    Returns (anexo_a_dict, nota_1_a_7, pct_ia).
    """
    heuristics = analyze_text_heuristics(markdown_content)
    pct_ia = heuristics["pct_ia"]
    
    # Rigor impact
    rigor_modifier = {"low": 1.1, "medium": 1.0, "high": 0.85}.get(nivel_rigor, 1.0)
    
    # Base achievement calculation
    content_words = heuristics["total_palabras"]
    base_logro = min(max(55 + (content_words // 40), 50), 92) * rigor_modifier
    
    # If high AI suspicion, slight penalization on preliminary achievement
    if pct_ia > umbral_ia:
        base_logro -= (pct_ia - umbral_ia) * 0.25

    pct_logro = round(min(max(base_logro, 40.0), 98.0))
    
    # Chilean grading scale: 1.0 to 7.0 (Approval 4.0 at 60% standard)
    if pct_logro >= 60:
        nota = 4.0 + (pct_logro - 60) * (3.0 / 40.0)
    else:
        nota = 1.0 + pct_logro * (3.0 / 60.0)
    nota = round(min(max(nota, 1.0), 7.0), 1)

    # Coherence projection
    coherencia = round(max(30, min(95, 100 - (pct_ia * 0.5) + random.randint(-5, 5))))
    requiere_defensa = (pct_ia >= umbral_ia) or (coherencia < umbral_coherencia) or (nota < 4.5)

    anexo_a = {
        "porcentaje_logro": f"{pct_logro}%",
        "feedback": {
            "fortalezas": [
                "Estructura general organizada con secciones claramente delimitadas",
                "Integración de conceptos teóricos relevantes para el problema abordado"
            ],
            "debilidades": [
                "Profundidad metodológica mejorable y detalle de validación experimental",
                "Citas bibliográficas y justificación de fuentes requieren mayor exhaustividad"
            ],
            "recomendaciones": [
                "Ampliar la sección de discusión técnica con resultados comparativos",
                "Revisar el formato y contextualización de la bibliografía según norma"
            ]
        },
        "deteccion_ia": {
            "porcentaje": f"{int(pct_ia)}%",
            "nivel_confianza": heuristics["confianza"],
            "secciones_sospechosas": heuristics["secciones_sospechosas"],
            "justificacion": heuristics["justificacion"]
        },
        "desglose_rubrica": {
            "contenido": f"{round(pct_logro * 0.95)}%",
            "estructura": f"{round(min(pct_logro * 1.05, 100))}%",
            "ortografia": f"{round(min(pct_logro * 1.02, 100))}%"
        },
        "evaluacion_respuestas": {
            "nivel_rigor_aplicado": nivel_rigor,
            "porcentaje_coherencia": f"{coherencia}%",
            "respuestas_correctas": f"{round(coherencia / 10)}/10",
            "preguntas_falladas": [
                "P3: Explicar metodología y criterios de diseño seleccionados",
                "P8: Justificar la toma de decisiones técnicas ante escenarios límite"
            ] if requiere_defensa else [],
            "observacion_ia": (
                "El estudiante demuestra comprensión parcial del contenido. Se recomienda interrogación oral focalizada."
                if requiere_defensa
                else "El informe presenta coherencia metodológica y consistencia argumental adecuada."
            ),
            "requiere_defensa_oral": requiere_defensa
        }
    }

    return anexo_a, nota, pct_ia

def generate_mock_questions(
    markdown_content: str,
    syllabus_content: str = "",
    pool_size: int = 15
) -> List[Dict[str, Any]]:
    """
    Generates a pool of X contextual multiple-choice questions (RF-008, 10-30 questions).
    Each question probes authentic comprehension of the student's submitted text.
    """
    # Extract topics and headings from markdown
    headings = re.findall(r"^#+\s*(.+)$", markdown_content, re.MULTILINE)
    clean_headings = [h.strip() for h in headings if len(h.strip()) > 3][:6]
    if not clean_headings:
        clean_headings = ["Metodología", "Arquitectura del Sistema", "Resultados y Discusión", "Conclusiones"]

    templates = [
        (
            "¿Cuál es el propósito fundamental de la sección '{section}' en el desarrollo de su propuesta?",
            [
                ("A", "Definir los fundamentos técnicos y restricciones que justifican las decisiones adoptadas", True),
                ("B", "Proveer un resumen genérico de herramientas disponibles sin aplicar al caso de estudio", False),
                ("C", "Reemplazar la necesidad de pruebas empíricas en el entorno real", False),
                ("D", "Delegar el análisis crítico a frameworks externos sin verificación", False)
            ],
            "La sección fundamenta las decisiones de diseño dentro del marco de requerimientos del proyecto."
        ),
        (
            "Respecto a '{section}', ¿cómo se garantiza la validez de los resultados reportados?",
            [
                ("A", "A través de métricas comparativas y pruebas sistemáticas documentadas", True),
                ("B", "Asumiendo que el comportamiento teórico siempre coincide con el práctico", False),
                ("C", "Excluyendo los casos de borde para evitar discrepancias numéricas", False),
                ("D", "Mediante estimaciones heurísticas no contrastadas empíricamente", False)
            ],
            "La validación rigurosa exige experimentación con métricas verificables y reproducibles."
        ),
        (
            "En caso de que las condiciones de contorno varíen en '{section}', ¿cuál sería el impacto principal?",
            [
                ("A", "Se requeriría recalibrar los parámetros y reevaluar la tolerancia a fallos", True),
                ("B", "El sistema mantendría su precisión invariable sin importar los cambios del entorno", False),
                ("C", "Quedaría invalidada toda la fundamentación teórica de manera irrecuperable", False),
                ("D", "No existe impacto alguno porque el modelo opera de forma aislada", False)
            ],
            "Los cambios de frontera demandan reajuste de parámetros para preservar la robustez."
        ),
        (
            "¿Qué justificación técnica respalda el enfoque seleccionado en '{section}' frente a soluciones alternativas?",
            [
                ("A", "Mejor balance entre complejidad computacional, mantenibilidad y costo de implementación", True),
                ("B", "Fue la primera alternativa encontrada en la documentación sin análisis comparativo", False),
                ("C", "Minimiza la necesidad de validación docente e independencia operativa", False),
                ("D", "Evita el cumplimiento de requerimientos no funcionales de seguridad", False)
            ],
            "La elección ingenieril prioriza equilibrio técnico y restricciones de diseño."
        ),
        (
            "¿Qué limitación identificada en '{section}' motivaría una futura línea de trabajo?",
            [
                ("A", "Escalabilidad ante concurrencia extrema o restricciones de infraestructura no contempladas", True),
                ("B", "Incapacidad de ejecutar operaciones aritméticas elementales", False),
                ("C", "Obligatoriedad de reescribir todo el algoritmo desde cero en un nuevo lenguaje", False),
                ("D", "Carencia de objetivos pedagógicos asociados al plan de estudios", False)
            ],
            "Todo trabajo académico y de ingeniería identifica límites de escala y supuestos operativos."
        )
    ]

    questions = []
    q_index = 1
    
    # Generate pool_size questions cycling intelligently across sections and templates
    while len(questions) < pool_size:
        sec = clean_headings[(q_index - 1) % len(clean_headings)]
        t_index = (q_index - 1) % len(templates)
        template_text, options_template, rationale = templates[t_index]
        
        q_text = template_text.format(section=sec)
        
        # Build alternatives
        alts = []
        for opt_id, opt_text, is_correct in options_template:
            alts.append({
                "id": opt_id,
                "texto": opt_text,
                "es_correcta": is_correct
            })
            
        questions.append({
            "texto": f"P{q_index}: {q_text}",
            "alternativas": alts,
            "justificacion_respuesta": rationale,
            "seccion_origen": sec,
            "seleccionada": (q_index <= 5)  # By default select first 5 for the test
        })
        q_index += 1

    return questions

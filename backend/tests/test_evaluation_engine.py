import pytest
from backend.app.services.mock_engine import (
    analyze_text_heuristics,
    generate_mock_evaluation,
    generate_mock_questions
)

def test_heuristic_analysis():
    sample_text = (
        "# Introducción\n\n"
        "En conclusión, es fundamental destacar que la metodología utilizada permite "
        "comprender el impacto de las tecnologías emergentes en la educación superior.\n\n"
        "# Metodología\n\n"
        "Se aplicó un diseño metodológico descriptivo y analítico para evaluar la integridad."
    )
    res = analyze_text_heuristics(sample_text)
    assert "pct_ia" in res
    assert "confianza" in res
    assert "justificacion" in res
    assert isinstance(res["secciones_sospechosas"], list)

def test_anexo_a_conformance():
    """Verify evaluation strictly adheres to Blueprint Anexo A schema (RF-007)"""
    sample_text = (
        "# Resumen Ejecutivo\n\n"
        "El presente informe detalla el análisis de sistemas distribuidos y microservicios.\n\n"
        "# Arquitectura del Sistema\n\n"
        "Se adoptó un esquema descentralizado con tolerancia a particiones de red."
    )
    anexo_a, nota, pct_ia = generate_mock_evaluation(sample_text, nivel_rigor="medium")
    
    # Assert top-level keys
    assert "porcentaje_logro" in anexo_a
    assert "feedback" in anexo_a
    assert "deteccion_ia" in anexo_a
    assert "desglose_rubrica" in anexo_a
    assert "evaluacion_respuestas" in anexo_a

    # Assert feedback
    fb = anexo_a["feedback"]
    assert "fortalezas" in fb and isinstance(fb["fortalezas"], list)
    assert "debilidades" in fb and isinstance(fb["debilidades"], list)
    assert "recomendaciones" in fb and isinstance(fb["recomendaciones"], list)

    # Assert deteccion_ia
    det = anexo_a["deteccion_ia"]
    assert "porcentaje" in det
    assert "nivel_confianza" in det
    assert "secciones_sospechosas" in det
    assert "justificacion" in det

    # Assert desglose_rubrica
    dr = anexo_a["desglose_rubrica"]
    assert "contenido" in dr
    assert "estructura" in dr
    assert "ortografia" in dr

    # Assert evaluacion_respuestas
    er = anexo_a["evaluacion_respuestas"]
    assert "nivel_rigor_aplicado" in er
    assert "porcentaje_coherencia" in er
    assert "respuestas_correctas" in er
    assert "preguntas_falladas" in er
    assert "observacion_ia" in er
    assert "requiere_defensa_oral" in er
    assert isinstance(er["requiere_defensa_oral"], bool)

    # Assert grading scale
    assert 1.0 <= nota <= 7.0
    assert 0.0 <= pct_ia <= 100.0

def test_question_pool_generation():
    """Verify question pool generation RF-008 (10-30 questions)"""
    sample_text = (
        "# Metodología\n\n"
        "Se implementaron pruebas unitarias y de estrés.\n\n"
        "# Resultados\n\n"
        "El tiempo de respuesta se redujo en un 40%."
    )
    questions = generate_mock_questions(sample_text, pool_size=15)
    assert len(questions) == 15
    for q in questions:
        assert "texto" in q
        assert "alternativas" in q
        assert len(q["alternativas"]) == 4
        # Exactly one correct alternative
        correct_count = sum(1 for a in q["alternativas"] if a.get("es_correcta"))
        assert correct_count == 1

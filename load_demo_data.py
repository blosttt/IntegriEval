"""Carga aditiva e idempotente de ejemplos locales; no envía correos ni borra datos."""
from datetime import datetime, timedelta, timezone
import json

from backend.app.database import SessionLocal
from backend.app import models as m
from backend.app.services.mock_engine import generate_mock_evaluation, generate_mock_questions
from seed_demo_data import STUDENTS, MARKDOWNS, NOTE_OVERRIDES


def main():
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        teacher = db.query(m.Usuario).filter_by(correo="docente@universidad.cl").one()
        course = db.query(m.Asignatura).filter_by(docente_id=teacher.id).first()
        if course is None:
            raise RuntimeError("No existe un curso asignado al docente demo")
        created = 0
        for i, data in enumerate(STUDENTS):
            email = f"alumno.demo.{i + 1:02d}@example.invalid"
            if db.query(m.Estudiante).filter_by(asignatura_id=course.id, correo=email).first():
                continue
            student = m.Estudiante(nombre=f"{data['nombre']} (Demo)", correo=email, asignatura_id=course.id)
            db.add(student)
            db.flush()
            work = m.Trabajo(estudiante_id=student.id, markdown=MARKDOWNS[i], estado="analizado")
            db.add(work)
            db.flush()
            _, pct_ia, logro = NOTE_OVERRIDES[i]
            breakdown, _, _ = generate_mock_evaluation(markdown_content=MARKDOWNS[i], nivel_rigor="medium", umbral_ia=40, umbral_coherencia=60)
            breakdown["porcentaje_logro"] = f"{logro}%"
            breakdown["deteccion_ia"]["porcentaje"] = f"{pct_ia}%"
            breakdown["evaluacion_respuestas"]["requiere_defensa_oral"] = i in (2, 4, 8)
            feedback = breakdown.get("feedback", {})
            evaluation = m.Evaluacion(trabajo_id=work.id, nota=float(logro), pct_ia=pct_ia, feedback=feedback, desglose=breakdown)
            db.add(evaluation)
            db.flush()
            questions = []
            for j, q in enumerate(generate_mock_questions(markdown_content=MARKDOWNS[i], pool_size=15)):
                question = m.Pregunta(evaluacion_id=evaluation.id, texto=q["texto"], alternativas=q["alternativas"], seleccionada=j < 5, justificacion_respuesta=q.get("justificacion_respuesta"), seccion_origen=q.get("seccion_origen"))
                db.add(question)
                questions.append(question)
            db.flush()
            if i < 8:
                selected = questions[:5]
                completed = i < 6
                correct_count = [5, 4, 2, 4, 1, 5][i] if completed else 0
                answers = {}
                if completed:
                    for j, q in enumerate(selected):
                        answers[str(q.id)] = next(a["id"] for a in q.alternativas if bool(a.get("es_correcta")) == (j < correct_count))
                flash = m.FlashTest(estudiante_id=student.id, vigencia=now + timedelta(hours=48), estado="completado" if completed else "pendiente", respuestas=answers, puntaje=correct_count * 20, fecha_inicio=now - timedelta(minutes=15) if completed else None, fecha_completado=now - timedelta(minutes=12) if completed else None, tiempo_transcurrido=180 if completed else 0)
                if i in (0, 1):
                    flash.nota_cerrada = True
                    flash.nota_final_confirmada = float(logro)
                    flash.justificacion_nota = "Ejemplo simulado: revisión integral del informe y Flash Test."
                    flash.fecha_cierre = now
                db.add(flash)
                db.flush()
                db.add(m.FlashTestState(test_id=flash.id, preguntas=[{"id":q.id,"texto":q.texto,"alternativas":q.alternativas,"seccion_origen":q.seccion_origen} for q in selected], indice=len(selected) if completed else 0))
            if i in (2, 4, 8):
                db.add(m.Cita(estudiante_id=student.id, docente_id=teacher.id, fecha=now + timedelta(days=3 + i), bloque="10:00 - 10:20", estado="programada", acuerdos="DEMO: revisar decisiones de diseño y metodología del informe."))
            created += 1
        if not db.query(m.Material).filter_by(asignatura_id=course.id, nombre="Guía de evaluación (Demo)").first():
            db.add(m.Material(asignatura_id=course.id, nombre="Guía de evaluación (Demo)", tipo="guia", markdown="# Material simulado\n\nJustificar arquitectura, documentar pruebas y explicar decisiones de diseño.\n\nRúbrica: problema 20%, diseño 30%, implementación 30%, conclusiones 20%."))
        if not db.query(m.TeacherAvailability).filter_by(usuario_id=teacher.id).first():
            db.add(m.TeacherAvailability(usuario_id=teacher.id, day_of_week=1, start_time="10:00", end_time="12:00"))
        if created:
            db.add(m.AuditLog(usuario_id=teacher.id, accion="CARGAR_DATOS_DEMO", tabla="asignaturas", registro_id=course.id, datos_nuevos={"estudiantes_creados":created,"simulados":True,"correos_enviados":False}))
        db.commit()
        pending = db.query(m.FlashTest).join(m.Estudiante).filter(m.Estudiante.asignatura_id == course.id, m.Estudiante.correo.like("%@example.invalid"), m.FlashTest.estado == "pendiente").all()
        print(json.dumps({"curso":course.nombre,"alumnos_nuevos":created,"flash_tests_pendientes":[f"http://127.0.0.1:3000/flash/{f.token}" for f in pending]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

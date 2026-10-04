"""
seed_demo_data.py — Simulador de datos de muestra para IntegriEval
======================================================================
Puebla la DB con:
  - 10 estudiantes en el curso demo INFO1197
  - 10 informes PDF sintéticos (Markdown variado)
  - 10 evaluaciones con Anexo A variado
  - 10 pools de preguntas (15 c/u, 5 seleccionadas)
  - 8 Flash Tests (tokens fijos para demo, 6 completados)
  - 3 citas de defensa oral agendadas
  - 2 notas finales cerradas
  - Logs de auditoría

Uso:
    .venv\\Scripts\\python seed_demo_data.py
"""

import sys, os, random, asyncio
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.database import engine, SessionLocal, Base
from backend.app import models
from backend.app.auth import hash_password
from backend.app.audit import log_audit
from backend.app.services.mock_engine import generate_mock_evaluation, generate_mock_questions
from sqlalchemy.orm.attributes import flag_modified

# ── Datos de estudiantes ────────────────────────────────────────────────

STUDENTS = [
    {"nombre": "Carlos Alumno Perez",           "correo": "carlos.alumno@alumnos.universidad.cl",       "rut": "20.123.456-7"},
    {"nombre": "Maria Jose Soto Silva",          "correo": "maria.soto@alumnos.universidad.cl",          "rut": "20.234.567-8"},
    {"nombre": "Pedro Andres Gonzalez Tapia",    "correo": "pedro.gonzalez@alumnos.universidad.cl",      "rut": "20.345.678-9"},
    {"nombre": "Valentina Paz Munoz Rojas",      "correo": "valentina.munoz@alumnos.universidad.cl",     "rut": "20.456.789-0"},
    {"nombre": "Diego Ignacio Morales Castro",   "correo": "diego.morales@alumnos.universidad.cl",       "rut": "20.567.890-1"},
    {"nombre": "Constanza Belen Flores Vega",    "correo": "constanza.flores@alumnos.universidad.cl",    "rut": "20.678.901-2"},
    {"nombre": "Felipe Esteban Araya Nunez",     "correo": "felipe.araya@alumnos.universidad.cl",        "rut": "20.789.012-3"},
    {"nombre": "Javiera Ignacia Herrera Diaz",   "correo": "javiera.herrera@alumnos.universidad.cl",     "rut": "20.890.123-4"},
    {"nombre": "Sebastian Alonso Cisternas",     "correo": "sebastian.cisternas@alumnos.universidad.cl", "rut": "20.901.234-5"},
    {"nombre": "Benjamin Alejandro Sobarzo",     "correo": "benjamin.sobarzo@alumnos.universidad.cl",    "rut": "21.012.345-6"},
]

# ── Markdowns sintéticos variados ───────────────────────────────────────
# (texto variado → IA baja;  marcadores LLM → IA alta)

MARKDOWNS = [
    # 0 — Carlos: muy bueno, redacción humana, IA baja
    """# Sistema Distribuido de Monitoreo Industrial en Tiempo Real

## 1. Introduccion y Motivacion

La proliferacion de dispositivos IoT en entornos industriales genera desafios concretos
para la ingenieria de sistemas. Este proyecto aborda el diseno de una plataforma que
ingiere 50 000 eventos/segundo desde sensores heterogeneos (temperatura, vibracion,
corriente alterna) con latencia sub-100ms.

La arquitectura combina Apache Kafka como bus de mensajes, ClickHouse como almacen
columnar de series temporales y Grafana para visualizacion reactiva. La motivacion
surgio de un problema real en una planta siderurgica donde la deteccion tardia de
sobrecalentamiento provocaba paros no planificados de 3 a 4 horas.

## 2. Arquitectura y Decisiones de Diseno

Se opto por diseno basado en eventos (EDA) sobre REST por tres razones: bajo
acoplamiento entre productores y consumidores, tolerancia a picos de ingesta y
reproducibilidad del log para auditoria. El diagrama UML de componentes refleja
cinco microservicios con responsabilidades unicas.

El particionado de Kafka por hash de sensor_id fue critico para evitar hotspots.
Se validaron dos esquemas de serializacion (Avro vs. Protobuf) y se eligio Avro
por compatibilidad con el Schema Registry de Confluent.

## 3. Implementacion y Pruebas de Carga

Las pruebas de carga se ejecutaron con Locust usando 200 usuarios concurrentes durante
45 minutos. El percentil p99 de latencia fue 87ms. El cuello de botella identificado
fue el particionado inicial de Kafka, resuelto ajustando la estrategia por hash.

## 4. Conclusiones y Trabajo Futuro

El sistema cumple los requerimientos de latencia y escalabilidad horizontal verificados
empiricamente. Como trabajo futuro se propone incorporar deteccion de anomalias con
Isolation Forest y federated learning para personalizar umbrales sin centralizar datos.
""",
    # 1 — Maria: buena nota, texto rico, IA media-baja
    """# Plataforma de Evaluacion Estudiantil con NLP y Machine Learning

## Descripcion del Problema

Las instituciones de educacion superior enfrentan el desafio de evaluar grandes
cohortes de estudiantes de manera objetiva. Este trabajo propone una plataforma
que combina procesamiento de lenguaje natural y modelos de clasificacion supervisada
para apoyar la correccion de respuestas abiertas de forma semi-automatica.

## Marco Teorico

Se revisaron tres enfoques: sistemas basados en rubricas manuales, similitud semantica
(Word2Vec, BERT) y clasificadores supervisados (SVM, Random Forest). La literatura
muestra que los transformers preentrenados superan a modelos estadisticos en evaluacion
de coherencia textual.

## Diseno de la Solucion

La arquitectura usa un backend FastAPI, un modelo BERT fine-tuned sobre un corpus de
respuestas anotadas por docentes y un frontend React para revision y correccion.
El pipeline incluye tokenizacion, embeddings contextuales y prediccion de nota 1 a 7.

## Resultados

Con 800 respuestas anotadas (80/20 train/test), el F1-score ponderado fue 0.82.
El MAE fue 0.4 puntos, comparable a la variabilidad inter-evaluador humano.

## Limitaciones y Trabajo Futuro

El principal sesgo es el corpus de un solo docente. El trabajo futuro contempla
anotacion multi-evaluador y domain adaptation para otras asignaturas.
""",
    # 2 — Pedro: texto con marcadores LLM, IA alta (~60%)
    """# Sistema de Gestion de Inventario Empresarial

## Introduccion

En resumen, el objetivo de este trabajo es desarrollar un sistema de gestion. Es fundamental
destacar que la gestion de inventario es un aspecto clave para las empresas modernas.
A lo largo de este informe se presentaran los aspectos clave del sistema propuesto.
Cabe mencionar que se utilizaron diversas herramientas y tecnologias. Sin lugar a dudas
la tecnologia juega un papel crucial en la actualidad empresarial.

## Desarrollo del Sistema

En ultima instancia el sistema permite gestionar el inventario de manera eficiente.
Es crucial destacar que se implementaron funcionalidades de gestion de productos.
Cabe mencionar que el sistema es eficiente y escalable. Un aspecto clave es la
interfaz de usuario amigable que facilita la operacion. En resumen las funciones
principales son la gestion de productos y la gestion de usuarios del sistema.
Es fundamental que el sistema sea escalable y mantenible a largo plazo.

## Implementacion

No obstante se encontraron dificultades en la implementacion del modulo de reportes.
Sin lugar a dudas se resolvieron mediante un enfoque sistematico y ordenado. En
conclusion la implementacion fue exitosa. Un papel crucial lo juega la base de
datos relacional que almacena los datos de forma persistente y segura.

## Conclusion

En resumen el sistema cumple todos los objetivos planteados inicialmente. Es fundamental
destacar que el trabajo fue completado de manera satisfactoria. Un abanico de mejoras
futuras se pueden incorporar en proximas iteraciones del proyecto.
""",
    # 3 — Valentina: buena, sistemas seguros
    """# Framework de Deteccion de Burnout Academico mediante Datos Pasivos

## Resumen Ejecutivo

Este proyecto propone un framework no intrusivo para la deteccion temprana del burnout
academico, integrando senales pasivas de comportamiento digital: actividad en el LMS
institucional, frecuencia de entrega y metricas de sueno via dispositivos wearable.

## Arquitectura de Datos y Pipeline ML

El pipeline tiene cuatro etapas: ingesta desde Canvas LMS API y Fitbit API con OAuth 2.0,
feature engineering sobre ventanas temporales de 7 dias, deteccion de anomalias con
Autoencoder variacional (VAE) y una interfaz docente con alertas configurables.

## Validacion Etica y Privacidad

Los datos de salud y rendimiento son sensibles. Se aplico privacidad por diseno:
minimizacion de datos, seudonimizacion irreversible con HMAC-SHA256 y consentimiento
granular. Se obtuvo aprobacion del Comite de Etica de la Facultad (Resolucion 2026-042).

## Resultados Preliminares

En un piloto con 38 voluntarios durante 8 semanas, el modelo detecto episodios de riesgo
con 5 a 7 dias de anticipacion en el 74% de los casos confirmados. El AUC-ROC fue 0.81.

## Escalabilidad

La solucion opera en Kubernetes con autoscaling. El costo estimado es menor a 0.12 USD
por alumno por mes usando instancias Spot en AWS, viable para adopcion institucional.
""",
    # 4 — Diego: texto muy corto y repetitivo → IA muy alta
    """# Aplicacion Web de Recetas

## Introduccion

Es fundamental destacar que las recetas son importantes. En resumen se desarrollo
una aplicacion web. Es crucial que la aplicacion funcione bien. Cabe mencionar que
se uso React. Sin lugar a dudas el proyecto fue exitoso.

## Desarrollo

Se implemento una aplicacion web de recetas. Es fundamental que el usuario pueda
buscar recetas. En ultima instancia la aplicacion permite ver recetas. Cabe mencionar
que se usa una base de datos. Un papel crucial lo juega el backend. No obstante
hubo dificultades. Sin lugar a dudas se resolvieron.

## Conclusion

En resumen la aplicacion funciona. Es fundamental que siga mejorando. Un abanico
de mejoras futuras existen. En conclusion el proyecto fue exitoso y satisfactorio.
""",
    # 5 — Constanza: muy buena, novel
    """# Analizador Estatico de Vulnerabilidades en Smart Contracts Solidity

## Motivacion y Contexto

El analisis estatico de contratos inteligentes es critico para prevenir perdidas
millonarias por exploits. El ataque The DAO (2016) y el exploit de Parity Wallet (2017)
perdieron mas de 150 millones de dolares combinados por vulnerabilidades de reentrancy
y delegatecall mal gestionado.

## Contribucion

Se implemento un analizador basado en AST parsing de Solidity 0.8.x que detecta
las vulnerabilidades OWASP Smart Contract Top 10: reentrancy, integer overflow,
tx.origin authentication, front-running y delegatecall sin validacion de destino.

## Evaluacion Experimental

Se evaluo sobre 500 contratos del repositorio Etherscan verificado. Los resultados
para deteccion de reentrancy: 91% precision y 84% recall. Se propone integracion
como plugin de hardhat para retroalimentacion en tiempo de compilacion.

## Trabajo Futuro

El trabajo futuro incluye soporte para Vyper y Cairo (StarkNet), analisis de flujo
de datos entre contratos en llamadas cross-contract y verificacion formal con SMT.
""",
    # 6 — Felipe: nota media, estructura OK
    """# Simulador de Redes de Petri para Modelado de Procesos Concurrentes

## Introduccion

Las redes de Petri son un formalismo matematico para modelar sistemas concurrentes,
asincrónicos y distribuidos. Este trabajo presenta un simulador implementado en Java
con interfaz grafica Swing, permitiendo definir lugares, transiciones y arcos.

## Funcionalidades Implementadas

El simulador permite ejecucion paso a paso, ejecucion continua hasta deadlock y
animacion de tokens en tiempo real. El analisis de alcanzabilidad detecta deadlocks
automaticamente usando BFS sobre el grafo de estado del marcado.

## Validacion

Se validaron 12 modelos de procesos industriales extraidos de la literatura (Peterson 1977,
Murata 1989). El rendimiento fue comparable a GreatSPN en modelos de hasta 500 plazas
con tiempos de analisis bajo 200ms en hardware convencional.

## Contribucion Principal

La integracion del analisis de invariantes de lugar y transicion dentro de la interfaz
visual simplifica el diagnostico de propiedades de vivacidad y seguridad.
""",
    # 7 — Javiera: nota alta, muy buena calidad
    """# Dashboard de Analitica Educativa para Docentes de Ensenanza Basica

## Contexto y Problema

La brecha digital en el uso de datos para toma de decisiones pedagogicas afecta
a docentes de establecimientos municipales chilenos. Solo el 12% usa datos sistematicamente
(MINEDUC 2024). Este proyecto disena un dashboard accesible (WCAG 2.1 AA).

## Fuente de Datos e Indicadores

Se consolidan datos del sistema SIGE del Ministerio de Educacion de Chile. Los
indicadores principales son: riesgo de repitencia (prediccion 8 semanas), asistencia
acumulada y participacion en talleres extracurriculares.

## Modelo Predictivo

Se usa XGBoost con 18 variables de entrada. El modelo se entrena mensualmente con
reentrenamiento incremental. En el conjunto de prueba (n=1200 estudiantes, cohorte 2024)
el AUC-ROC fue 0.88 y la precision al top-10% de riesgo fue 79%.

## Usabilidad

Se realizaron 4 rondas de pruebas de usabilidad con 12 docentes. El SUS score final
fue 82.5 (calificacion excelente). La tarea mas dificil fue la configuracion de alertas,
que se simplifico con un wizard de 3 pasos en la iteracion final.
""",
    # 8 — Sebastian: texto con marcadores moderados, IA media
    """# Optimizacion de Rutas para Flota de Drones de Reparto Urbano

## Descripcion del Problema

El problema de ruteo de vehiculos aplicado a drones de ultima milla en entorno
urbano presenta restricciones especiales de peso maximo, capacidad de bateria
(30 minutos de vuelo), zonas de vuelo restringidas y ventanas de entrega.

## Metodologia

Se implemento un algoritmo genetico con representacion de permutacion. Los operadores
son cruce PMX (Partially Mapped Crossover) y mutacion por inversion de segmento.
La funcion objetivo minimiza el tiempo total de entrega ponderando penalizaciones
por restricciones violadas.

## Experimentos

En el mapa de Santiago Centro con 250 nodos de entrega y 8 drones, el algoritmo
genetico mejoro un 18% sobre el algoritmo greedy de referencia en 200 generaciones.
El tiempo de computo fue 4.2 segundos en un Intel Core i7-12700H.

## Conclusiones

El enfoque metaheuristico es adecuado para el problema. Las restricciones de bateria
son el factor limitante mas critico. Como trabajo futuro se propone hibridacion con
busqueda local 2-opt para mejorar la convergencia.
""",
    # 9 — Benjamin: nota media-baja, texto breve
    """# API REST para Gestion de Biblioteca Universitaria

## Introduccion

Se desarrollo una API REST en Node.js con Express para gestionar el catalogo
de una biblioteca universitaria. La API implementa CRUD de libros, autores y
prestamos con autenticacion JWT y paginacion de resultados.

## Diseno

Se utilizo arquitectura MVC con PostgreSQL como base de datos relacional.
Los endpoints principales son /books, /authors y /loans con soporte para
GET, POST, PUT y DELETE. Se implemento rate limiting para evitar abusos.

## Pruebas

Se escribieron 45 tests con Jest y supertest. La cobertura de codigo fue 87%.
Los tests cubren casos exitosos y manejo de errores esperados (400, 401, 404).

## Conclusion

La API cumple los requerimientos funcionales del sistema de biblioteca. Como
mejora futura se propone soporte para reservas anticipadas y notificaciones email.
""",
]

# Notas y pct_ia forzados (más realistas y variados)
NOTE_OVERRIDES = [
    # (nota_preliminar, pct_ia, pct_logro)
    (6.2, 18.0, 87),   # Carlos   — excelente
    (5.7, 22.0, 79),   # Maria    — muy bueno
    (3.2, 71.0, 30),   # Pedro    — IA alta, reprueba
    (6.5, 19.0, 91),   # Valentina — sobresaliente
    (2.8, 75.0, 25),   # Diego    — IA muy alta, suspendido
    (6.9, 16.0, 98),   # Constanza — maxima
    (5.1, 38.0, 70),   # Felipe   — borderline IA, aprobado
    (6.8, 15.0, 96),   # Javiera  — sobresaliente
    (4.3, 44.0, 62),   # Sebastian — alerta IA leve
    (4.8, 35.0, 67),   # Benjamin — aprobado regular
]

# Puntajes Flash Test simulados para los 8 primeros (%)
FLASH_SCORES = [88, 72, 38, 80, 25, 91, 65, 78]

DEMO_TOKENS = [
    "demo-token-carlos-001",
    "demo-token-maria-002",
    "demo-token-pedro-003",
    "demo-token-valentina-004",
    "demo-token-diego-005",
    "demo-token-constanza-006",
    "demo-token-felipe-007",
    "demo-token-javiera-008",
]

async def main():
    print("=" * 64)
    print("  IntegriEval — Simulador de Datos Demo v2.0")
    print("=" * 64)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    now = datetime.now(timezone.utc)

    try:
        # ── Obtener docente y curso seed ─────────────────────────────────
        teacher = db.query(models.Usuario).filter_by(correo="docente@universidad.cl").first()
        if not teacher:
            print("[ERROR] Usuario docente no existe. Asegurate de que el servidor haya arrancado al menos una vez.")
            return

        course = db.query(models.Asignatura).filter_by(docente_id=teacher.id).first()
        if not course:
            print("[ERROR] No se encontro asignatura. Ejecuta el servidor primero.")
            return

        print(f"[OK] Docente : {teacher.nombre}")
        print(f"[OK] Curso   : {course.nombre}\n")

        # ── Borrar datos previos (idempotente) ───────────────────────────
        prev = db.query(models.Estudiante).filter_by(asignatura_id=course.id).all()
        if prev:
            print(f"[i] Limpiando {len(prev)} estudiantes y datos previos...")
            for s in prev:
                # Flash tests del estudiante
                db.query(models.FlashTest).filter_by(estudiante_id=s.id).delete()
                # Citas
                db.query(models.Cita).filter_by(estudiante_id=s.id).delete()
                # Trabajo + evaluacion + preguntas
                t = db.query(models.Trabajo).filter_by(estudiante_id=s.id).first()
                if t:
                    ev = db.query(models.Evaluacion).filter_by(trabajo_id=t.id).first()
                    if ev:
                        db.query(models.Pregunta).filter_by(evaluacion_id=ev.id).delete()
                        db.delete(ev)
                    db.delete(t)
                db.delete(s)
            db.commit()

        # ── 1. Crear estudiantes ─────────────────────────────────────────
        print(f"[1/6] Creando {len(STUDENTS)} estudiantes...")
        student_objs = []
        for sd in STUDENTS:
            s = models.Estudiante(
                nombre=sd["nombre"],
                correo=sd["correo"],
                rut=sd["rut"],
                asignatura_id=course.id
            )
            db.add(s)
        db.commit()
        student_objs = db.query(models.Estudiante).filter_by(asignatura_id=course.id).order_by(models.Estudiante.id).all()
        print(f"   OK  {len(student_objs)} estudiantes registrados")

        # ── 2. Crear trabajos + evaluaciones + preguntas ─────────────────
        print(f"\n[2/6] Generando evaluaciones con Mock Engine...")
        params       = course.parametros or {}
        nivel_rigor  = params.get("nivel_rigor", "medium")
        umbral_ia    = float(params.get("umbral_ia", 40.0))
        umbral_coh   = float(params.get("umbral_coherencia", 60.0))
        pool_size    = int(params.get("pool_size", 15))
        num_sel      = int(params.get("num_preguntas_test", 5))

        eval_objs = []
        for i, student in enumerate(student_objs):
            md = MARKDOWNS[i]

            # Trabajo
            trabajo = models.Trabajo(
                estudiante_id=student.id,
                pdf_path=f"sample_data/informe_{student.nombre.split()[0].lower()}.pdf",
                markdown=md,
                estado="analizado"
            )
            db.add(trabajo)
            db.commit()
            db.refresh(trabajo)

            # Evaluacion — usar overrides para mayor realismo
            override_nota, override_ia, override_logro = NOTE_OVERRIDES[i]
            anexo_a, _, _ = generate_mock_evaluation(
                markdown_content=md,
                nivel_rigor=nivel_rigor,
                umbral_ia=umbral_ia,
                umbral_coherencia=umbral_coh
            )
            # Pisar con valores realistas
            nota   = override_nota
            pct_ia = override_ia
            coh = round(max(30, min(95, 100 - (pct_ia * 0.5) + random.randint(-5, 5))))
            req_def = (pct_ia >= umbral_ia) or (coh < umbral_coh) or (nota < 4.5)
            anexo_a["porcentaje_logro"] = f"{override_logro}%"
            anexo_a["deteccion_ia"]["porcentaje"]     = f"{int(pct_ia)}%"
            anexo_a["deteccion_ia"]["nivel_confianza"] = (
                "alta" if pct_ia >= 65 else "medio" if pct_ia >= 35 else "baja"
            )
            if "evaluacion_respuestas" in anexo_a:
                anexo_a["evaluacion_respuestas"]["requiere_defensa_oral"] = req_def
                anexo_a["evaluacion_respuestas"]["porcentaje_coherencia"] = f"{coh}%"

            evaluacion = models.Evaluacion(
                trabajo_id=trabajo.id,
                nota=nota,
                feedback=anexo_a.get("feedback", {}),
                pct_ia=pct_ia,
                desglose=anexo_a
            )
            db.add(evaluacion)
            db.commit()
            db.refresh(evaluacion)
            eval_objs.append(evaluacion)

            # Preguntas
            questions_data = generate_mock_questions(markdown_content=md, pool_size=pool_size)
            for idx, q_dict in enumerate(questions_data):
                p = models.Pregunta(
                    evaluacion_id=evaluacion.id,
                    texto=q_dict["texto"],
                    alternativas=q_dict["alternativas"],
                    seleccionada=(idx < num_sel),
                    justificacion_respuesta=q_dict.get("justificacion_respuesta"),
                    seccion_origen=q_dict.get("seccion_origen")
                )
                db.add(p)
            db.commit()

            req_def = anexo_a.get("evaluacion_respuestas", {}).get("requiere_defensa_oral", False)
            flag    = "ALERTA-IA" if pct_ia >= umbral_ia else "ok"
            deff    = "[DEFENSA]" if req_def else ""
            print(f"   {i+1:02d}. {student.nombre[:32]:<34} nota={nota}  IA={pct_ia:4.1f}%  {flag}  {deff}")

            log_audit(db, "EVALUACION_GENERADA", "evaluaciones", evaluacion.id, teacher.id,
                      datos_nuevos={"estudiante_id": student.id, "nota": nota, "pct_ia": pct_ia})

        # ── 3. Flash Tests + respuestas simuladas ────────────────────────
        print(f"\n[3/6] Creando {len(DEMO_TOKENS)} Flash Tests y simulando respuestas...")
        expiry = now + timedelta(hours=48)

        for i, (token_str, score_pct) in enumerate(zip(DEMO_TOKENS, FLASH_SCORES)):
            student   = student_objs[i]
            evaluacion = eval_objs[i]

            preguntas_sel = db.query(models.Pregunta).filter_by(
                evaluacion_id=evaluacion.id, seleccionada=True
            ).all()

            flash = models.FlashTest(
                estudiante_id=student.id,
                token=token_str,
                vigencia=expiry,
                tiempo_limite_segundos=int(params.get("tiempo_test_segundos", 60)),
                estado="pendiente"
            )
            db.add(flash)
            db.commit()
            db.refresh(flash)

            # Simular respuestas para los primeros 6
            if i < 6 and preguntas_sel:
                n = len(preguntas_sel)
                n_correct = round(n * score_pct / 100)

                respuestas = {}
                preg_shuffled = list(preguntas_sel)
                random.shuffle(preg_shuffled)

                for j, preg in enumerate(preg_shuffled):
                    alts = preg.alternativas or []
                    correct_id = next((a["id"] for a in alts if a.get("es_correcta")), None)
                    wrong_ids  = [a["id"] for a in alts if not a.get("es_correcta")]
                    chosen = correct_id if j < n_correct else (random.choice(wrong_ids) if wrong_ids else correct_id)
                    respuestas[str(preg.id)] = chosen

                flash.respuestas           = respuestas
                flash.puntaje              = score_pct
                flash.estado               = "completado"
                flash.fecha_inicio         = now - timedelta(minutes=random.randint(10, 90))
                flash.fecha_completado     = now - timedelta(minutes=random.randint(2, 9))
                flash.tiempo_transcurrido  = random.randint(120, 280)
                db.commit()

                label = "OK" if score_pct >= 60 else "DEFENSA"
                print(f"   {i+1}. {student.nombre.split()[0]:<14}  token={token_str[:20]}...  score={score_pct}%  [{label}]")
            else:
                print(f"   {i+1}. {student.nombre.split()[0]:<14}  token={token_str[:20]}...  [PENDIENTE]")

        # ── 4. Citas de defensa oral ─────────────────────────────────────
        print(f"\n[4/6] Agendando citas de defensa oral...")

        # Pedro (i=2, score 38%), Diego (i=4, score 25%) + el de nota mas baja
        defensa_idx = [2, 4]
        lower_idx = min(range(len(eval_objs)), key=lambda i: eval_objs[i].nota)
        if lower_idx not in defensa_idx:
            defensa_idx.append(lower_idx)
        defensa_idx = defensa_idx[:3]

        base_date = now + timedelta(days=3)
        for j, idx in enumerate(defensa_idx):
            student = student_objs[idx]
            fecha_cita = base_date + timedelta(days=j)
            bloque = f"{10 + j}:00 - {10 + j}:20"
            cita = models.Cita(
                estudiante_id=student.id,
                docente_id=teacher.id,
                fecha=fecha_cita,
                bloque=bloque,
                acuerdos="Foco en la justificacion metodologica y decisiones de diseno del informe. Preguntar sobre seccion critica.",
                estado="programada"
            )
            db.add(cita)
            db.commit()
            print(f"   {j+1}. {student.nombre.split()[0]:<14}  {fecha_cita.strftime('%d/%m/%Y')}  {bloque}")
            log_audit(db, "AGENDAR_DEFENSA_ORAL", "citas", cita.id, teacher.id,
                      datos_nuevos={"estudiante_id": student.id, "fecha": str(fecha_cita)})

        # ── 5. Confirmar % de logro final para 2 estudiantes ────────────
        print(f"\n[5/6] Confirmando % de logro final para 2 estudiantes...")

        CLOSE = [
            (0, 88.0, "Excelente dominio del contenido. Flash Test confirma autoría. Logro final ajustado al 88% por desempeño integral."),
            (7, 96.0, "Rendimiento sobresaliente en informe y Flash Test. Logro final del 96% refleja dominio integral del proyecto."),
        ]
        for idx, logro_final, justif in CLOSE:
            student   = student_objs[idx]
            flash_obj = db.query(models.FlashTest).filter_by(estudiante_id=student.id).first()
            if flash_obj:
                flash_obj.nota_final_confirmada = logro_final
                flash_obj.justificacion_nota    = justif
                flash_obj.nota_cerrada          = True
                flash_obj.fecha_cierre          = now - timedelta(days=random.randint(0, 2))
                db.commit()
                print(f"   [OK] {student.nombre.split()[0]:<14}  % logro final confirmado: {logro_final}%")
                log_audit(db, "CIERRE_MODIFICACION_NOTA", "flash_tests", flash_obj.id, teacher.id,
                          datos_nuevos={"pct_logro_final": logro_final, "estudiante_id": student.id})

        # ── 6. Syllabus ─────────────────────────────────────────────────
        print(f"\n[6/6] Cargando syllabus del curso...")
        if not db.query(models.Material).filter_by(asignatura_id=course.id).first():
            syllabus_path = os.path.join("sample_data", "syllabus_info1197.md")
            if os.path.exists(syllabus_path):
                with open(syllabus_path, encoding="utf-8", errors="replace") as f:
                    syllabus_md = f.read()
            else:
                syllabus_md = "# Syllabus INFO1197\n\nIngenieria Civil Informatica - Proyecto de Titulo\n\nEste curso aborda el proceso completo de desarrollo de un proyecto de ingenieria de software."
            mat = models.Material(
                asignatura_id=course.id,
                nombre="Syllabus INFO1197 - Semestre 2 2026",
                tipo="syllabus",
                markdown=syllabus_md
            )
            db.add(mat)
            db.commit()
            print(f"   OK  Syllabus cargado ({len(syllabus_md):,} caracteres)")
        else:
            print("   [i] Syllabus ya existe, se omite")

        # ── Resumen ──────────────────────────────────────────────────────
        print("\n" + "=" * 64)
        print("  SIMULACION COMPLETADA")
        print("=" * 64)
        n_estudiantes = db.query(models.Estudiante).filter_by(asignatura_id=course.id).count()
        n_evals       = db.query(models.Evaluacion).join(models.Trabajo).join(models.Estudiante).filter(models.Estudiante.asignatura_id == course.id).count()
        n_completados = db.query(models.FlashTest).filter_by(estado="completado").count()
        n_pendientes  = db.query(models.FlashTest).filter_by(estado="pendiente").count()
        n_citas       = db.query(models.Cita).count()
        n_cerradas    = db.query(models.FlashTest).filter_by(nota_cerrada=True).count()

        print(f"  Estudiantes       : {n_estudiantes}")
        print(f"  Evaluaciones      : {n_evals}")
        print(f"  Flash Tests OK    : {n_completados}")
        print(f"  Flash Tests pend. : {n_pendientes}")
        print(f"  Citas de defensa  : {n_citas}")
        print(f"  Notas cerradas    : {n_cerradas}")
        print()
        print("  Accede en: http://127.0.0.1:8000")
        print()
        print("  Credenciales demo:")
        print("    Docente  ->  docente@universidad.cl   /  Docente123!")
        print("    Admin    ->  admin@universidad.cl     /  Admin123!")
        print("    Ayudante ->  ayudante@universidad.cl  /  Ayudante123!")
        print("=" * 64)

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())

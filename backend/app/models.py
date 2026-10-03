import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from backend.app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

def default_vigencia():
    return datetime.now(timezone.utc) + timedelta(hours=48)

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    correo = Column(String(150), unique=True, index=True, nullable=False)
    contrasena = Column(String(255), nullable=False)
    rol = Column(String(50), default="docente", nullable=False)  # docente, ayudante, admin
    fecha_creacion = Column(DateTime, default=utc_now)

    asignaturas = relationship("Asignatura", back_populates="docente", cascade="all, delete-orphan")
    citas = relationship("Cita", back_populates="docente")
    auditorias = relationship("AuditLog", back_populates="usuario")

class Asignatura(Base):
    __tablename__ = "asignaturas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    periodo = Column(String(50), nullable=False)  # Semestre 1, Semestre 2
    ano = Column(Integer, nullable=False)
    docente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    parametros = Column(JSON, default=lambda: {
        "prompt_custom": "",
        "nivel_rigor": "medium",  # low, medium, high
        "pool_size": 15,          # 10 a 30 (RF-003)
        "num_preguntas_test": 5,  # Seleccionadas para el test
        "umbral_ia": 40.0,        # % IA para alerta
        "umbral_coherencia": 60.0,# % coherencia mínimo
        "tiempo_test_segundos": 60# 60s por test o pregunta (RN-002)
    })
    fecha_creacion = Column(DateTime, default=utc_now)

    docente = relationship("Usuario", back_populates="asignaturas")
    estudiantes = relationship("Estudiante", back_populates="asignatura", cascade="all, delete-orphan")
    materiales = relationship("Material", back_populates="asignatura", cascade="all, delete-orphan")

class Estudiante(Base):
    __tablename__ = "estudiantes"
    __table_args__ = (
        UniqueConstraint("correo", "asignatura_id", name="uq_estudiante_correo_asignatura"),
    )

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    correo = Column(String(150), nullable=False, index=True)
    rut = Column(String(20), nullable=True)
    asignatura_id = Column(Integer, ForeignKey("asignaturas.id"), nullable=False)
    fecha_creacion = Column(DateTime, default=utc_now)

    asignatura = relationship("Asignatura", back_populates="estudiantes")
    trabajo = relationship("Trabajo", back_populates="estudiante", uselist=False, cascade="all, delete-orphan")
    flash_tests = relationship("FlashTest", back_populates="estudiante", cascade="all, delete-orphan")
    citas = relationship("Cita", back_populates="estudiante", cascade="all, delete-orphan")

class Material(Base):
    __tablename__ = "materiales"

    id = Column(Integer, primary_key=True, index=True)
    asignatura_id = Column(Integer, ForeignKey("asignaturas.id"), nullable=False)
    nombre = Column(String(200), nullable=False)
    tipo = Column(String(50), nullable=False)  # syllabus, rubrica, guia, otro
    file_path = Column(String(500), nullable=True)
    markdown = Column(Text, nullable=False)
    fecha_creacion = Column(DateTime, default=utc_now)

    asignatura = relationship("Asignatura", back_populates="materiales")

class Trabajo(Base):
    __tablename__ = "trabajos"

    id = Column(Integer, primary_key=True, index=True)
    estudiante_id = Column(Integer, ForeignKey("estudiantes.id"), unique=True, nullable=False)
    pdf_path = Column(String(500), nullable=True)
    markdown = Column(Text, nullable=True)
    estado = Column(String(50), default="cargado")  # cargado, analizado, error
    fecha_entrega = Column(DateTime, default=utc_now)

    estudiante = relationship("Estudiante", back_populates="trabajo")
    evaluacion = relationship("Evaluacion", back_populates="trabajo", uselist=False, cascade="all, delete-orphan")

class Evaluacion(Base):
    __tablename__ = "evaluaciones"

    id = Column(Integer, primary_key=True, index=True)
    trabajo_id = Column(Integer, ForeignKey("trabajos.id"), unique=True, nullable=False)
    nota = Column(Float, nullable=False)  # Escala 1.0 - 7.0
    feedback = Column(JSON, nullable=False)
    pct_ia = Column(Float, nullable=False)  # 0.0 - 100.0
    desglose = Column(JSON, nullable=False)  # Exact structure from Anexo A
    fecha_creacion = Column(DateTime, default=utc_now)

    trabajo = relationship("Trabajo", back_populates="evaluacion")
    preguntas = relationship("Pregunta", back_populates="evaluacion", cascade="all, delete-orphan")

class Pregunta(Base):
    __tablename__ = "preguntas"

    id = Column(Integer, primary_key=True, index=True)
    evaluacion_id = Column(Integer, ForeignKey("evaluaciones.id"), nullable=False)
    texto = Column(Text, nullable=False)
    alternativas = Column(JSON, nullable=False)  # [{"id": "A", "texto": "...", "es_correcta": bool}, ...]
    seleccionada = Column(Boolean, default=False)  # Docente selecciona N <= Pool (RF-009)
    justificacion_respuesta = Column(Text, nullable=True)
    seccion_origen = Column(String(100), nullable=True)

    evaluacion = relationship("Evaluacion", back_populates="preguntas")

class FlashTest(Base):
    __tablename__ = "flash_tests"

    id = Column(Integer, primary_key=True, index=True)
    estudiante_id = Column(Integer, ForeignKey("estudiantes.id"), nullable=False)
    token = Column(String(100), unique=True, index=True, default=lambda: str(uuid.uuid4()))  # UUIDv4 (RFC 4122)
    vigencia = Column(DateTime, default=default_vigencia)  # 48 horas (RN-001)
    respuestas = Column(JSON, default=dict)  # {"P1": "A", "P2": "B"}
    puntaje = Column(Float, default=0.0)
    tiempo_limite_segundos = Column(Integer, default=60)
    tiempo_transcurrido = Column(Integer, default=0)
    estado = Column(String(50), default="pendiente")  # pendiente, en_progreso, completado, expirado
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_completado = Column(DateTime, nullable=True)
    
    # Cierre de calificaciones (RF-013, RN-004)
    nota_final_confirmada = Column(Float, nullable=True)
    justificacion_nota = Column(String(500), default="Criterio del docente")
    nota_cerrada = Column(Boolean, default=False)
    fecha_cierre = Column(DateTime, nullable=True)

    estudiante = relationship("Estudiante", back_populates="flash_tests")

class Cita(Base):
    __tablename__ = "citas"

    id = Column(Integer, primary_key=True, index=True)
    estudiante_id = Column(Integer, ForeignKey("estudiantes.id"), nullable=False)
    docente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha = Column(DateTime, nullable=False)
    bloque = Column(String(50), nullable=False)  # ej: "10:00 - 10:15"
    estado = Column(String(50), default="programada")  # programada, realizada, ausente, cancelada
    acuerdos = Column(Text, nullable=True)
    creada_por = Column(String(100), default="docente")
    fecha_creacion = Column(DateTime, default=utc_now)

    estudiante = relationship("Estudiante", back_populates="citas")
    docente = relationship("Usuario", back_populates="citas")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    accion = Column(String(100), nullable=False)  # LOGIN, EDITAR_NOTA, CITAR_DEFENSA, CREAR_ASIGNATURA, etc.
    tabla = Column(String(50), nullable=False)
    registro_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=utc_now)
    datos_previos = Column(JSON, nullable=True)
    datos_nuevos = Column(JSON, nullable=True)

    usuario = relationship("Usuario", back_populates="auditorias")

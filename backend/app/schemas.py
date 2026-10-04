from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# --- Auth & User Schemas (RF-015, RNF-005, RNF-006) ---
class UserCreate(BaseModel):
    nombre: str
    correo: EmailStr
    contrasena: str = Field(..., min_length=6)
    rol: str = "docente"

class UserLogin(BaseModel):
    correo: EmailStr
    contrasena: str

class UserOut(BaseModel):
    id: int
    nombre: str
    correo: str
    rol: str
    fecha_creacion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# --- Asignatura Schemas (RF-001, RF-003) ---
class ParametrosConfig(BaseModel):
    prompt_custom: str = ""
    nivel_rigor: str = "medium"  # low, medium, high
    pool_size: int = Field(default=15, ge=10, le=30)  # RF-003 (10-30)
    num_preguntas_test: int = Field(default=5, ge=1, le=15)
    umbral_ia: float = Field(default=40.0, ge=0.0, le=100.0)
    umbral_coherencia: float = Field(default=60.0, ge=0.0, le=100.0)
    tiempo_test_segundos: int = Field(default=60, ge=30, le=300)

class AsignaturaCreate(BaseModel):
    nombre: str
    periodo: str
    ano: int
    parametros: Optional[ParametrosConfig] = None

class AsignaturaUpdate(BaseModel):
    nombre: Optional[str] = None
    periodo: Optional[str] = None
    ano: Optional[int] = None
    parametros: Optional[ParametrosConfig] = None

class AsignaturaOut(BaseModel):
    id: int
    nombre: str
    periodo: str
    ano: int
    docente_id: int
    parametros: Dict[str, Any]
    fecha_creacion: Optional[datetime] = None
    total_estudiantes: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

# --- Student Schemas (RF-002) ---
class EstudianteCreate(BaseModel):
    nombre: str
    correo: EmailStr
    rut: Optional[str] = None
    asignatura_id: int

class EstudianteOut(BaseModel):
    id: int
    nombre: str
    correo: str
    rut: Optional[str] = None
    asignatura_id: int
    fecha_creacion: Optional[datetime] = None
    tiene_trabajo: Optional[bool] = False
    tiene_test: Optional[bool] = False
    estado_test: Optional[str] = None
    nota_final: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class CSVIngestionResult(BaseModel):
    total_procesados: int
    cargados_exitosamente: int
    duplicados_omitidos: int
    errores: List[str]
    estudiantes: List[EstudianteOut]

# --- Material Schemas (RF-004) ---
class MaterialOut(BaseModel):
    id: int
    asignatura_id: int
    nombre: str
    tipo: str
    file_path: Optional[str] = None
    markdown: str
    fecha_creacion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Anexo A Evaluation Structure (RF-007) ---
class FeedbackSchema(BaseModel):
    fortalezas: List[str]
    debilidades: List[str]
    recomendaciones: List[str]

class DeteccionIASchema(BaseModel):
    porcentaje: str
    nivel_confianza: str
    secciones_sospechosas: List[str]
    justificacion: str

class DesgloseRubricaSchema(BaseModel):
    contenido: str
    estructura: str
    ortografia: str

class EvaluacionRespuestasSchema(BaseModel):
    nivel_rigor_aplicado: str
    porcentaje_coherencia: str
    respuestas_correctas: str
    preguntas_falladas: List[str]
    observacion_ia: str
    requiere_defensa_oral: bool

class AnexoAEvaluacionSchema(BaseModel):
    porcentaje_logro: str
    feedback: FeedbackSchema
    deteccion_ia: DeteccionIASchema
    desglose_rubrica: DesgloseRubricaSchema
    evaluacion_respuestas: EvaluacionRespuestasSchema

# --- Trabajo & Evaluacion Schemas ---
class EvaluacionOut(BaseModel):
    id: int
    trabajo_id: int
    nota: float
    feedback: Dict[str, Any]
    pct_ia: float
    desglose: Dict[str, Any]
    fecha_creacion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TrabajoOut(BaseModel):
    id: int
    estudiante_id: int
    pdf_path: Optional[str] = None
    markdown: Optional[str] = None
    estado: str
    fecha_entrega: Optional[datetime] = None
    evaluacion: Optional[EvaluacionOut] = None

    model_config = ConfigDict(from_attributes=True)

# --- Preguntas Schemas (RF-008, RF-009) ---
class AlternativaItem(BaseModel):
    id: str  # "A", "B", "C", "D"
    texto: str
    es_correcta: bool

class PreguntaCreate(BaseModel):
    texto: str
    alternativas: List[AlternativaItem]
    seleccionada: bool = False
    justificacion_respuesta: Optional[str] = None
    seccion_origen: Optional[str] = None

class PreguntaUpdate(BaseModel):
    texto: Optional[str] = None
    alternativas: Optional[List[AlternativaItem]] = None
    seleccionada: Optional[bool] = None
    justificacion_respuesta: Optional[str] = None

class PreguntaOut(BaseModel):
    id: int
    evaluacion_id: int
    texto: str
    alternativas: List[Dict[str, Any]]
    seleccionada: bool
    justificacion_respuesta: Optional[str] = None
    seccion_origen: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SeleccionarPreguntasRequest(BaseModel):
    pregunta_ids: List[int]

# --- Flash Test Schemas (RF-010, RF-011, RN-001, RN-002) ---
class FlashTestDispatchItem(BaseModel):
    estudiante_id: int
    token: str
    correo: str
    enlace_test: str
    correo_enviado: bool
    error: Optional[str] = None

class FlashTestDispatchResponse(BaseModel):
    total_despachados: int
    items: List[FlashTestDispatchItem]

class FlashTestPublicInfo(BaseModel):
    token: str
    estudiante_nombre: str
    asignatura_nombre: str
    tiempo_limite_segundos: int
    tiempo_restante_segundos: int
    estado: str
    preguntas: List[Dict[str, Any]]  # Alternatives WITHOUT revealing correct answer!

class SubmitAnswerRequest(BaseModel):
    token: str
    respuestas: Dict[str, str]  # {"1": "A", "2": "C"}
    tiempo_transcurrido: int

class FlashTestOut(BaseModel):
    id: int
    estudiante_id: int
    token: str
    vigencia: datetime
    respuestas: Dict[str, Any]
    puntaje: float
    tiempo_limite_segundos: int
    tiempo_transcurrido: int
    estado: str
    nota_final_confirmada: Optional[float] = None
    justificacion_nota: Optional[str] = None
    nota_cerrada: bool

    model_config = ConfigDict(from_attributes=True)

# --- Teacher Results Panel & Oral Defense Citation (RF-012, RF-013, RN-004) ---
class PanelEstudianteFila(BaseModel):
    estudiante_id: int
    estudiante_nombre: str
    estudiante_correo: str
    trabajo_estado: str
    pct_logro: Optional[float] = None
    pct_logro_final: Optional[float] = None
    porcentaje_logro: Optional[str] = None
    nota_preliminar: Optional[float] = None
    pct_ia: Optional[float] = None
    confianza_ia: Optional[str] = None
    coherencia_flash: Optional[str] = None
    puntaje_flash: Optional[float] = None
    requiere_defensa: bool = False
    cita_id: Optional[int] = None
    cita_fecha: Optional[str] = None
    cita_bloque: Optional[str] = None
    cita_estado: Optional[str] = None
    nota_final: Optional[float] = None
    justificacion_nota: Optional[str] = None
    nota_cerrada: bool = False
    flash_test_token: Optional[str] = None

class PanelResultadosOut(BaseModel):
    asignatura_id: int
    asignatura_nombre: str
    total_alumnos: int
    analizados: int
    alerta_ia: int
    requieren_defensa: int
    tests_completados: int
    notas_cerradas: int
    estudiantes: List[PanelEstudianteFila]

class CitaCreate(BaseModel):
    estudiante_id: int
    fecha: datetime
    bloque: str  # ej: "09:30 - 09:45"
    acuerdos: Optional[str] = None

class CitaUpdate(BaseModel):
    fecha: Optional[datetime] = None
    bloque: Optional[str] = None
    estado: Optional[str] = None  # programada, realizada, ausente, cancelada
    acuerdos: Optional[str] = None

class CitaOut(BaseModel):
    id: int
    estudiante_id: int
    estudiante_nombre: Optional[str] = None
    docente_id: int
    fecha: datetime
    bloque: str
    estado: str
    acuerdos: Optional[str] = None
    creada_por: str

    model_config = ConfigDict(from_attributes=True)

class CierreNotaRequest(BaseModel):
    estudiante_id: int
    nota_final: float = Field(..., ge=0.0, le=100.0)  # % de logro final (0% a 100%)
    justificacion: str = Field(default="Criterio del docente")  # RN-004 obligatorio

class AuditLogOut(BaseModel):
    id: int
    usuario_id: Optional[int] = None
    usuario_nombre: Optional[str] = None
    accion: str
    tabla: str
    registro_id: Optional[int] = None
    timestamp: datetime
    datos_previos: Optional[Dict[str, Any]] = None
    datos_nuevos: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

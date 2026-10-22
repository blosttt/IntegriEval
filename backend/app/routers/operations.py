import csv
import io
from datetime import datetime, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app import models
from backend.app.config import settings
from backend.app.auth import get_current_user, check_course_access, require_admin
from backend.app.database import get_db
from backend.app.activities import parameters
from backend.app.audit import log_audit
from backend.app.services.mail_outbox import deliver
from backend.app.services.scheduling import utc

router=APIRouter(tags=['Operaciones docentes'])

class StateData(BaseModel):
    estado: Literal['abierta','cerrada','archivada']

@router.put('/api/asignaturas/{course_id}/actividades/{activity_key}/estado')
def set_state(course_id:int, activity_key:int, data:StateData, user=Depends(get_current_user), db:Session=Depends(get_db)):
    course=check_course_access(course_id,user,db,write=True)
    parameters(course,activity_key or None,db)
    if data.estado!='abierta':
        if db.query(models.UploadJob).filter(models.UploadJob.asignatura_id==course_id,models.UploadJob.actividad_id==(activity_key or None),models.UploadJob.status.in_(['pending','running'])).first():
            raise HTTPException(409,'Hay informes en cola o procesándose. Espera o cancela los pendientes antes de cerrar.')
        active=db.query(models.FlashTest).join(models.Estudiante).filter(models.Estudiante.asignatura_id==course_id,models.FlashTest.actividad_id==(activity_key or None),models.FlashTest.estado.in_(['pendiente','en_progreso']),models.FlashTest.vigencia>datetime.now(timezone.utc)).first()
        if active: raise HTTPException(409,'Hay Flash Tests activos. Espera a que terminen o caduquen antes de cerrar.')
    state=db.get(models.ActivityStatus,(course_id,activity_key))
    before=state.estado if state else 'abierta'
    if not state: state=models.ActivityStatus(asignatura_id=course_id,actividad_key=activity_key);db.add(state)
    state.estado=data.estado;db.commit()
    log_audit(db,'ESTADO_EVALUACION','asignaturas',course_id,user.id,{'estado':before},{'actividad_id':activity_key,'estado':data.estado})
    return {'estado':data.estado}

@router.get('/api/asignaturas/{course_id}/correos')
def list_deliveries(course_id:int, user=Depends(get_current_user), db:Session=Depends(get_db)):
    check_course_access(course_id,user,db)
    records=db.query(models.MailDelivery).filter_by(asignatura_id=course_id).order_by(models.MailDelivery.id.desc()).limit(100).all()
    return [{key:getattr(r,key) for key in ('id','purpose','reference_id','recipient','subject','status','attempts','error','created_at','sent_at')} for r in records]

@router.post('/api/asignaturas/{course_id}/correos/{delivery_id}/reintentar')
async def retry_delivery(course_id:int, delivery_id:int, user=Depends(get_current_user), db:Session=Depends(get_db)):
    check_course_access(course_id,user,db,write=True)
    record=db.query(models.MailDelivery).filter_by(id=delivery_id,asignatura_id=course_id).first()
    if not record: raise HTTPException(404,'Envío no encontrado')
    if record.status=='cancelled': raise HTTPException(409,'Este aviso fue reemplazado por una actualización de la cita')
    if record.purpose=='flash':
        test=db.get(models.FlashTest,record.reference_id)
        if not test or test.estado not in ('pendiente','en_progreso') or utc(test.vigencia)<=datetime.now(timezone.utc):
            raise HTTPException(409,'El Flash Test ya no está activo; genera una nueva invitación')
    if record.purpose in ('appointment','reminder'):
        appointment=db.get(models.Cita,record.reference_id)
        if not appointment or appointment.estado!='programada' or utc(appointment.fecha)<=datetime.now(timezone.utc):
            raise HTTPException(409,'La cita ya no está pendiente')
    await deliver(record,db)
    log_audit(db,'REINTENTAR_CORREO','mail_deliveries',record.id,user.id,datos_nuevos={'status':record.status})
    return {'status':record.status,'attempts':record.attempts,'error':record.error}

def safe_cell(value):
    text='' if value is None else str(value)
    return "'"+text if text.lstrip().startswith(('=','+','-','@','\t','\r')) else text

@router.get('/api/asignaturas/{course_id}/exportar')
def export_results(course_id:int, actividad_id:int|None=None, formato:Literal['csv','pdf']='csv', user=Depends(get_current_user), db:Session=Depends(get_db)):
    from backend.app.routers.panel import get_teacher_panel
    panel=get_teacher_panel(course_id,actividad_id,user,db)
    rows=[['Estudiante','Correo','Logro informe (%)','Indicador IA (%)','Flash (%)','Logro final (%)','Requiere revisión','Fecha cita','Estado cita']]
    rows.extend([[s.estudiante_nombre,s.estudiante_correo,s.pct_logro,s.pct_ia,s.puntaje_flash,s.pct_logro_final,'Sí' if s.requiere_defensa else 'No',s.cita_fecha,s.cita_estado] for s in panel.estudiantes])
    name=f'resultados-{course_id}-{actividad_id or 0}'
    if formato=='csv':
        stream=io.StringIO(newline='');writer=csv.writer(stream);writer.writerows([[safe_cell(v) for v in row] for row in rows])
        return Response(('\ufeff'+stream.getvalue()).encode('utf-8'),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="{name}.csv"'})
    import pymupdf
    document=pymupdf.open()
    for offset in range(1,max(2,len(rows)),18):
        page=document.new_page(width=842,height=595)
        page.insert_text((30,35),f'IntegryEval | Resultados | Curso {course_id} | Evaluacion {actividad_id or 0}',fontsize=14)
        y=60
        for row in rows[offset:offset+18]:
            line=f'{row[0][:32]} | Informe: {row[2]}% | IA: {row[3]}% | Flash: {row[4]}% | Final: {row[5]}%'
            page.insert_text((30,y),line,fontsize=9);y+=27
    content=document.tobytes();document.close()
    return Response(content,media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="{name}.pdf"'})

@router.get('/api/admin/integraciones')
def integration_status(user=Depends(require_admin)):
    from pathlib import Path
    path=Path(settings.TESSDATA_PREFIX) if settings.TESSDATA_PREFIX else None
    languages=settings.OCR_LANGUAGE.split('+')
    return {'llm':{'provider':settings.LLM_PROVIDER,'model':settings.LLM_MODEL,'configured':settings.LLM_PROVIDER=='ollama' or bool(settings.LLM_API_KEY),'simulated':settings.LLM_PROVIDER=='mock'},'smtp':{'enabled':settings.SMTP_ENABLED,'configured':bool(settings.SMTP_USER and settings.SMTP_PASSWORD),'public_url':settings.PUBLIC_APP_URL},'ocr':{'enabled':settings.OCR_ENABLED,'language':settings.OCR_LANGUAGE,'trained_data_ready':bool(path and all((path/(lang+'.traineddata')).is_file() for lang in languages))}}

@router.post('/api/admin/integraciones/probar-ia')
async def probe_llm(user=Depends(require_admin)):
    if settings.LLM_PROVIDER=='mock':
        raise HTTPException(409,'La IA está en modo simulado; configura un proveedor real antes de probarlo')
    if settings.LLM_PROVIDER!='ollama' and not settings.LLM_API_KEY:
        raise HTTPException(409,'Falta la clave del proveedor en la configuración del servidor')
    from backend.app.services.llm_service import request_json
    try:
        result=await request_json('Responde únicamente un objeto JSON con la propiedad ok igual a true.','Prueba de conexión sin datos de alumnos.')
        if result.get('ok') is not True:raise ValueError()
    except Exception:
        raise HTTPException(503,'El proveedor no respondió con el formato esperado; revisa modelo, URL y credenciales')
    return {'message':'El proveedor respondió correctamente. No se enviaron datos de alumnos.'}

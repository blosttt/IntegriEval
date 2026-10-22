import json
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from backend.app import models
from backend.app.auth import get_current_user, check_course_access
from backend.app.activities import parameters, assert_activity_open
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.audit import log_audit

router=APIRouter(tags=['Procesamiento en cola'])

def public_job(job):
    return {k:getattr(job,k) for k in ('id','actividad_id','estudiante_id','filename','status','attempts','error','created_at','started_at','finished_at')}

@router.post('/api/asignaturas/{course_id}/cargas')
async def queue_upload(course_id:int, estudiante_ids:str=Form(...), actividad_id:Optional[int]=Form(None), files:list[UploadFile]=File(...), user=Depends(get_current_user), db:Session=Depends(get_db)):
    course=check_course_access(course_id,user,db,write=True)
    parameters(course,actividad_id,db);assert_activity_open(course_id,actividad_id,db)
    try:
        ids=json.loads(estudiante_ids)
        if not isinstance(ids,list) or not all(isinstance(i,int) and not isinstance(i,bool) for i in ids): raise ValueError()
    except (ValueError,TypeError): raise HTTPException(422,'Lista de alumnos inválida')
    if len(files)!=len(ids) or not 1<=len(files)<=50 or len(ids)!=len(set(ids)):
        raise HTTPException(422,'Selecciona de 1 a 50 PDF, uno por alumno')
    valid={s.id for s in db.query(models.Estudiante).filter(models.Estudiante.asignatura_id==course_id,models.Estudiante.id.in_(ids),~models.Estudiante.id.in_(db.query(models.StudentStatus.estudiante_id).filter_by(active=False))).all()}
    if set(ids)!=valid: raise HTTPException(422,'Selecciona alumnos activos de esta asignatura')
    from backend.app.routers.trabajos import assert_work_editable
    for student_id in ids: assert_work_editable(student_id,db,actividad_id)
    from sqlalchemy import update
    db.execute(update(models.Asignatura).where(models.Asignatura.id==course_id).values(nombre=models.Asignatura.nombre))
    if db.query(models.UploadJob).filter(models.UploadJob.asignatura_id==course_id,models.UploadJob.actividad_id==actividad_id,models.UploadJob.estudiante_id.in_(ids),models.UploadJob.status.in_(['pending','running'])).first():
        raise HTTPException(409,'Ya hay un informe en cola para uno de esos alumnos')
    folder=settings.UPLOAD_DIR/'queue';folder.mkdir(parents=True,exist_ok=True)
    saved=[];jobs=[]
    try:
        for student_id,file in zip(ids,files):
            name=Path((file.filename or '').replace('\\','/')).name
            if not name.lower().endswith('.pdf'):raise HTTPException(422,'Solo se admiten archivos PDF')
            content=await file.read(20*1024*1024+1)
            if len(content)>20*1024*1024 or not content.startswith(b'%PDF-'):raise HTTPException(422,'PDF inválido o mayor a 20 MB')
            path=folder/(uuid.uuid4().hex+'.pdf');path.write_bytes(content);saved.append(path)
            job=models.UploadJob(asignatura_id=course_id,actividad_id=actividad_id,estudiante_id=student_id,usuario_id=user.id,filename=name[:250],file_path=str(path))
            db.add(job);jobs.append(job)
        db.commit()
    except Exception:
        db.rollback()
        for path in saved:path.unlink(missing_ok=True)
        raise
    log_audit(db,'ENCOLAR_INFORMES','asignaturas',course_id,user.id,datos_nuevos={'total':len(jobs),'actividad_id':actividad_id})
    return {'items':[public_job(j) for j in jobs]}

@router.get('/api/asignaturas/{course_id}/cargas')
def list_jobs(course_id:int, actividad_id:Optional[int]=None, user=Depends(get_current_user), db:Session=Depends(get_db)):
    course=check_course_access(course_id,user,db);parameters(course,actividad_id,db)
    return [public_job(j) for j in db.query(models.UploadJob).filter_by(asignatura_id=course_id,actividad_id=actividad_id).order_by(models.UploadJob.id.desc()).limit(100).all()]

@router.post('/api/asignaturas/{course_id}/cargas/{job_id}/{action}')
def change_job(course_id:int,job_id:int,action:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    check_course_access(course_id,user,db,write=True)
    job=db.query(models.UploadJob).filter_by(id=job_id,asignatura_id=course_id).first()
    if not job:raise HTTPException(404,'Archivo en cola no encontrado')
    if action=='cancelar':
        # Atomic claim competes with the worker, so a running file cannot be cancelled halfway through commits.
        count=db.query(models.UploadJob).filter_by(id=job.id,status='pending').update({'status':'cancelled'})
        if not count:raise HTTPException(409,'Solo se pueden cancelar archivos pendientes; los iniciados terminan su procesamiento')
    elif action=='reintentar':
        from sqlalchemy import update
        db.execute(update(models.Asignatura).where(models.Asignatura.id==course_id).values(nombre=models.Asignatura.nombre))
        assert_activity_open(course_id,job.actividad_id,db)
        if job.status not in ('failed','cancelled'):raise HTTPException(409,'El archivo no necesita reintento')
        if db.query(models.UploadJob).filter(models.UploadJob.id!=job.id,models.UploadJob.asignatura_id==course_id,models.UploadJob.actividad_id==job.actividad_id,models.UploadJob.estudiante_id==job.estudiante_id,models.UploadJob.status.in_(['pending','running'])).first():
            raise HTTPException(409,'Ya existe una carga pendiente o en proceso para este alumno y evaluación')
        if not Path(job.file_path).is_file():raise HTTPException(409,'El archivo ya no está disponible; vuelve a subirlo')
        job.status='pending';job.error=None;job.usuario_id=user.id
    else:raise HTTPException(404,'Acción no encontrada')
    db.commit();db.refresh(job)
    log_audit(db,'COLA_'+action.upper(),'upload_jobs',job.id,user.id)
    return public_job(job)

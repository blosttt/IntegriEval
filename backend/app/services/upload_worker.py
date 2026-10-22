import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, UploadFile
from sqlalchemy import update
from backend.app import models
from backend.app.auth import check_course_access


async def process_one(session_factory):
    with session_factory() as db:
        cutoff=datetime.now(timezone.utc)-timedelta(minutes=30)
        db.query(models.UploadJob).filter(models.UploadJob.status=='running',models.UploadJob.started_at<cutoff).update({'status':'failed','error':'Procesamiento interrumpido o demasiado largo; puedes reintentar'})
        db.commit()
        job=db.query(models.UploadJob).filter_by(status='pending').order_by(models.UploadJob.id).first()
        if not job:return False
        claimed=db.execute(update(models.UploadJob).where(models.UploadJob.id==job.id,models.UploadJob.status=='pending').values(status='running',attempts=models.UploadJob.attempts+1,started_at=datetime.now(timezone.utc),error=None))
        db.commit()
        if claimed.rowcount!=1:return True
        db.refresh(job)
        try:
            user=db.get(models.Usuario,job.usuario_id)
            status=db.get(models.AccountStatus,job.usuario_id)
            if not user or (status and not status.active):raise HTTPException(403,'La cuenta que solicitó la carga está desactivada')
            check_course_access(job.asignatura_id,user,db,write=True)
            student_status=db.get(models.StudentStatus,job.estudiante_id)
            if student_status and not student_status.active:raise HTTPException(409,'El alumno fue retirado del curso')
            from backend.app.routers.trabajos import upload_trabajo_single
            with open(job.file_path,'rb') as file:
                await upload_trabajo_single(job.asignatura_id,job.estudiante_id,job.actividad_id,UploadFile(filename=job.filename,file=file),user,db)
            job.status='completed';job.error=None
        except HTTPException as error:
            db.rollback();job=db.get(models.UploadJob,job.id);job.status='failed';job.error=str(error.detail)[:500]
        except Exception:
            db.rollback();job=db.get(models.UploadJob,job.id);job.status='failed';job.error='No se pudo procesar el archivo; revisa el PDF y la configuración antes de reintentar'
        job.finished_at=datetime.now(timezone.utc);db.commit()
        return True


def process_in_thread(session_factory):
    return asyncio.run(process_one(session_factory))


async def upload_loop(session_factory):
    while True:
        try:
            worked=await asyncio.to_thread(process_in_thread,session_factory)
        except Exception:
            import logging
            logging.getLogger(__name__).exception('Error en el procesador de informes')
            worked=False
        await asyncio.sleep(0.2 if worked else 2)

"use client";
import {useState} from 'react';
import Dialog from './Dialog';
import {request} from '@/lib/api';
export default function StudentEditor({courseId,student,onClose,onSaved}:{courseId:number;student?:any;onClose:()=>void;onSaved:()=>void}){
  const [error,setError]=useState(''),[busy,setBusy]=useState(false);
  const submit=async(event:React.FormEvent<HTMLFormElement>)=>{
    event.preventDefault();setBusy(true);setError('');const data=Object.fromEntries(new FormData(event.currentTarget));
    try{await request(`/asignaturas/${courseId}/estudiantes${student?'/'+student.id:''}`,student?'PUT':'POST',data);onSaved();onClose();}
    catch(e:any){setError(e.message);}finally{setBusy(false);}
  };
  return <Dialog title={student?'Editar estudiante':'Agregar estudiante'} onClose={onClose}>
    <form onSubmit={submit}><div className="ie-form">{error&&<p role="alert" className="ie-error">{error}</p>}
      <label>Nombre completo<input name="nombre" defaultValue={student?.nombre||student?.name||''} required maxLength={150}/></label>
      <label>Correo institucional<input name="correo" type="email" defaultValue={student?.correo||student?.email||''} required/></label>
      <label>RUT (opcional)<input name="rut" defaultValue={student?.rut||''} maxLength={20}/></label>
      <p className="ie-muted">El estudiante accederá únicamente al Flash Test mediante su enlace personal, sin crear una cuenta.</p>
    </div><footer className="ie-dialog-footer"><button type="button" className="ie-button" onClick={onClose}>Cancelar</button><button disabled={busy} className="ie-button ie-primary">{busy?'Guardando…':'Guardar estudiante'}</button></footer></form>
  </Dialog>;
}

"use client";
import {useState} from 'react';
import Dialog from './Dialog';

export default function AppointmentForm({students,initial,onSave,onClose}:{students:any[];initial?:any;onSave:(studentId:number,date:string,block:string)=>Promise<void>;onClose:()=>void}){
 const local=(value:string)=>{const d=new Date(value);return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16);};
 const [student,setStudent]=useState(String(initial?.estudiante_id||''));
 const [date,setDate]=useState(initial?.scheduled_time?local(initial.scheduled_time):'');
 const [end,setEnd]=useState(initial?.bloque?.split(' - ')[1]||'');
 const [error,setError]=useState(''),[saving,setSaving]=useState(false);
 return <Dialog title={initial?.id?'Reprogramar cita de revisión':'Agendar cita de revisión'} onClose={onClose}><form className="ie-form" onSubmit={async e=>{e.preventDefault();const start=date.slice(11,16);if(new Date(date).getTime()<=Date.now()){setError('Elige una fecha y hora futuras.');return;}if(end<=start){setError('La hora de término debe ser posterior al inicio.');return;}setSaving(true);setError('');try{await onSave(Number(student),new Date(date).toISOString(),`${start} - ${end}`);onClose();}catch(err:any){setError(err.message);}finally{setSaving(false);}}}>
 <label>Estudiante<select required value={student} disabled={!!initial?.estudiante_id} onChange={e=>setStudent(e.target.value)}><option value="">Selecciona un alumno</option>{students.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select></label>
 <label>Fecha y hora de inicio<input aria-label="Fecha y hora de inicio" type="datetime-local" required value={date} onChange={e=>setDate(e.target.value)}/></label>
 <label>Hora de término<input aria-label="Hora de término" type="time" required value={end} onChange={e=>setEnd(e.target.value)}/></label>
 {error&&<p role="alert">{error}</p>}<button className="ie-button ie-primary" disabled={saving}>{saving?'Guardando…':'Guardar cita'}</button>
 </form></Dialog>;
}

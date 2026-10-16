"use client";
import {useState} from 'react';
import Link from 'next/link';
import {ArrowLeft,ShieldCheck,Plus,Pencil,UserMinus} from 'lucide-react';
import Dialog from './Dialog';
import {request} from '@/lib/api';

export default function AdminTeacherContext({person,courses,onChanged}:{person:any;courses:any[];onChanged:()=>void}){
  const [open,setOpen]=useState(false),[editor,setEditor]=useState<any>(null),[allCourses,setAllCourses]=useState<any[]>([]),[error,setError]=useState(''),[busy,setBusy]=useState(false),[remove,setRemove]=useState<any>(null);
  const manage=async()=>{setOpen(true);setError('');try{setAllCourses(await request('/asignaturas'));}catch(e:any){setError(e.message);}};
  const save=async(e:React.FormEvent<HTMLFormElement>)=>{e.preventDefault();setBusy(true);setError('');const d:any=Object.fromEntries(new FormData(e.currentTarget));d.ano=Number(d.ano);
    try{await request(editor.id?`/asignaturas/${editor.id}`:`/admin/profesores/${person.id}/asignaturas`,editor.id?'PUT':'POST',d);setEditor(null);setOpen(false);onChanged();}catch(e:any){setError(e.message);}finally{setBusy(false);}
  };
  return <>
    <aside className="ie-context-banner"><div><Link href="/admin/dashboard" className="ie-context-back"><ArrowLeft size={16}/>Volver a Super admin</Link><strong><ShieldCheck size={17}/>Vista de {person.nombre}</strong><p>Actúas como superadministrador. Puedes modificar este espacio; la auditoría conserva tu identidad.</p></div><button className="ie-button" onClick={manage}>Gestionar asignaturas</button></aside>
    {open&&!editor&&!remove&&<Dialog title={`Asignaturas de ${person.nombre}`} onClose={()=>setOpen(false)} wide><div className="ie-form">
      {error&&<p className="ie-error" role="alert">{error}</p>}
      {courses.length?<div className="ie-course-list">{courses.map(c=><div className="ie-course" key={c.id}><span><strong>{c.name}</strong><p className="ie-muted">{c.period} · {c.ano}</p></span><div className="ie-actions"><button className="ie-button" onClick={()=>{setEditor(c);setError('');}}><Pencil size={15}/>Editar</button><button className="ie-button ie-danger-text" onClick={()=>setRemove(c)}><UserMinus size={15}/>Retirar acceso</button></div></div>)}</div>:<p>Este docente todavía no tiene asignaturas.</p>}
      <button className="ie-button ie-primary" onClick={()=>{setEditor({});setError('');}}><Plus size={16}/>Crear y asignar una asignatura</button>
      <form className="ie-inline-form" onSubmit={async e=>{e.preventDefault();setBusy(true);setError('');const id=String(new FormData(e.currentTarget).get('course'));try{await request(`/admin/asignaturas/${id}/profesores`,'POST',{usuario_id:person.id});setOpen(false);onChanged();}catch(e:any){setError(e.message);}finally{setBusy(false);}}}><label>Asignar una existente<select name="course" required defaultValue=""><option value="" disabled>Selecciona una asignatura…</option>{allCourses.filter(c=>!courses.some(assigned=>assigned.id===c.id)).map(c=><option key={c.id} value={c.id}>{c.nombre} · {c.periodo}</option>)}</select></label><button className="ie-button" disabled={busy}>Asignar</button></form>
    </div></Dialog>}
    {editor&&<Dialog title={editor.id?'Editar asignatura':'Crear y asignar asignatura'} onClose={()=>setEditor(null)}><form onSubmit={save}><div className="ie-form">{error&&<p className="ie-error" role="alert">{error}</p>}<label>Nombre<input name="nombre" defaultValue={editor.name||''} maxLength={150} required/></label><label>Período<input name="periodo" defaultValue={editor.period||'Semestre 2'} maxLength={50} required/></label><label>Año<input name="ano" type="number" min={2000} max={2200} defaultValue={editor.ano||new Date().getFullYear()} required/></label></div><footer className="ie-dialog-footer"><button type="button" className="ie-button" onClick={()=>setEditor(null)}>Cancelar</button><button className="ie-button ie-primary" disabled={busy}>{busy?'Guardando…':'Guardar'}</button></footer></form></Dialog>}
    {remove&&<Dialog title="Retirar acceso a la asignatura" onClose={()=>setRemove(null)}><div className="ie-form"><p>{person.nombre} perderá el acceso a {remove.name}. Los datos del curso se conservarán.</p>{error&&<p className="ie-error">{error}</p>}</div><footer className="ie-dialog-footer"><button className="ie-button" onClick={()=>setRemove(null)}>Cancelar</button><button disabled={busy} className="ie-button ie-primary" onClick={async()=>{setBusy(true);try{await request(`/admin/asignaturas/${remove.id}/profesores/${person.id}`,'DELETE');setRemove(null);setOpen(false);onChanged();}catch(e:any){setError(e.message);}finally{setBusy(false);}}}>Retirar acceso</button></footer></Dialog>}
  </>;
}

"use client";
import {useEffect,useState} from 'react';
import {useRouter} from 'next/navigation';
import Link from 'next/link';
import {Search,Plus,ArrowRight,Pencil,ShieldCheck,GraduationCap,Users} from 'lucide-react';
import IntegrationStatus from './IntegrationStatus';
import Navbar from './Navbar';
import Dialog from './Dialog';
import {api,request} from '@/lib/api';

export default function SuperAdmin(){
  const router=useRouter();
  const [people,setPeople]=useState<any[]>([]),[ready,setReady]=useState(false),[query,setQuery]=useState(''),[editor,setEditor]=useState<any>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const load=async()=>setPeople(await request('/admin/profesores'));
  useEffect(()=>{api.getMe().then(u=>{if(u.rol!=='admin'){router.replace('/');return;}setReady(true);load().catch(e=>setError(e.message));}).catch(()=>router.replace('/#acceso'));},[]);
  const save=async(e:React.FormEvent<HTMLFormElement>)=>{e.preventDefault();setBusy(true);setError('');const data:any=Object.fromEntries(new FormData(e.currentTarget));data.active=data.active==='true';if(!data.contrasena)delete data.contrasena;
    try{await request('/admin/profesores'+(editor.id?'/'+editor.id:''),editor.id?'PUT':'POST',data);await load();setEditor(null);}catch(e:any){setError(e.message);}finally{setBusy(false);}
  };
  const visible=people.filter(p=>`${p.nombre} ${p.correo}`.toLowerCase().includes(query.toLowerCase()));
  return <div className="ie-shell"><Navbar/><main className="ie-workspace ie-directory">
    <header className="ie-page-heading"><div><span className="ie-eyebrow"><ShieldCheck size={16}/>Super admin</span><h1>Selecciona un docente</h1><p>Abre su espacio de trabajo para revisar y administrar sus cursos con tus permisos de superadministrador.</p></div><button className="ie-button ie-primary" onClick={()=>{setEditor({});setError('');}}><Plus size={16}/>Agregar docente</button></header>
    {!ready?<p className="ie-empty">Verificando acceso…</p>:<>
      <IntegrationStatus/><label className="ie-directory-search"><Search size={18}/><input aria-label="Buscar profesor o ayudante" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Buscar por nombre o correo"/><span>{visible.length} docentes</span></label>
      {error&&!editor&&<p role="alert" className="ie-error">{error}</p>}
      <div className="ie-person-grid">{visible.map(person=><article className="ie-person-card" key={person.id}>
        <div className="ie-person-top"><span className="ie-person-avatar">{person.rol==='ayudante'?<Users size={24}/>:<GraduationCap size={24}/>}</span><span className={`ie-badge ${person.active?'teacher':'inactive'}`}>{person.active?'Activo':'Desactivado'}</span></div>
        <h2><Link href={`/teacher/dashboard?profesor=${person.id}`}>{person.nombre}</Link></h2><p>{person.correo}</p><div className="ie-person-meta"><span>{person.rol==='ayudante'?'Ayudante':'Profesor'}</span><span>{person.asignaturas.length} asignaturas</span></div>
        <footer><Link className="ie-button ie-primary" href={`/teacher/dashboard?profesor=${person.id}`}>Abrir vista<ArrowRight size={16}/></Link><button className="ie-icon-button" aria-label={`Editar cuenta de ${person.nombre}`} onClick={()=>{setEditor(person);setError('');}}><Pencil size={17}/></button></footer>
      </article>)}</div>{!visible.length&&<p className="ie-empty">{people.length?'No se encontraron docentes con esa búsqueda.':'Agrega el primer profesor o ayudante para comenzar.'}</p>}
    </>}
    {editor&&<Dialog title={editor.id?'Editar cuenta docente':'Agregar profesor o ayudante'} onClose={()=>setEditor(null)}><form onSubmit={save}><div className="ie-form">
      {error&&<p className="ie-error" role="alert">{error}</p>}
      <label>Nombre completo<input name="nombre" defaultValue={editor.nombre||''} required maxLength={120}/></label><label>Correo institucional<input name="correo" type="email" defaultValue={editor.correo||''} required/></label>
      <label>Perfil<select name="rol" defaultValue={editor.rol||'docente'} disabled={!!editor.id}><option value="docente">Profesor</option><option value="ayudante">Ayudante · sin edición de alumnos</option></select></label>
      <label>{editor.id?'Nueva contraseña (opcional)':'Contraseña inicial'}<input name="contrasena" type="password" autoComplete="new-password" minLength={6} required={!editor.id}/></label>
      <label>Estado<select name="active" defaultValue={editor.active===false?'false':'true'}><option value="true">Activo</option><option value="false">Desactivado</option></select></label>
    </div><footer className="ie-dialog-footer"><button type="button" className="ie-button" onClick={()=>setEditor(null)}>Cancelar</button><button className="ie-button ie-primary" disabled={busy}>{busy?'Guardando…':'Guardar cuenta'}</button></footer></form></Dialog>}
  </main></div>;
}

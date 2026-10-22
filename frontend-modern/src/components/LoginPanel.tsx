"use client";
import Link from 'next/link';
import {useState} from 'react';
import {useRouter} from 'next/navigation';
import {LogIn,GraduationCap,Users,ShieldCheck} from 'lucide-react';
import {api} from '@/lib/api';

export default function LoginPanel(){
  const router=useRouter();
  const [role,setRole]=useState('teacher'),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const options=[{id:'teacher',label:'Docente',icon:GraduationCap,detail:'Accede a las asignaturas que te han asignado.'},{id:'assistant',label:'Ayudante',icon:Users,detail:'Trabaja en la evaluación con la nómina de solo lectura.'},{id:'admin',label:'Super admin',icon:ShieldCheck,detail:'Selecciona un docente para administrar su espacio de trabajo.'}];
  const submit=async(event:React.FormEvent<HTMLFormElement>)=>{event.preventDefault();setBusy(true);setError('');const form=new FormData(event.currentTarget);
    try{const data=await api.login(String(form.get('email')),String(form.get('password')));router.push(data.role==='admin'?'/admin/dashboard':data.role==='assistant'?'/assistant/dashboard':'/teacher/dashboard');}
    catch(e:any){setError(e.message);}finally{setBusy(false);}
  };
  return <section className="ie-login-panel" id="acceso" aria-labelledby="login-title">
    <div className="ie-login-heading"><LogIn size={19}/><h2 id="login-title">Ingresa a IntegryEval</h2></div>
    <div className="ie-login-tabs" role="tablist" aria-label="Tipo de acceso">{options.map(option=><button key={option.id} type="button" role="tab" id={`login-tab-${option.id}`} aria-selected={role===option.id} aria-controls="login-content" onClick={()=>{setRole(option.id);setError('');}}><option.icon size={16}/>{option.label}</button>)}</div>
    <div role="tabpanel" id="login-content" aria-labelledby={`login-tab-${role}`}><p className="ie-muted">{options.find(o=>o.id===role)?.detail}</p>
    <form className="ie-login-form" onSubmit={submit}>
      <label>Correo institucional<input name="email" type="email" autoComplete="username" placeholder="nombre@universidad.cl" required/></label>
      <label>Contraseña<input name="password" type="password" autoComplete="current-password" placeholder="Tu contraseña" required/></label>
      {error&&<p className="ie-error" role="alert">{error}</p>}
      <button className="ie-button ie-primary" disabled={busy}>{busy?'Ingresando…':`Ingresar como ${role==='admin'?'super administrador':role==='assistant'?'ayudante':'docente'}`}<LogIn size={16}/></button>
    </form><Link className="ie-button" href="/recuperar">Olvidé mi contraseña</Link><p className="ie-login-note">El perfil y los permisos se validan con tu cuenta. Los estudiantes acceden por el enlace personal enviado a su correo.</p></div>
  </section>;
}

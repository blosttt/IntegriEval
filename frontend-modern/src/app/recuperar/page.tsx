"use client";
import {useEffect,useState} from 'react';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import {request} from '@/lib/api';

export default function Recover(){
 const [token,setToken]=useState(''),[message,setMessage]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false),[done,setDone]=useState(false);
 useEffect(()=>{setToken(new URLSearchParams(location.search).get('token')||'');},[]);
 return <div className="ie-shell"><Navbar/><main className="ie-student-main"><section className="ie-panel ie-student-panel"><h1>{token?'Nueva contraseña':'Recuperar acceso'}</h1><p>{token?'El enlace se puede usar una sola vez y caduca en 30 minutos.':'Ingresa el correo de tu cuenta docente o administrativa.'}</p>{!done&&<form className="ie-form" onSubmit={async e=>{e.preventDefault();setBusy(true);setError('');const data=new FormData(e.currentTarget);if(token&&data.get('password')!==data.get('confirm')){setError('Las contraseñas no coinciden.');setBusy(false);return;}try{const result=await request('/auth/'+(token?'reset-password':'forgot-password'),'POST',token?{token,contrasena:String(data.get('password'))}:{correo:String(data.get('email'))});setMessage(result.message);setDone(true);if(token){history.replaceState(null,'','/recuperar');setToken('');}}catch(err:any){setError(err.message);}finally{setBusy(false);}}}>{token?<><label>Nueva contraseña<input name="password" type="password" autoComplete="new-password" minLength={10} required/></label><label>Confirmar contraseña<input name="confirm" type="password" autoComplete="new-password" minLength={10} required/></label></>:<label>Correo institucional<input name="email" type="email" autoComplete="email" required/></label>}<button className="ie-button ie-primary" disabled={busy}>{busy?'Procesando…':token?'Guardar nueva contraseña':'Solicitar enlace'}</button></form>}{message&&<p role="status">{message}</p>}{error&&<p className="ie-error" role="alert">{error}</p>}<Link className="ie-button" href="/#acceso">Volver al inicio de sesión</Link></section></main></div>;
}

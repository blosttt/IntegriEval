"use client";
import Link from 'next/link';
import {useEffect,useState} from 'react';
import Navbar from '@/components/Navbar';
import LoginPanel from '@/components/LoginPanel';
import {api,getToken} from '@/lib/api';
export default function Home(){
 const [user,setUser]=useState<any>(null);
 useEffect(()=>{let active=true;const sync=()=>{if(!getToken()){setUser(null);return;}api.getMe().then(value=>{if(active&&getToken())setUser(value);}).catch(()=>{if(active)setUser(null);});};sync();window.addEventListener('integryeval:session-changed',sync);return()=>{active=false;window.removeEventListener('integryeval:session-changed',sync);};},[]);
 const href=user?.rol==='admin'?'/admin/dashboard':user?.rol==='ayudante'?'/assistant/dashboard':'/teacher/dashboard';
 return <div className="ie-home"><Navbar/><main className="ie-home-main"><section className="ie-hero ie-hero-with-login"><h1>Crea, administra y revisa<br className="ie-desktop-break"/> evaluaciones</h1><p>Conoce la nueva forma de evaluar en esta era de inteligencia artificial.</p><div className="ie-hero-actions"><Link href={user?href:'#acceso'} className="ie-button ie-primary">{user?.rol==='admin'?'Super admin':user?.rol==='ayudante'?'Portal del Ayudante':'Portal del Docente'}</Link><Link href="/student/dashboard" className="ie-button">Portal del Alumno</Link></div></section>{user?<section className="ie-home-session" id="acceso"><p>Sesión activa como <strong>{user.nombre}</strong></p><Link href={href} className="ie-button ie-primary">Continuar a mi espacio de trabajo</Link><p className="ie-muted">Para cambiar de cuenta, cierra tu sesión desde la cabecera.</p></section>:<LoginPanel/>}</main><footer className="ie-home-footer">IntegryEval · Evaluación auténtica y verificación de comprensión</footer></div>;
}

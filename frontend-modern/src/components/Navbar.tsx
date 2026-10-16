"use client";
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {usePathname,useRouter} from 'next/navigation';
import {LogOut,Moon,Sun,HelpCircle} from 'lucide-react';
import {api,getToken,logout} from '@/lib/api';
export default function Navbar(){
 const router=useRouter(),path=usePathname();
 const [user,setUser]=useState<any>(null),[light,setLight]=useState(false);
 useEffect(()=>{if(getToken())api.getMe().then(setUser).catch(()=>{setUser(null);});const value=localStorage.getItem('integryeval:theme')||'dark';setLight(value==='light');document.documentElement.dataset.appTheme=value;},[]);
 const toggle=()=>{const next=light?'dark':'light';setLight(!light);document.documentElement.dataset.appTheme=next;localStorage.setItem('integryeval:theme',next);};
 const role=user?.rol;const teacher=role==='docente'||role==='admin'||role==='ayudante';
 return <header className="ie-navbar"><div className="ie-navbar-left">
   <Link href="/" className="ie-brand" aria-label="IntegryEval · Inicio"><span className="ie-uct-symbol"><img src="/uct-logo.png" alt="Universidad Católica de Temuco" width={108} height={38}/></span><span>IntegryEval</span></Link>
   <nav aria-label="Navegación principal">{role==='admin'?<Link href="/admin/dashboard" className={path.startsWith('/admin')||path.startsWith('/teacher')?'selected':''}>Super admin</Link>:<Link href={teacher?(role==='ayudante'?'/assistant/dashboard':'/teacher/dashboard'):'/#acceso'} className={path.startsWith('/teacher')||path.startsWith('/assistant')?'selected':''}>{role==='ayudante'?'Ayudante':'Docente'}</Link>}<Link href="/student/dashboard" className={path.startsWith('/student')?'selected':''}>Alumno</Link></nav>
 </div><div className="ie-navbar-right">
   {user?<><span className="ie-avatar" aria-hidden="true">{user.nombre.split(' ').map((s:string)=>s[0]).slice(0,2).join('')}</span><span className="ie-user-name">{user.nombre}</span><span className={`ie-badge ${role==='admin'?'admin':role==='docente'?'teacher':'inactive'}`}>{role==='admin'?'Superadministrador':role==='docente'?'Docente':'Ayudante'}</span>{(path.startsWith('/teacher')||path.startsWith('/assistant'))&&<button className="ie-icon-button" title="Guía de uso" aria-label="Guía de uso" onClick={()=>window.dispatchEvent(new Event('integryeval:open-tutorial'))}><HelpCircle size={19}/></button>}<button className="ie-icon-button" title="Cerrar sesión" aria-label="Cerrar sesión" onClick={()=>{logout();setUser(null);router.push('/');}}><LogOut size={18}/></button></>:<Link className="ie-button" href="/#acceso">Ingresar</Link>}
   <button className="ie-icon-button" onClick={toggle} aria-label={light?'Activar tema oscuro':'Activar tema claro'}>{light?<Sun size={18}/>:<Moon size={18}/>}</button>
 </div></header>;
}

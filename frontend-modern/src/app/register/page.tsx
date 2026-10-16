import Link from 'next/link';
import Navbar from '@/components/Navbar';
export default function Register(){return <div className="ie-shell"><Navbar/><main className="ie-student-main"><section className="ie-panel ie-student-panel"><h1>Acceso administrado</h1><p>El administrador crea las cuentas docentes y asigna sus cursos. Solicita tu acceso a la administración.</p><p>Los estudiantes acceden únicamente por el enlace de Flash Test enviado a su correo.</p><Link className="ie-button ie-primary" href="/login">Volver al ingreso</Link></section></main></div>;}

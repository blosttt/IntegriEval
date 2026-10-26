import Link from "next/link";
import Navbar from "@/components/Navbar";
import {
  buttonClasses,
  shellClasses,
  studentHeadingClasses,
  studentMainClasses,
  studentPanelClasses,
} from "@/components/ui";

export default function Register() {
  return (
    <div className={shellClasses}>
      <Navbar />
      <main className={studentMainClasses}>
        <section className={studentPanelClasses}>
          <h1 className={studentHeadingClasses}>Acceso administrado</h1>
          <p>
            El administrador crea las cuentas docentes y asigna sus cursos. Solicita tu acceso a la
            administración.
          </p>
          <p>Los estudiantes acceden únicamente por el enlace de Flash Test enviado a su correo.</p>
          <Link className={buttonClasses("primary", "classic")} href="/login">
            Volver al ingreso
          </Link>
        </section>
      </main>
    </div>
  );
}

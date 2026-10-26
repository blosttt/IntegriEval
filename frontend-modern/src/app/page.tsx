"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import LoginPanel from "@/components/LoginPanel";
import { MutedText, buttonClasses, cx } from "@/components/ui";
import { api, getToken } from "@/lib/api";

export default function Home() {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    let active = true;
    const sync = () => {
      if (!getToken()) {
        setUser(null);
        return;
      }
      api
        .getMe()
        .then((value) => {
          if (active && getToken()) setUser(value);
        })
        .catch(() => {
          if (active) setUser(null);
        });
    };
    sync();
    window.addEventListener("integryeval:session-changed", sync);
    return () => {
      active = false;
      window.removeEventListener("integryeval:session-changed", sync);
    };
  }, []);

  const href =
    user?.rol === "admin"
      ? "/admin/dashboard"
      : user?.rol === "ayudante"
        ? "/assistant/dashboard"
        : "/teacher/dashboard";

  return (
    <div className="flex min-h-screen flex-col bg-canvas font-ui text-fg">
      <Navbar />
      <main className="flex-1">
        <section className="mx-auto w-full max-w-[1120px] flex-1 px-6 pt-[78px] pb-10 text-center max-[700px]:px-5 max-[700px]:pt-[55px] max-[700px]:pb-8">
          <h1 className="mx-auto max-w-[930px] text-[clamp(34px,4vw,52px)] leading-[1.15] font-[750] tracking-[-1.9px] text-fg max-[720px]:tracking-[-1px] max-[700px]:text-[35px]">
            Crea, administra y revisa
            <br className="max-[720px]:hidden" /> evaluaciones
          </h1>
          <p className="mx-auto mt-[22px] mb-[34px] max-w-[800px] text-[19px] leading-[1.6] text-muted max-[720px]:max-w-[450px] max-[720px]:text-base">
            Conoce la nueva forma de evaluar en esta era de inteligencia artificial.
          </p>
          <div className="flex justify-center gap-[15px] max-[720px]:flex-wrap">
            <Link href={user ? href : "#acceso"} className={buttonClasses("primary", "hero")}>
              {user?.rol === "admin"
                ? "Super admin"
                : user?.rol === "ayudante"
                  ? "Portal del Ayudante"
                  : "Portal del Docente"}
            </Link>
            <Link href="/student/dashboard" className={buttonClasses("surface", "hero")}>
              Portal del Alumno
            </Link>
          </div>
        </section>
        {user ? (
          <section
            className="mx-auto mb-[70px] max-w-[510px] rounded-[10px] border border-line bg-surface p-6 text-center max-[700px]:mx-5"
            id="acceso"
          >
            <p className="mb-[18px] text-sm">
              Sesión activa como <strong>{user.nombre}</strong>
            </p>
            <Link href={href} className={buttonClasses("primary", "classic")}>
              Continuar a mi espacio de trabajo
            </Link>
            <MutedText>Para cambiar de cuenta, cierra tu sesión desde la cabecera.</MutedText>
          </section>
        ) : (
          <LoginPanel />
        )}
      </main>
      <footer className={cx("p-6 text-center text-[11px] text-muted opacity-65")}>
        IntegryEval · Evaluación auténtica y verificación de comprensión
      </footer>
    </div>
  );
}

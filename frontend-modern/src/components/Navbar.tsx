"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LogOut, Moon, Sun, HelpCircle } from "lucide-react";
import { api, getToken, logout } from "@/lib/api";
import { Badge, IconButton, buttonClasses, cx } from "./ui";

const navLink = (selected: boolean) =>
  cx("py-2 no-underline", selected ? "text-fg underline underline-offset-[5px]" : "text-muted");

export default function Navbar() {
  const router = useRouter();
  const path = usePathname();
  const [user, setUser] = useState<any>(null);
  const [light, setLight] = useState(false);

  useEffect(() => {
    if (getToken())
      api
        .getMe()
        .then(setUser)
        .catch(() => {
          setUser(null);
        });
    const value = localStorage.getItem("integryeval:theme") || "dark";
    setLight(value === "light");
    document.documentElement.dataset.appTheme = value;
  }, []);

  const toggle = () => {
    const next = light ? "dark" : "light";
    setLight(!light);
    document.documentElement.dataset.appTheme = next;
    localStorage.setItem("integryeval:theme", next);
  };

  const role = user?.rol;
  const teacher = role === "docente" || role === "admin" || role === "ayudante";
  const inTeacherArea = path.startsWith("/teacher") || path.startsWith("/assistant");

  return (
    <header className="flex min-h-[66px] w-full items-center justify-between gap-5 border-b border-line/60 bg-canvas px-6 py-3 font-ui text-fg max-[1000px]:px-[18px] max-[720px]:flex-wrap max-[720px]:gap-3">
      <div className="flex items-center gap-[42px] max-[1000px]:gap-6 max-[720px]:w-full max-[720px]:justify-between max-[720px]:gap-3">
        <Link
          href="/"
          className="flex items-center gap-2.5 text-[21px] font-bold whitespace-nowrap text-fg no-underline max-[720px]:text-[19px]"
          aria-label="IntegryEval · Inicio"
        >
          <span className="relative size-9 shrink-0 overflow-hidden rounded-full">
            <img
              src="/uct-logo.png"
              alt="Universidad Católica de Temuco"
              width={108}
              height={38}
              className="absolute top-0 left-0 h-[38px] w-[108px] max-w-none"
            />
          </span>
          <span>IntegryEval</span>
        </Link>
        <nav
          aria-label="Navegación principal"
          className="flex items-center gap-[30px] text-[15px] font-semibold max-[1000px]:gap-5 max-[720px]:gap-4 max-[720px]:text-[13px]"
        >
          {role === "admin" ? (
            <Link
              href="/admin/dashboard"
              className={navLink(path.startsWith("/admin") || path.startsWith("/teacher"))}
            >
              Super admin
            </Link>
          ) : (
            <Link
              href={
                teacher
                  ? role === "ayudante"
                    ? "/assistant/dashboard"
                    : "/teacher/dashboard"
                  : "/#acceso"
              }
              className={navLink(inTeacherArea)}
            >
              {role === "ayudante" ? "Ayudante" : "Docente"}
            </Link>
          )}
          <Link href="/student/dashboard" className={navLink(path.startsWith("/student"))}>
            Alumno
          </Link>
        </nav>
      </div>
      <div className="flex items-center gap-3 max-[1000px]:gap-2 max-[720px]:ml-auto">
        {user ? (
          <>
            <span
              className="grid size-[30px] place-items-center rounded-full bg-[#344656] text-[10px] font-bold text-[#e5edf5] max-[720px]:hidden"
              aria-hidden="true"
            >
              {user.nombre
                .split(" ")
                .map((s: string) => s[0])
                .slice(0, 2)
                .join("")}
            </span>
            <span className="max-w-[280px] overflow-hidden text-xs text-ellipsis whitespace-nowrap uppercase max-[1000px]:max-w-40 max-[720px]:max-w-[180px] max-[720px]:text-[10px]">
              {user.nombre}
            </span>
            <Badge tone={role === "admin" ? "admin" : role === "docente" ? "teacher" : "inactive"}>
              {role === "admin" ? "Superadministrador" : role === "docente" ? "Docente" : "Ayudante"}
            </Badge>
            {inTeacherArea && (
              <IconButton
                title="Guía de uso"
                aria-label="Guía de uso"
                onClick={() => window.dispatchEvent(new Event("integryeval:open-tutorial"))}
              >
                <HelpCircle size={19} />
              </IconButton>
            )}
            <IconButton
              title="Cerrar sesión"
              aria-label="Cerrar sesión"
              onClick={() => {
                logout();
                setUser(null);
                router.push("/");
              }}
            >
              <LogOut size={18} />
            </IconButton>
          </>
        ) : (
          <Link className={buttonClasses("surface", "classic")} href="/#acceso">
            Ingresar
          </Link>
        )}
        <IconButton onClick={toggle} aria-label={light ? "Activar tema oscuro" : "Activar tema claro"}>
          {light ? <Sun size={18} /> : <Moon size={18} />}
        </IconButton>
      </div>
    </header>
  );
}

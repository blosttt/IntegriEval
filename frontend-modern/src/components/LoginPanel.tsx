"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { LogIn, GraduationCap, Users, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import { Banner, Button, FormField, FormInput, MutedText, cx } from "./ui";

const OPTIONS = [
  {
    id: "teacher",
    label: "Docente",
    icon: GraduationCap,
    detail: "Accede a las asignaturas que te han asignado.",
  },
  {
    id: "assistant",
    label: "Ayudante",
    icon: Users,
    detail: "Trabaja en la evaluación con la nómina de solo lectura.",
  },
  {
    id: "admin",
    label: "Super admin",
    icon: ShieldCheck,
    detail: "Selecciona un docente para administrar su espacio de trabajo.",
  },
];

export default function LoginPanel() {
  const router = useRouter();
  const [role, setRole] = useState("teacher");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      const data = await api.login(String(form.get("email")), String(form.get("password")));
      router.push(
        data.role === "admin"
          ? "/admin/dashboard"
          : data.role === "assistant"
            ? "/assistant/dashboard"
            : "/teacher/dashboard",
      );
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section
      className="mx-auto mb-[54px] w-[calc(100%-40px)] max-w-[510px] scroll-mt-6 rounded-[10px] border border-line bg-surface p-6 max-[700px]:p-5"
      id="acceso"
      aria-labelledby="login-title"
    >
      <div className="mb-[22px] flex items-center justify-center gap-2.5 text-fg">
        <LogIn size={19} />
        <h2 id="login-title" className="text-[19px] font-semibold text-fg">
          Ingresa a IntegryEval
        </h2>
      </div>
      <div
        className="mb-[18px] flex gap-1 border-b border-line"
        role="tablist"
        aria-label="Tipo de acceso"
      >
        {OPTIONS.map((option) => (
          <button
            key={option.id}
            type="button"
            role="tab"
            id={`login-tab-${option.id}`}
            aria-selected={role === option.id}
            aria-controls="login-content"
            className={cx(
              "flex flex-1 cursor-pointer items-center justify-center gap-[7px] border-b-2 px-1 py-3 text-xs font-semibold",
              role === option.id ? "border-brand text-[#75c5f1]" : "border-transparent text-muted",
            )}
            onClick={() => {
              setRole(option.id);
              setError("");
            }}
          >
            <option.icon size={16} />
            {option.label}
          </button>
        ))}
      </div>
      <div role="tabpanel" id="login-content" aria-labelledby={`login-tab-${role}`}>
        <MutedText>{OPTIONS.find((o) => o.id === role)?.detail}</MutedText>
        <form className="flex flex-col gap-[17px]" onSubmit={submit}>
          <FormField label="Correo institucional">
            <FormInput
              className="p-3 text-sm"
              name="email"
              type="email"
              autoComplete="username"
              placeholder="nombre@universidad.cl"
              required
            />
          </FormField>
          <FormField label="Contraseña">
            <FormInput
              className="p-3 text-sm"
              name="password"
              type="password"
              autoComplete="current-password"
              placeholder="Tu contraseña"
              required
            />
          </FormField>
          {error && (
            <Banner tone="error" role="alert">
              {error}
            </Banner>
          )}
          <Button type="submit" size="classicWide" disabled={busy}>
            {busy
              ? "Ingresando…"
              : `Ingresar como ${role === "admin" ? "super administrador" : role === "assistant" ? "ayudante" : "docente"}`}
            <LogIn size={16} />
          </Button>
        </form>
        <p className="mt-5 text-center text-[11px] leading-[1.7] text-muted">
          El perfil y los permisos se validan con tu cuenta. Los estudiantes acceden por el enlace
          personal enviado a su correo.
        </p>
      </div>
    </section>
  );
}

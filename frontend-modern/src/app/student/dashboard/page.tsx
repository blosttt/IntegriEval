"use client";

import { useState, type FormEvent } from "react";
import { Mail, ArrowRight, LockKeyhole } from "lucide-react";
import Navbar from "@/components/Navbar";
import { api } from "@/lib/api";
import {
  Banner,
  Button,
  FormField,
  FormInput,
  MutedText,
  shellClasses,
  studentHeadingClasses,
  studentMainClasses,
  studentPanelClasses,
} from "@/components/ui";

export default function StudentPortal() {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const open = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setBusy(true);
    const raw = String(new FormData(event.currentTarget).get("link") || "").trim();
    let token = raw;
    try {
      if (raw.includes("://")) token = new URL(raw).pathname.split("/").filter(Boolean).pop() || "";
      const data = await api.validateFlashToken(token);
      if (data.estado === "completado") throw new Error("Este Flash Test ya fue completado.");
      if (!["pendiente", "en_progreso"].includes(data.estado))
        throw new Error("Este Flash Test no está activo.");
      window.location.assign("/flash/" + encodeURIComponent(token));
    } catch (e: any) {
      setError(e.message);
      setBusy(false);
    }
  };

  return (
    <div className={shellClasses}>
      <Navbar />
      <main className={studentMainClasses}>
        <section className={studentPanelClasses}>
          <span className="inline-flex size-[58px] items-center justify-center rounded-[15px] border border-[#148bd030] bg-[#148bd015] text-[#84c9f4]">
            <Mail size={27} />
          </span>
          <span className="my-4 flex items-center justify-center gap-2 text-xs font-semibold text-[#84c9f4]">
            Portal del alumno
          </span>
          <h1 className={studentHeadingClasses}>
            Tu evaluación comienza
            <br />
            en tu correo
          </h1>
          <p>
            Abre el enlace personal que te envió tu profesor. No necesitas crear una cuenta ni iniciar
            sesión.
          </p>
          <div className="my-[22px] flex gap-3 rounded-[9px] border border-[#148bd030] bg-[#148bd010] p-[17px] text-left text-[13px] leading-[1.7] text-fg">
            <LockKeyhole size={18} className="mt-[3px] shrink-0" />
            <p className="m-0">
              Solo podrás responder tu Flash Test activo. El enlace es personal, tiene vigencia limitada y
              guarda tu avance.
            </p>
          </div>
          <form onSubmit={open} className="my-5 flex flex-col items-stretch gap-2.5 text-left">
            <FormField label="¿Ya tienes tu enlace o código?" className="min-w-0 flex-1">
              <FormInput
                name="link"
                placeholder="Pega aquí el enlace o token de tu correo"
                autoComplete="off"
                required
              />
            </FormField>
            <Button type="submit" size="classic" disabled={busy}>
              {busy ? "Verificando…" : "Abrir mi Flash Test"}
              <ArrowRight size={16} />
            </Button>
          </form>
          {error && (
            <Banner tone="error" role="alert">
              {error}
            </Banner>
          )}
          <MutedText>Si no has recibido el correo o tu enlace expiró, contacta a tu profesor.</MutedText>
        </section>
      </main>
    </div>
  );
}

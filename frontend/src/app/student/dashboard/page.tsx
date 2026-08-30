"use client";

import Link from "next/link";
import { Mail, CheckCircle2, ShieldCheck, ArrowLeft } from "lucide-react";
import Navbar from "@/components/Navbar";

export default function StudentDashboard() {
  return (
    <div className="flex min-h-screen flex-col bg-[#07070a] text-zinc-100 pb-20">
      <Navbar />

      <main className="max-w-2xl w-full mx-auto px-6 mt-16 flex flex-col items-center text-center">
        <div className="glass-panel p-8 rounded-3xl border border-zinc-800 bg-zinc-950/60 shadow-2xl space-y-6">
          <div className="mx-auto w-16 h-16 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Mail className="h-8 w-8" />
          </div>

          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-white">Acceso Estudiantil Vía Correo</h1>
            <p className="text-sm text-zinc-400 leading-relaxed">
              En IntegriEval, <strong>los estudiantes no necesitan crearse una cuenta ni iniciar sesión</strong>.
            </p>
          </div>

          <div className="bg-zinc-900/60 rounded-2xl p-5 text-left text-xs space-y-3 text-zinc-300 border border-zinc-800/80">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
              <span>
                Tu profesor descarga tus trabajos de la plataforma universitaria y los sube a IntegriEval.
              </span>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
              <span>
                Una vez analizado tu informe, recibirás un <strong>enlace directo y seguro por correo</strong> para responder tus preguntas flash cronometradas.
              </span>
            </div>
            <div className="flex items-start gap-3">
              <ShieldCheck className="h-4 w-4 text-indigo-400 shrink-0 mt-0.5" />
              <span>
                Si eres convocado a una reunión de justificación o verificación con tu profesor, también recibirás la fecha y hora en tu correo institucional.
              </span>
            </div>
          </div>

          <div className="pt-2">
            <Link
              href="/login"
              className="inline-flex items-center gap-2 text-xs font-semibold text-zinc-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="h-4 w-4" /> Volver al Inicio / Acceso Docente
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}

"use client";

import Link from "next/link";
import { Mail, ArrowLeft } from "lucide-react";
import Navbar from "@/components/Navbar";

export default function EvaluationDetails() {
  return (
    <div className="flex min-h-screen flex-col bg-[#07070a] text-zinc-100 pb-20">
      <Navbar />

      <main className="max-w-2xl w-full mx-auto px-6 mt-16 flex flex-col items-center text-center">
        <div className="glass-panel p-8 rounded-3xl border border-zinc-800 bg-zinc-950/60 shadow-2xl space-y-6">
          <div className="mx-auto w-16 h-16 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Mail className="h-8 w-8" />
          </div>

          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-white">Evaluación Gestionada por el Profesor</h1>
            <p className="text-sm text-zinc-400 leading-relaxed">
              Los trabajos son subidos y procesados directamente por tu profesor.
              Recibirás el enlace directo a tu <strong>Flash Test</strong> en tu correo institucional una vez que tu trabajo sea revisado.
            </p>
          </div>

          <div className="pt-4">
            <Link
              href="/student/dashboard"
              className="inline-flex items-center gap-2 text-xs font-semibold text-zinc-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="h-4 w-4" /> Volver al portal
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}

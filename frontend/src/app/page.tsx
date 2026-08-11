"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Shield, BookOpen, Clock, Brain, UserCheck, ChevronRight } from "lucide-react";
import { getToken, getRole } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    const role = getRole();
    if (token && role) {
      if (role === "student") router.push("/student/dashboard");
      else if (role === "teacher") router.push("/teacher/dashboard");
      else if (role === "admin") router.push("/admin/dashboard");
    } else {
      setLoading(false);
    }
  }, [router]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#07070a]">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen overflow-hidden flex flex-col justify-between">
      {/* Background glow effects */}
      <div className="glow-bg top-[-10%] left-[-10%]" />
      <div className="glow-bg bottom-[-10%] right-[-10%] bg-radial-gradient" style={{ backgroundImage: 'radial-gradient(circle, rgba(217, 70, 239, 0.1) 0%, transparent 70%)' }} />

      {/* Header / Navbar */}
      <header className="glass-panel sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="h-6 w-6 text-indigo-400" />
          <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            IntegriEval
          </span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/login" className="text-sm font-medium text-zinc-300 hover:text-white transition-colors">
            Iniciar Sesión
          </Link>
          <Link 
            href="/register" 
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 hover:bg-indigo-500 hover:shadow-indigo-500/30 transition-all duration-200"
          >
            Registrarse
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto px-6 py-16 flex flex-col items-center justify-center text-center gap-16">
        <div className="flex flex-col items-center gap-6 max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-4 py-1.5 text-xs font-semibold text-indigo-300 backdrop-blur-md">
            <Brain className="h-4 w-4" />
            <span>Validación de Aprendizaje con Inteligencia Artificial</span>
          </div>
          
          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-none">
            Verifica la{" "}
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              Comprensión Real
            </span>{" "}
            detrás de cada Informe
          </h1>
          
          <p className="text-lg text-zinc-400 max-w-2xl leading-relaxed">
            IntegriEval ayuda a profesores a validar que los informes de los estudiantes no hayan sido generados por IA sin comprensión, mediante cuestionarios dinámicos cronometrados controlados por el servidor.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 mt-4 w-full justify-center">
            <Link 
              href="/register" 
              className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 px-8 py-4 text-base font-bold text-white shadow-xl shadow-indigo-600/30 hover:opacity-95 hover:shadow-indigo-600/40 transition-all duration-200"
            >
              Comenzar Ahora
              <ChevronRight className="h-5 w-5" />
            </Link>
            <Link 
              href="/login" 
              className="flex items-center justify-center rounded-xl border border-zinc-700/60 bg-zinc-900/30 px-8 py-4 text-base font-semibold text-zinc-300 hover:bg-zinc-900/60 hover:text-white transition-colors"
            >
              Plataforma de Demo
            </Link>
          </div>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full">
          {/* Card 1 */}
          <div className="glass-panel-interactive p-8 rounded-2xl flex flex-col items-center text-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 text-indigo-400">
              <Clock className="h-6 w-6" />
            </div>
            <h3 className="text-xl font-bold text-zinc-200">Evaluación Flash Cronometrada</h3>
            <p className="text-sm text-zinc-400">
              Preguntas de respuesta inmediata (30 seg por defecto) generadas a partir del informe del alumno. El tiempo estricto impide consultas a IAs externas.
            </p>
          </div>

          {/* Card 2 */}
          <div className="glass-panel-interactive p-8 rounded-2xl flex flex-col items-center text-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20 text-purple-400">
              <UserCheck className="h-6 w-6" />
            </div>
            <h3 className="text-xl font-bold text-zinc-200">Defensa Oral y Verificación</h3>
            <p className="text-sm text-zinc-400">
              Citas automáticas de defensa oral en el calendario del profesor para estudiantes de bajo puntaje. Ajusta notas directamente tras la sesión.
            </p>
          </div>

          {/* Card 3 */}
          <div className="glass-panel-interactive p-8 rounded-2xl flex flex-col items-center text-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-pink-500/10 flex items-center justify-center border border-pink-500/20 text-pink-400">
              <Shield className="h-6 w-6" />
            </div>
            <h3 className="text-xl font-bold text-zinc-200">Detección y Disuasión Aleatoria</h3>
            <p className="text-sm text-zinc-400">
              Notas excepcionales gatillan verificación. Además, el sistema cita al azar a un compañero del curso, introduciendo incertidumbre anti-fraude.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-900 py-8 px-6 text-center text-xs text-zinc-500">
        <p>© 2026 IntegriEval. Proyecto de Título - Ingeniería Civil Informática.</p>
        <p className="mt-1">Universidad Católica de Temuco. Temuco, Chile.</p>
      </footer>
    </div>
  );
}

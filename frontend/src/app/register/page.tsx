"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Shield, User, Mail, Lock, UserPlus, AlertCircle, CheckCircle } from "lucide-react";
import { api } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("student");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      await api.register({
        name,
        email,
        password,
        role,
        institution_id: null, // Optional in backend
      });
      setSuccess("¡Registro exitoso! Redirigiendo al login...");
      setTimeout(() => {
        router.push("/login");
      }, 1500);
    } catch (err: any) {
      setError(err.message || "Error al registrarse. Intente nuevamente.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-[#07070a] px-6 py-12">
      <div className="glow-bg bottom-[20%] right-[30%] bg-radial-gradient" style={{ backgroundImage: 'radial-gradient(circle, rgba(217, 70, 239, 0.08) 0%, transparent 70%)' }} />
      
      <div className="w-full max-w-md space-y-8">
        {/* Brand logo */}
        <div className="flex flex-col items-center text-center gap-2">
          <div className="h-12 w-12 rounded-2xl bg-indigo-600/10 flex items-center justify-center border border-indigo-500/20 text-indigo-400">
            <Shield className="h-6 w-6" />
          </div>
          <h2 className="mt-4 text-3xl font-extrabold tracking-tight text-white">
            Crear una Cuenta
          </h2>
          <p className="mt-1 text-sm text-zinc-400">
            Regístrate para comenzar a usar la plataforma IntegriEval
          </p>
        </div>

        {/* Card */}
        <div className="glass-panel p-8 rounded-2xl space-y-6">
          {error && (
            <div className="flex items-center gap-2 rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="flex items-center gap-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 p-3 text-sm text-emerald-400">
              <CheckCircle className="h-4 w-4 shrink-0" />
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={handleRegister} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                Nombre Completo
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-zinc-500">
                  <User className="h-5 w-5" />
                </span>
                <input
                  type="text"
                  required
                  placeholder="Juan Pérez"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-950/40 py-3 pl-10 pr-4 text-sm text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                Correo Electrónico
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-zinc-500">
                  <Mail className="h-5 w-5" />
                </span>
                <input
                  type="email"
                  required
                  placeholder="juan.perez@uct.cl"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-950/40 py-3 pl-10 pr-4 text-sm text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                Contraseña
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-zinc-500">
                  <Lock className="h-5 w-5" />
                </span>
                <input
                  type="password"
                  required
                  placeholder="Mínimo 6 caracteres"
                  minLength={6}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-950/40 py-3 pl-10 pr-4 text-sm text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                Rol del Usuario
              </label>
              <div className="grid grid-cols-2 gap-3 pt-1">
                <button
                  type="button"
                  onClick={() => setRole("student")}
                  className={`rounded-xl py-3 text-sm font-semibold border transition-all cursor-pointer ${
                    role === "student"
                      ? "bg-indigo-600/10 border-indigo-500 text-indigo-400"
                      : "border-zinc-800 bg-zinc-950/10 text-zinc-400 hover:bg-zinc-900/40"
                  }`}
                >
                  Estudiante
                </button>
                <button
                  type="button"
                  onClick={() => setRole("teacher")}
                  className={`rounded-xl py-3 text-sm font-semibold border transition-all cursor-pointer ${
                    role === "teacher"
                      ? "bg-indigo-600/10 border-indigo-500 text-indigo-400"
                      : "border-zinc-800 bg-zinc-950/10 text-zinc-400 hover:bg-zinc-900/40"
                  }`}
                >
                  Docente
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 hover:bg-indigo-500 disabled:opacity-50 transition-all cursor-pointer"
            >
              {loading ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
              ) : (
                <>
                  <UserPlus className="h-5 w-5" />
                  <span>Registrar Cuenta</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Link to Login */}
        <p className="text-center text-sm text-zinc-500">
          ¿Ya tienes una cuenta?{" "}
          <Link href="/login" className="font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
            Inicia sesión aquí
          </Link>
        </p>
      </div>
    </div>
  );
}

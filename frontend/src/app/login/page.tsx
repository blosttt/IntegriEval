"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Shield, Mail, Lock, LogIn, Globe, AlertCircle } from "lucide-react";
import { api, getToken, getRole, getApiBase } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const token = getToken();
    const role = getRole();
    if (token && role) {
      redirectUser(role);
    }
  }, []);

  const redirectUser = (role: string) => {
    if (role === "student") router.push("/student/dashboard");
    else if (role === "teacher") router.push("/teacher/dashboard");
    else if (role === "admin") router.push("/admin/dashboard");
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await api.login(email, password);
      redirectUser(data.role);
    } catch (err: any) {
      setError(err.message || "Credenciales inválidas");
    } finally {
      setLoading(false);
    }
  };

  const handleMockSSO = async (roleType: "student" | "teacher") => {
    setError("");
    setLoading(true);
    const mockEmail = roleType === "student" ? "estudiante.demo@uct.cl" : "docente.demo@uct.cl";
    const mockName = roleType === "student" ? "Sebastián Estudiante (Demo)" : "Dra. Elisa Docente (Demo)";

    try {
      const data2 = await requestMockSSO(mockEmail, mockName, roleType);
      redirectUser(data2.role);
    } catch (err: any) {
      setError(err.message || "Error en SSO");
    } finally {
      setLoading(false);
    }
  };

  // Helper request since we want to pass role to the mock endpoint
  const requestMockSSO = async (email: string, name: string, role: string) => {
    const response = await fetch(`${getApiBase()}/auth/sso/google-mock`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, name, role }), // our backend can be modified to read role!
    });
    if (!response.ok) throw new Error("Error en SSO");
    const data = await response.json();
    if (data.access_token) {
      localStorage.setItem("integrieval_token", data.access_token);
      localStorage.setItem("integrieval_role", data.role);
      localStorage.setItem("integrieval_name", data.name);
    }
    return data;
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-[#07070a] px-6 py-12">
      <div className="glow-bg top-[20%] left-[30%]" />
      
      <div className="w-full max-w-md space-y-8">
        {/* Brand logo */}
        <div className="flex flex-col items-center text-center gap-2">
          <div className="h-12 w-12 rounded-2xl bg-indigo-600/10 flex items-center justify-center border border-indigo-500/20 text-indigo-400">
            <Shield className="h-6 w-6" />
          </div>
          <h2 className="mt-4 text-3xl font-extrabold tracking-tight text-white">
            Ingreso al Sistema
          </h2>
          <p className="mt-1 text-sm text-zinc-400">
            Ingresa tus credenciales para acceder a IntegriEval
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

          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                Correo Institucional
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-zinc-500">
                  <Mail className="h-5 w-5" />
                </span>
                <input
                  type="email"
                  required
                  placeholder="ejemplo@uct.cl"
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
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-950/40 py-3 pl-10 pr-4 text-sm text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors"
                />
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
                  <LogIn className="h-5 w-5" />
                  <span>Ingresar</span>
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative flex py-2 items-center">
            <div className="flex-grow border-t border-zinc-800/80"></div>
            <span className="flex-shrink mx-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">O continuar con</span>
            <div className="flex-grow border-t border-zinc-800/80"></div>
          </div>

          {/* SSO Google Mock Buttons */}
          <div className="grid grid-cols-1 gap-3">
            <button
              type="button"
              disabled={loading}
              onClick={() => handleMockSSO("student")}
              className="flex items-center justify-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/30 py-3 px-4 text-sm font-medium text-zinc-300 hover:bg-zinc-900/60 hover:text-white transition-colors cursor-pointer"
            >
              <Globe className="h-4 w-4 text-red-400" />
              <span>Google SSO (Estudiante Demo)</span>
            </button>

            <button
              type="button"
              disabled={loading}
              onClick={() => handleMockSSO("teacher")}
              className="flex items-center justify-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/30 py-3 px-4 text-sm font-medium text-zinc-300 hover:bg-zinc-900/60 hover:text-white transition-colors cursor-pointer"
            >
              <Globe className="h-4 w-4 text-blue-400" />
              <span>Google SSO (Docente Demo)</span>
            </button>
          </div>
        </div>

        {/* Link to Register */}
        <p className="text-center text-sm text-zinc-500">
          ¿No tienes una cuenta?{" "}
          <Link href="/register" className="font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
            Regístrate aquí
          </Link>
        </p>
      </div>
    </div>
  );
}

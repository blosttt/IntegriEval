"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { 
  ShieldAlert, Database, Users, Cpu, FileText, 
  ArrowLeft, RefreshCw, AlertTriangle, Terminal, ChevronLeft, ChevronRight 
} from "lucide-react";
import Navbar from "@/components/Navbar";
import { api, getToken, getRole } from "@/lib/api";

export default function AdminDashboard() {
  const router = useRouter();
  const [metrics, setMetrics] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  // Pagination
  const [page, setPage] = useState(0);
  const logsPerPage = 25;

  useEffect(() => {
    const token = getToken();
    const role = getRole();
    if (!token || role !== "admin") {
      router.push("/login");
      return;
    }
    loadData();
  }, [router, page]);

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      // 1. Fetch system metrics
      const systemMetrics = await api.getSystemMetrics();
      setMetrics(systemMetrics);

      // 2. Fetch paginated audit logs
      const offset = page * logsPerPage;
      const logList = await api.getAuditLogs(logsPerPage, offset);
      setLogs(logList);
    } catch (err: any) {
      setError("Error al cargar los registros de auditoría y métricas");
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleString("es-CL", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    });
  };

  if (loading && !metrics) {
    return (
      <div className="flex min-h-screen flex-col bg-[#07070a]">
        <Navbar />
        <div className="flex flex-1 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-[#07070a] pb-16">
      <Navbar />

      <main className="max-w-7xl w-full mx-auto px-6 mt-8 space-y-8">
        
        {/* Header */}
        <div className="flex justify-between items-center">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
              <Database className="h-8 w-8 text-indigo-400" />
              Consola de Administración
            </h1>
            <p className="text-zinc-400 text-sm">Monitoreo técnico global, consumo de API de IA y bitácora de auditoría legal.</p>
          </div>

          <button
            onClick={loadData}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-zinc-800 bg-zinc-900/30 text-xs font-semibold text-zinc-300 hover:text-white transition-all cursor-pointer"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Actualizar Consola
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 rounded-xl bg-red-500/10 border border-red-500/20 p-4 text-sm text-red-400">
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* System metrics row */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="glass-panel p-5 rounded-2xl flex items-center gap-4">
              <div className="h-12 w-12 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 text-indigo-400">
                <Users className="h-6 w-6" />
              </div>
              <div className="space-y-0.5">
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Usuarios Activos</span>
                <span className="text-2xl font-black text-white">{metrics.total_users}</span>
                <span className="text-[10px] text-zinc-500 block">
                  {metrics.teachers} Profesores / {metrics.students} Alumnos
                </span>
              </div>
            </div>

            <div className="glass-panel p-5 rounded-2xl flex items-center gap-4">
              <div className="h-12 w-12 rounded-xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20 text-purple-400">
                <Cpu className="h-6 w-6" />
              </div>
              <div className="space-y-0.5">
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Llamadas a la IA (LLM)</span>
                <span className="text-2xl font-black text-white">{metrics.llm_invocations}</span>
                <span className="text-[10px] text-zinc-500 block">Generación de cuestionarios</span>
              </div>
            </div>

            <div className="glass-panel p-5 rounded-2xl flex items-center gap-4">
              <div className="h-12 w-12 rounded-xl bg-red-500/10 flex items-center justify-center border border-red-500/20 text-red-400">
                <ShieldAlert className="h-6 w-6" />
              </div>
              <div className="space-y-0.5">
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Errores de Sistema</span>
                <span className="text-2xl font-black text-white">{metrics.system_errors}</span>
                <span className="text-[10px] text-zinc-500 block">Logs de excepción capturados</span>
              </div>
            </div>

            <div className="glass-panel p-5 rounded-2xl flex items-center gap-4">
              <div className="h-12 w-12 rounded-xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20 text-blue-400">
                <Terminal className="h-6 w-6" />
              </div>
              <div className="space-y-0.5">
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Estado Base Datos</span>
                <span className="text-base font-extrabold text-emerald-400 mt-1 block">Conectado (SQL)</span>
                <span className="text-[10px] text-zinc-500 block">SQLite / PostgreSQL Ready</span>
              </div>
            </div>
          </div>
        )}

        {/* Audit Log Table */}
        <div className="glass-panel rounded-2xl overflow-hidden border">
          <div className="px-6 py-4 border-b border-zinc-850 bg-zinc-950/40">
            <h3 className="text-base font-bold text-zinc-200 flex items-center gap-2">
              <FileText className="h-5 w-5 text-indigo-400" />
              Bitácora de Auditoría Académica (Trace Logs)
            </h3>
          </div>

          <div className="overflow-x-auto w-full">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-zinc-850 bg-zinc-900/30 text-zinc-400 font-bold uppercase tracking-wider">
                  <th className="p-4">Fecha/Hora (UTC)</th>
                  <th className="p-4">Identidad</th>
                  <th className="p-4">Acción</th>
                  <th className="p-4">Módulo Afectado</th>
                  <th className="p-4">ID Entidad</th>
                  <th className="p-4">Detalles JSON</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900 text-zinc-300">
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-zinc-500 italic">No hay registros de auditoría disponibles.</td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id} className="hover:bg-zinc-950/40 transition-colors">
                      <td className="p-4 whitespace-nowrap text-zinc-500 font-mono">{formatDateTime(log.timestamp)}</td>
                      <td className="p-4 whitespace-nowrap font-semibold text-zinc-200">{log.user_email}</td>
                      <td className="p-4 whitespace-nowrap">
                        <span className="inline-block px-2 py-0.5 rounded border border-zinc-800 bg-zinc-900 font-mono text-[10px] text-zinc-400">
                          {log.action}
                        </span>
                      </td>
                      <td className="p-4 whitespace-nowrap font-medium">{log.entity}</td>
                      <td className="p-4 whitespace-nowrap font-mono text-zinc-500">{log.entity_id || "-"}</td>
                      <td className="p-4 max-w-xs truncate font-mono text-[10px] text-indigo-300" title={JSON.stringify(log.details)}>
                        {log.details ? JSON.stringify(log.details) : "-"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Table Pagination footer */}
          <div className="px-6 py-4 border-t border-zinc-850 bg-zinc-950/20 flex justify-between items-center text-xs">
            <span className="text-zinc-500">Página {page + 1}</span>
            <div className="flex gap-2">
              <button
                disabled={page === 0}
                onClick={() => setPage(p => Math.max(0, p - 1))}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-950/45 text-zinc-400 hover:text-white disabled:opacity-30 cursor-pointer"
              >
                <ChevronLeft className="h-4 w-4" />
                Anterior
              </button>
              <button
                disabled={logs.length < logsPerPage}
                onClick={() => setPage(p => p + 1)}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-950/45 text-zinc-400 hover:text-white disabled:opacity-30 cursor-pointer"
              >
                Siguiente
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

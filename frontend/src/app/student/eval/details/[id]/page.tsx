"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  ArrowLeft, FileText, FileUp, AlertTriangle, 
  CheckCircle, Play, RefreshCw, Clock, Sparkles
} from "lucide-react";
import Navbar from "@/components/Navbar";
import { api, getToken, getRole } from "@/lib/api";

export default function EvaluationDetails() {
  const params = useParams();
  const router = useRouter();
  const evalId = Number(params.id);

  const [evaluation, setEvaluation] = useState<any>(null);
  const [statusDetails, setStatusDetails] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    const token = getToken();
    const role = getRole();
    if (!token || role !== "student") {
      router.push("/login");
      return;
    }
    loadDetails();
  }, [evalId, router]);

  // Auto-refresh when AI is processing
  useEffect(() => {
    let interval: any;
    if (statusDetails && statusDetails.report_uploaded && !statusDetails.bank_ready) {
      interval = setInterval(() => {
        refreshStatusOnly();
      }, 4000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [statusDetails]);

  const loadDetails = async () => {
    setLoading(true);
    setError("");
    try {
      const ev = await api.getEvaluation(evalId);
      setEvaluation(ev);
      const st = await api.getEvaluationStudentStatus(evalId);
      setStatusDetails(st);
    } catch (err: any) {
      setError(err.message || "Error al cargar detalles de la evaluación");
    } finally {
      setLoading(false);
    }
  };

  const refreshStatusOnly = async () => {
    try {
      const st = await api.getEvaluationStudentStatus(evalId);
      setStatusDetails(st);
    } catch (err) {}
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      const ext = selectedFile.name.split(".").pop()?.toLowerCase();
      
      if (ext !== "pdf" && ext !== "docx" && ext !== "doc") {
        setError("Solo se admiten archivos PDF o Word (.docx)");
        setFile(null);
        return;
      }
      
      if (selectedFile.size > 10 * 1024 * 1024) {
        setError("El archivo supera el límite de 10MB");
        setFile(null);
        return;
      }

      setError("");
      setFile(selectedFile);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError("");
    setSuccess("");

    try {
      await api.uploadReport(evalId, file);
      setSuccess("¡Informe subido correctamente! Generando cuestionario con IA...");
      setFile(null);
      // Wait a moment and reload
      setTimeout(() => {
        loadDetails();
      }, 1000);
    } catch (err: any) {
      setError(err.message || "Error al subir el informe");
    } finally {
      setUploading(false);
    }
  };

  const handleStartExam = async () => {
    setError("");
    try {
      const session = await api.startSession(evalId);
      router.push(`/student/eval/session/${session.id}`);
    } catch (err: any) {
      setError(err.message || "Error al iniciar la prueba");
    }
  };

  const formatDateTime = (dateStr: string) => {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return d.toLocaleString("es-CL", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  if (loading) {
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

      <main className="max-w-3xl w-full mx-auto px-6 mt-8 space-y-6">
        {/* Back Link */}
        <button 
          onClick={() => router.push("/student/dashboard")}
          className="flex items-center gap-2 text-sm font-semibold text-zinc-400 hover:text-white transition-colors cursor-pointer"
        >
          <ArrowLeft className="h-4 w-4" />
          Volver al panel
        </button>

        {evaluation && (
          <div className="space-y-6">
            {/* Header info */}
            <div className="glass-panel p-6 rounded-2xl space-y-4">
              <div>
                <h1 className="text-2xl font-bold text-white">{evaluation.title}</h1>
                <p className="text-sm text-zinc-400 mt-1">Asignatura y Rúbrica de la Evaluación</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm bg-zinc-950/40 p-4 rounded-xl border border-zinc-900">
                <div className="space-y-1">
                  <span className="text-xs text-zinc-500 font-semibold uppercase tracking-wider block">Entrega del informe</span>
                  <span className="text-zinc-200 font-medium">{formatDateTime(evaluation.due_date)}</span>
                </div>
                <div className="space-y-1">
                  <span className="text-xs text-zinc-500 font-semibold uppercase tracking-wider block">Ventana de Rendición</span>
                  <span className="text-zinc-200 font-medium">
                    {formatDateTime(evaluation.start_window)} al {formatDateTime(evaluation.end_window)}
                  </span>
                </div>
                <div className="space-y-1">
                  <span className="text-xs text-zinc-500 font-semibold uppercase tracking-wider block">Preguntas de la prueba</span>
                  <span className="text-zinc-200 font-medium">{evaluation.num_questions} preguntas flash</span>
                </div>
                <div className="space-y-1">
                  <span className="text-xs text-zinc-500 font-semibold uppercase tracking-wider block">Tiempo límite</span>
                  <span className="text-zinc-200 font-medium">{evaluation.time_per_question} segundos por pregunta</span>
                </div>
              </div>
            </div>

            {/* Error & Success States */}
            {error && (
              <div className="flex items-center gap-2 rounded-xl bg-red-500/10 border border-red-500/20 p-4 text-sm text-red-400">
                <AlertTriangle className="h-5 w-5 shrink-0" />
                <span>{error}</span>
              </div>
            )}
            {success && (
              <div className="flex items-center gap-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-4 text-sm text-emerald-400">
                <CheckCircle className="h-5 w-5 shrink-0" />
                <span>{success}</span>
              </div>
            )}

            {/* Flow State Cards */}
            {statusDetails && (
              <div className="space-y-6">
                
                {/* 1. REPORT UPLOAD SECTION */}
                {!statusDetails.report_uploaded && (
                  <div className="glass-panel p-6 rounded-2xl space-y-4">
                    <h2 className="text-lg font-bold text-zinc-200 flex items-center gap-2">
                      <FileUp className="h-5 w-5 text-indigo-400" />
                      Paso 1: Sube tu Informe Escrito
                    </h2>
                    <p className="text-zinc-400 text-sm leading-relaxed">
                      Sube tu reporte en formato PDF o Word (.docx). El sistema extraerá el texto automáticamente para que el LLM genere tus preguntas cronometradas de validación. Límite de tamaño: 10MB.
                    </p>

                    <form onSubmit={handleUpload} className="space-y-4 pt-2">
                      <div className="flex items-center justify-center w-full">
                        <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-zinc-800 rounded-xl cursor-pointer bg-zinc-950/20 hover:bg-zinc-900/10 hover:border-indigo-500/40 transition-colors">
                          <div className="flex flex-col items-center justify-center pt-5 pb-6 text-zinc-500">
                            <FileText className="w-8 h-8 mb-2" />
                            <p className="text-sm font-semibold">
                              {file ? file.name : "Selecciona un archivo PDF o Word"}
                            </p>
                            <p className="text-xs mt-1">Límite 10MB</p>
                          </div>
                          <input 
                            type="file" 
                            accept=".pdf,.docx,.doc" 
                            className="hidden" 
                            onChange={handleFileChange} 
                          />
                        </label>
                      </div>

                      <button
                        type="submit"
                        disabled={!file || uploading}
                        className="flex items-center justify-center gap-2 w-full rounded-xl bg-indigo-600 py-3 text-sm font-semibold text-white shadow-lg hover:bg-indigo-500 disabled:opacity-50 transition-all cursor-pointer"
                      >
                        {uploading ? (
                          <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                        ) : (
                          <>
                            <FileUp className="h-5 w-5" />
                            <span>Subir y Procesar Informe</span>
                          </>
                        )}
                      </button>
                    </form>
                  </div>
                )}

                {/* 2. REPORT UPLOADED & WAITING FOR AI */}
                {statusDetails.report_uploaded && !statusDetails.bank_ready && (
                  <div className="glass-panel p-6 rounded-2xl flex flex-col items-center text-center gap-4">
                    <div className="relative">
                      <Sparkles className="h-10 w-10 text-indigo-400 animate-pulse" />
                      <div className="absolute inset-0 h-10 w-10 bg-indigo-500/20 rounded-full blur animate-ping"></div>
                    </div>
                    <div className="space-y-1">
                      <h2 className="text-lg font-bold text-zinc-200">Generando tu cuestionario personalizado</h2>
                      <p className="text-sm text-zinc-500 max-w-md">
                        Nuestra IA (Claude) está leyendo tu informe y estructurando preguntas personalizadas sobre tu trabajo. Esto tarda unos segundos.
                      </p>
                    </div>

                    <div className="w-full max-w-xs bg-zinc-900 h-1.5 rounded-full overflow-hidden border border-zinc-800">
                      <div className="bg-indigo-500 h-full w-2/3 rounded-full animate-pulse"></div>
                    </div>

                    <button 
                      onClick={loadDetails}
                      className="flex items-center gap-1.5 text-xs font-semibold text-zinc-400 hover:text-white px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-950/40 hover:bg-zinc-900 transition-all cursor-pointer"
                    >
                      <RefreshCw className="h-3 w-3" />
                      Refrescar
                    </button>
                  </div>
                )}

                {/* 3. QUESTION BANK IS APPROVED & READY FOR EXAM */}
                {statusDetails.report_uploaded && statusDetails.bank_ready && (
                  <div className="glass-panel p-6 rounded-2xl space-y-6">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="h-6 w-6 text-emerald-400 shrink-0" />
                      <div>
                        <h2 className="text-lg font-bold text-zinc-200">Paso 2: Rinde la Evaluación Flash</h2>
                        <p className="text-xs text-zinc-500">Cuestionario personalizado listo y aprobado por el profesor.</p>
                      </div>
                    </div>

                    {statusDetails.window_open ? (
                      <div className="space-y-5">
                        <div className="flex gap-3 bg-indigo-500/5 border border-indigo-500/20 p-4 rounded-xl text-indigo-400 text-sm">
                          <AlertTriangle className="h-5 w-5 shrink-0" />
                          <div className="space-y-1">
                            <span className="font-bold">Advertencia Crítica de Seguridad:</span>
                            <ul className="list-disc list-inside space-y-0.5 text-xs text-indigo-300/90 leading-relaxed">
                              <li>El tiempo está controlado estrictamente por el <b>servidor</b> (30 segundos por pregunta).</li>
                              <li>No se puede pausar la prueba ni refrescar la página sin perder la pregunta activa.</li>
                              <li>Cualquier cambio de pestaña o pérdida de foco quedará registrado en la bitácora de auditoría.</li>
                            </ul>
                          </div>
                        </div>

                        <button
                          onClick={handleStartExam}
                          className="flex items-center justify-center gap-2 w-full rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 py-4 text-base font-bold text-white shadow-xl shadow-indigo-600/20 hover:opacity-95 transition-all cursor-pointer animate-pulse"
                        >
                          <Play className="h-5 w-5" />
                          Iniciar Cuestionario Flash
                        </button>
                      </div>
                    ) : statusDetails.window_close_passed ? (
                      <div className="flex gap-2 rounded-xl bg-zinc-900 border border-zinc-800 p-4 text-sm text-zinc-400">
                        <Clock className="h-5 w-5 shrink-0" />
                        <span>La ventana de esta evaluación ya cerró el {formatDateTime(evaluation.end_window)}.</span>
                      </div>
                    ) : (
                      <div className="flex gap-2 rounded-xl bg-zinc-900 border border-zinc-800 p-4 text-sm text-zinc-400">
                        <Clock className="h-5 w-5 shrink-0" />
                        <span>La ventana de evaluación abrirá el {formatDateTime(evaluation.start_window)}.</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

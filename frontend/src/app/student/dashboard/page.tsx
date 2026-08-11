"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { 
  BookOpen, Clock, FileText, Calendar, 
  ChevronRight, Play, CheckCircle2, AlertCircle, FileUp 
} from "lucide-react";
import Navbar from "@/components/Navbar";
import { api, getToken, getRole } from "@/lib/api";

interface Course {
  id: number;
  name: string;
  period: string;
  teacher_name: string;
}

interface Evaluation {
  id: number;
  title: string;
  due_date: string;
  start_window: string;
  end_window: string;
  statusDetails?: any; // populated client-side
}

interface Appointment {
  id: number;
  type: string;
  scheduled_time: string;
  status: string;
  notes: string;
  teacher_name: string;
  evaluation_title: string;
}

export default function StudentDashboard() {
  const router = useRouter();
  const [courses, setCourses] = useState<Course[]>([]);
  const [evaluations, setEvaluations] = useState<Record<number, Evaluation[]>>({});
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getToken();
    const role = getRole();
    if (!token || role !== "student") {
      router.push("/login");
      return;
    }

    loadDashboardData();
  }, [router]);

  const loadDashboardData = async () => {
    setLoading(true);
    setError("");
    try {
      // 1. Fetch courses
      const courseList = await api.getCourses();
      setCourses(courseList);

      // 2. Fetch appointments
      const apptList = await api.getAppointments();
      setAppointments(apptList.filter((a: any) => a.status === "pending"));

      // 3. For each course, fetch evaluations and their status
      const evalsMap: Record<number, Evaluation[]> = {};
      for (const course of courseList) {
        const evals = await api.getCourseEvaluations(course.id);
        
        // Fetch student status for each evaluation to know current stage
        const enrichedEvals = await Promise.all(
          evals.map(async (ev: any) => {
            try {
              const statusDetails = await api.getEvaluationStudentStatus(ev.id);
              return { ...ev, statusDetails };
            } catch (err) {
              return ev;
            }
          })
        );
        evalsMap[course.id] = enrichedEvals;
      }
      setEvaluations(evalsMap);
    } catch (err: any) {
      setError("Error al cargar los datos del panel académico");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (details: any) => {
    if (!details) return null;

    if (details.session_status === "completed") {
      return (
        <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
          <CheckCircle2 className="h-3.5 w-3.5" />
          Rendida
        </span>
      );
    }

    if (details.report_uploaded) {
      if (details.bank_ready) {
        if (details.window_open) {
          return (
            <span className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded-full border border-indigo-500/20 animate-pulse">
              <Play className="h-3.5 w-3.5" />
              Prueba Disponible
            </span>
          );
        } else if (details.window_close_passed) {
          return (
            <span className="inline-flex items-center gap-1 text-xs font-semibold text-zinc-500 bg-zinc-950 px-2.5 py-1 rounded-full border border-zinc-800">
              Ventana de Evaluación Cerrada
            </span>
          );
        } else {
          return (
            <span className="inline-flex items-center gap-1 text-xs font-semibold text-purple-400 bg-purple-500/10 px-2.5 py-1 rounded-full border border-purple-500/20">
              <Clock className="h-3.5 w-3.5" />
              Informe Aprobado: Esperando Ventana
            </span>
          );
        }
      } else {
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-yellow-400 bg-yellow-500/10 px-2.5 py-1 rounded-full border border-yellow-500/20">
            <Clock className="h-3.5 w-3.5" />
            IA Procesando Cuestionario
          </span>
        );
      }
    }

    if (details.due_date_passed) {
      return (
        <span className="inline-flex items-center gap-1 text-xs font-semibold text-red-400 bg-red-500/10 px-2.5 py-1 rounded-full border border-red-500/20">
          <AlertCircle className="h-3.5 w-3.5" />
          Atrasado (No entregado)
        </span>
      );
    }

    return (
      <span className="inline-flex items-center gap-1 text-xs font-semibold text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded-full border border-blue-500/20">
        <FileUp className="h-3.5 w-3.5" />
        Entregar Informe
      </span>
    );
  };

  const formatDateTime = (dateStr: string) => {
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

      <main className="max-w-7xl w-full mx-auto px-6 mt-10 grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Left Side: Course and Evaluations List */}
        <div className="lg:col-span-3 space-y-8">
          <div className="flex flex-col gap-2">
            <h1 className="text-3xl font-bold tracking-tight text-white">Mi Panel Académico</h1>
            <p className="text-zinc-400 text-sm">Monitorea tus asignaturas, entrega tus informes y rinde las evaluaciones flash correspondientes.</p>
          </div>

          {error && (
            <div className="flex items-center gap-2 rounded-xl bg-red-500/10 border border-red-500/20 p-4 text-sm text-red-400">
              <AlertCircle className="h-5 w-5" />
              <span>{error}</span>
            </div>
          )}

          {courses.length === 0 ? (
            <div className="glass-panel p-12 rounded-2xl text-center space-y-4">
              <BookOpen className="h-12 w-12 text-zinc-600 mx-auto" />
              <h3 className="text-xl font-bold text-zinc-300">No estás inscrito en ningún curso</h3>
              <p className="text-zinc-500 text-sm max-w-md mx-auto">
                Para ingresar a un curso, solicita a tu docente que te inscriba utilizando tu correo institucional.
              </p>
            </div>
          ) : (
            courses.map((course) => (
              <div key={course.id} className="glass-panel p-6 rounded-2xl space-y-5">
                {/* Course Header */}
                <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 pb-4 border-b border-zinc-800/80">
                  <div>
                    <h2 className="text-xl font-bold text-zinc-100">{course.name}</h2>
                    <p className="text-xs text-zinc-500">Periodo: {course.period} | Docente: {course.teacher_name}</p>
                  </div>
                </div>

                {/* Evaluations list for this course */}
                <div className="space-y-3">
                  <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Evaluaciones</h3>
                  
                  {!evaluations[course.id] || evaluations[course.id].length === 0 ? (
                    <p className="text-sm text-zinc-600 italic">No hay evaluaciones programadas para esta asignatura.</p>
                  ) : (
                    evaluations[course.id].map((evaluation) => {
                      const details = evaluation.statusDetails;
                      const canRenderEvalDetails = details !== undefined;

                      return (
                        <div 
                          key={evaluation.id} 
                          className="glass-panel-interactive p-4 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
                        >
                          <div className="space-y-1">
                            <div className="flex items-center gap-3 flex-wrap">
                              <span className="font-semibold text-zinc-200">{evaluation.title}</span>
                              {canRenderEvalDetails && getStatusBadge(details)}
                            </div>
                            
                            <div className="flex items-center gap-4 text-xs text-zinc-500 flex-wrap">
                              <span className="flex items-center gap-1">
                                <FileText className="h-3.5 w-3.5" />
                                Límite entrega: {formatDateTime(evaluation.due_date)}
                              </span>
                              <span className="flex items-center gap-1">
                                <Clock className="h-3.5 w-3.5" />
                                Ventana: {formatDateTime(evaluation.start_window)} - {formatDateTime(evaluation.end_window)}
                              </span>
                            </div>
                          </div>

                          <div className="w-full sm:w-auto">
                            {details?.session_status === "completed" ? (
                              <div className="text-left sm:text-right">
                                <span className="text-xs text-zinc-500 block">Puntaje obtenido</span>
                                <span className="text-sm font-bold text-zinc-200">{details.result?.score} correctas</span>
                                <span className={`text-[10px] font-bold block ${
                                  details.result?.classification === "low" 
                                    ? "text-red-400" 
                                    : details.result?.classification === "high" 
                                      ? "text-purple-400" 
                                      : "text-zinc-400"
                                }`}>
                                  {details.result?.classification === "low" 
                                    ? "Defensa Oral Gatillada" 
                                    : details.result?.classification === "high" 
                                      ? "Excelente (Verificación Gatillada)" 
                                      : "Aprobado"}
                                </span>
                              </div>
                            ) : (
                              <Link
                                href={`/student/eval/details/${evaluation.id}`}
                                className="flex items-center justify-center gap-1.5 w-full sm:w-auto rounded-lg bg-zinc-800/80 px-4 py-2 text-xs font-semibold text-zinc-300 border border-zinc-700/60 hover:bg-indigo-600 hover:text-white hover:border-indigo-500 transition-all duration-200"
                              >
                                Ver Detalles
                                <ChevronRight className="h-4 w-4" />
                              </Link>
                            )}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Right Side: Citations & Appointments Alerts */}
        <div className="space-y-6">
          <div className="glass-panel p-5 rounded-2xl space-y-4">
            <h2 className="text-lg font-bold text-zinc-100 flex items-center gap-2">
              <Calendar className="h-5 w-5 text-indigo-400" />
              Citas y Auditorías
            </h2>
            <p className="text-zinc-400 text-xs leading-relaxed">
              Las calificaciones bajas o de excelencia activan flujos de validación oral. Aquí verás tus defensas y citaciones.
            </p>

            <div className="space-y-3 pt-2">
              {appointments.length === 0 ? (
                <div className="rounded-xl border border-zinc-800 bg-zinc-950/20 p-4 text-center">
                  <p className="text-xs text-zinc-500">No tienes defensas orales ni verificaciones pendientes.</p>
                </div>
              ) : (
                appointments.map((appt) => (
                  <div 
                    key={appt.id} 
                    className={`rounded-xl border p-4 space-y-2 relative overflow-hidden ${
                      appt.type === "defense"
                        ? "bg-red-500/5 border-red-500/20"
                        : "bg-purple-500/5 border-purple-500/20"
                    }`}
                  >
                    <div className="flex justify-between items-start gap-1">
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                        appt.type === "defense"
                          ? "bg-red-500/10 text-red-400 border-red-500/20"
                          : "bg-purple-500/10 text-purple-400 border-purple-500/20"
                      }`}>
                        {appt.type === "defense" ? "Defensa Oral" : "Verificación Aleatoria"}
                      </span>
                    </div>

                    <h4 className="text-xs font-bold text-zinc-200 truncate">{appt.evaluation_title}</h4>
                    
                    <div className="text-[11px] text-zinc-400 space-y-0.5">
                      <p><span className="font-semibold text-zinc-300">Docente:</span> {appt.teacher_name}</p>
                      <p><span className="font-semibold text-zinc-300">Horario:</span> {formatDateTime(appt.scheduled_time)}</p>
                    </div>

                    <p className="text-[10px] text-zinc-500 leading-tight italic bg-zinc-950/40 p-2 rounded border border-zinc-900">
                      {appt.notes}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

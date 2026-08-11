"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { 
  BookOpen, Plus, Users, Award, Calendar, FileText, CheckCircle2, 
  Trash2, Edit, AlertCircle, RefreshCw, Send, Check, X, BarChart3, Clock, Sparkles
} from "lucide-react";
import Navbar from "@/components/Navbar";
import { api, getToken, getRole } from "@/lib/api";

export default function TeacherDashboard() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  
  // Navigation / Tabs state
  const [activeTab, setActiveTab] = useState<"courses" | "availability" | "appointments">("courses");
  
  // Courses states
  const [courses, setCourses] = useState<any[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [courseStats, setCourseStats] = useState<any>(null);
  const [courseEvals, setCourseEvals] = useState<any[]>([]);
  
  // Forms states
  const [newCourseName, setNewCourseName] = useState("");
  const [newCoursePeriod, setNewCoursePeriod] = useState("");
  const [enrollEmail, setEnrollEmail] = useState("");
  
  // Evaluation Creation Form
  const [newEvalTitle, setNewEvalTitle] = useState("");
  const [newEvalPrompt, setNewEvalPrompt] = useState("");
  const [newEvalDueDate, setNewEvalDueDate] = useState("");
  const [newEvalStart, setNewEvalStart] = useState("");
  const [newEvalEnd, setNewEvalEnd] = useState("");
  const [newEvalQuestions, setNewEvalQuestions] = useState(5);
  const [newEvalTime, setNewEvalTime] = useState(30);
  const [newEvalPass, setNewEvalPass] = useState(0.6);
  const [newEvalExcellence, setNewEvalExcellence] = useState(0.95);
  const [newEvalApproval, setNewEvalApproval] = useState(true);

  // Availability state
  const [availabilities, setAvailabilities] = useState<any[]>([]);
  const [newAvailDay, setNewAvailDay] = useState(0); // Monday
  const [newAvailStart, setNewAvailStart] = useState("09:00");
  const [newAvailEnd, setNewAvailEnd] = useState("10:00");

  // Appointments state
  const [appointments, setAppointments] = useState<any[]>([]);
  const [selectedAppt, setSelectedAppt] = useState<any>(null);
  const [apptFeedbackStatus, setApptFeedbackStatus] = useState("completed");
  const [apptFeedbackNotes, setApptFeedbackNotes] = useState("");
  const [apptFeedbackScore, setApptFeedbackScore] = useState<number | "">("");

  // Question Bank Reviewer state
  const [reviewBank, setReviewBank] = useState<any>(null);
  const [reviewStudentId, setReviewStudentId] = useState<number | null>(null);
  const [reviewEvalId, setReviewEvalId] = useState<number | null>(null);

  useEffect(() => {
    const token = getToken();
    const role = getRole();
    if (!token || role !== "teacher") {
      router.push("/login");
      return;
    }
    loadCourses();
    loadAvailabilities();
    loadAppointments();
  }, [router]);

  // Dynamic loaders
  const loadCourses = async () => {
    try {
      const data = await api.getCourses();
      setCourses(data);
      if (data.length > 0 && !selectedCourseId) {
        setSelectedCourseId(data[0].id);
      }
    } catch (err: any) {
      setError("Error al cargar asignaturas");
    } finally {
      setLoading(false);
    }
  };

  const loadAvailabilities = async () => {
    try {
      const data = await api.getTeacherAvailabilities();
      setAvailabilities(data);
    } catch (err) {}
  };

  const loadAppointments = async () => {
    try {
      const data = await api.getAppointments();
      setAppointments(data);
    } catch (err) {}
  };

  // Reload details when selecting a course
  useEffect(() => {
    if (selectedCourseId) {
      loadCourseDetails(selectedCourseId);
    }
  }, [selectedCourseId]);

  const loadCourseDetails = async (id: number) => {
    setError("");
    try {
      const stats = await api.getCourseStats(id);
      setCourseStats(stats);
      const evs = await api.getCourseEvaluations(id);
      setCourseEvals(evs);
      
      // Close reviewer if open
      setReviewBank(null);
    } catch (err: any) {
      setError("Error al cargar detalles de la asignatura");
    }
  };

  // --- ACTIONS ---

  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    try {
      await api.createCourse({
        name: newCourseName,
        period: newCoursePeriod,
        institution_id: 1, // Default or mock
      });
      setSuccess("Asignatura creada correctamente.");
      setNewCourseName("");
      setNewCoursePeriod("");
      loadCourses();
    } catch (err: any) {
      setError(err.message || "Error al crear curso");
    }
  };

  const handleEnrollStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId) return;
    setError("");
    setSuccess("");
    try {
      await api.enrollStudent(selectedCourseId, enrollEmail);
      setSuccess("Estudiante inscrito exitosamente.");
      setEnrollEmail("");
      loadCourseDetails(selectedCourseId);
    } catch (err: any) {
      setError(err.message || "Error al inscribir estudiante");
    }
  };

  const handleCreateEvaluation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId) return;
    setError("");
    setSuccess("");
    try {
      await api.createEvaluation(selectedCourseId, {
        title: newEvalTitle,
        prompt_teacher: newEvalPrompt,
        due_date: new Date(newEvalDueDate).toISOString(),
        start_window: new Date(newEvalStart).toISOString(),
        end_window: new Date(newEvalEnd).toISOString(),
        time_per_question: newEvalTime,
        num_questions: newEvalQuestions,
        pass_threshold: newEvalPass,
        excellence_threshold: newEvalExcellence,
        require_approval: newEvalApproval
      });
      setSuccess("Evaluación programada correctamente.");
      setNewEvalTitle("");
      setNewEvalPrompt("");
      setNewEvalDueDate("");
      setNewEvalStart("");
      setNewEvalEnd("");
      loadCourseDetails(selectedCourseId);
    } catch (err: any) {
      setError(err.message || "Error al crear evaluación");
    }
  };

  const handleAddAvailability = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.addTeacherAvailability({
        day_of_week: Number(newAvailDay),
        start_time: newAvailStart,
        end_time: newAvailEnd
      });
      loadAvailabilities();
    } catch (err: any) {
      setError(err.message || "Error al agregar disponibilidad");
    }
  };

  const handleDeleteAvailability = async (id: number) => {
    try {
      await api.deleteTeacherAvailability(id);
      loadAvailabilities();
    } catch (err: any) {
      setError("Error al eliminar disponibilidad");
    }
  };

  // Appointments Feedback
  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAppt) return;
    setError("");
    setSuccess("");
    try {
      await api.submitAppointmentFeedback(selectedAppt.id, {
        status: apptFeedbackStatus,
        notes: apptFeedbackNotes,
        adjusted_score: apptFeedbackScore !== "" ? Number(apptFeedbackScore) : null
      });
      setSuccess("Cita cerrada y notas actualizadas.");
      setSelectedAppt(null);
      setApptFeedbackNotes("");
      setApptFeedbackScore("");
      loadAppointments();
      if (selectedCourseId) loadCourseDetails(selectedCourseId);
    } catch (err: any) {
      setError(err.message || "Error al cerrar la cita");
    }
  };

  // Reviewing banks
  const handleOpenBankReview = async (evalId: number, studentId: number) => {
    setError("");
    try {
      const bank = await api.getStudentQuestionBank(evalId, studentId);
      setReviewBank(bank);
      setReviewStudentId(studentId);
      setReviewEvalId(evalId);
    } catch (err: any) {
      setError(err.message || "No se pudo cargar el banco de preguntas. ¿Ya se generó?");
    }
  };

  const handleEditQuestionText = (index: number, text: string) => {
    if (!reviewBank) return;
    const updated = { ...reviewBank };
    updated.questions[index].text = text;
    setReviewBank(updated);
  };

  const handleEditQuestionOption = (qIdx: number, optIdx: number, val: string) => {
    if (!reviewBank) return;
    const updated = { ...reviewBank };
    if (updated.questions[qIdx].options) {
      updated.questions[qIdx].options[optIdx] = val;
    }
    setReviewBank(updated);
  };

  const handleEditQuestionAnswer = (qIdx: number, val: string) => {
    if (!reviewBank) return;
    const updated = { ...reviewBank };
    updated.questions[qIdx].correct_answer = val;
    setReviewBank(updated);
  };

  const handleApproveBank = async (approved: boolean) => {
    if (!reviewBank) return;
    setError("");
    setSuccess("");
    
    // Map items to payload QuestionEdit
    const questionsPayload = reviewBank.questions.map((q: any) => ({
      id: q.id,
      text: q.text,
      options: q.options,
      correct_answer: q.correct_answer,
      limit_seconds: q.limit_seconds
    }));

    try {
      await api.reviewQuestionBank(reviewBank.id, {
        is_approved: approved,
        questions: questionsPayload
      });
      setSuccess(approved ? "Banco de preguntas APROBADO para el estudiante." : "Cambios guardados. Estado: RECHAZADO.");
      setReviewBank(null);
      if (selectedCourseId) loadCourseDetails(selectedCourseId);
    } catch (err: any) {
      setError(err.message || "Error al procesar la revisión");
    }
  };

  const handleRegenerateBank = async () => {
    if (!reviewEvalId || !reviewStudentId) return;
    setError("");
    setSuccess("");
    try {
      await api.regenerateQuestionBank(reviewEvalId, reviewStudentId);
      setSuccess("Regeneración solicitada. La IA actualizará el banco en unos segundos.");
      setReviewBank(null);
    } catch (err: any) {
      setError(err.message || "Error al regenerar banco");
    }
  };

  const getDayName = (d: number) => {
    const days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
    return days[d] || "";
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

      <main className="max-w-7xl w-full mx-auto px-6 mt-8 flex flex-col gap-6">
        
        {/* Navigation Tabs */}
        <div className="flex border-b border-zinc-800">
          <button
            onClick={() => setActiveTab("courses")}
            className={`px-5 py-3 text-sm font-semibold border-b-2 cursor-pointer transition-colors ${
              activeTab === "courses" 
                ? "border-indigo-500 text-indigo-400" 
                : "border-transparent text-zinc-400 hover:text-white"
            }`}
          >
            Mis Cursos y Evaluaciones
          </button>
          <button
            onClick={() => setActiveTab("availability")}
            className={`px-5 py-3 text-sm font-semibold border-b-2 cursor-pointer transition-colors ${
              activeTab === "availability" 
                ? "border-indigo-500 text-indigo-400" 
                : "border-transparent text-zinc-400 hover:text-white"
            }`}
          >
            Disponibilidad Horaria
          </button>
          <button
            onClick={() => setActiveTab("appointments")}
            className={`px-5 py-3 text-sm font-semibold border-b-2 cursor-pointer transition-colors ${
              activeTab === "appointments" 
                ? "border-indigo-500 text-indigo-400" 
                : "border-transparent text-zinc-400 hover:text-white"
            }`}
          >
            Citas de Defensa ({appointments.filter(a => a.status === 'pending').length})
          </button>
        </div>

        {/* Global Notifications */}
        {error && (
          <div className="flex items-center gap-2 rounded-xl bg-red-500/10 border border-red-500/20 p-4 text-sm text-red-400">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {success && (
          <div className="flex items-center gap-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-4 text-sm text-emerald-400">
            <CheckCircle2 className="h-5 w-5 shrink-0" />
            <span>{success}</span>
          </div>
        )}

        {/* ==================================== */}
        {/* TAB 1: COURSES & EVALUATIONS WORKSPACE */}
        {/* ==================================== */}
        {activeTab === "courses" && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            
            {/* Sidebar: Course selection & creation */}
            <div className="space-y-6">
              <div className="glass-panel p-5 rounded-2xl space-y-4">
                <h3 className="text-sm font-bold text-zinc-300 uppercase tracking-wider">Crear Asignatura</h3>
                <form onSubmit={handleCreateCourse} className="space-y-3">
                  <input
                    type="text"
                    required
                    placeholder="Nombre, ej: Programación I"
                    value={newCourseName}
                    onChange={(e) => setNewCourseName(e.target.value)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-950/60 p-3 text-xs text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
                  />
                  <input
                    type="text"
                    required
                    placeholder="Periodo, ej: 2026-1"
                    value={newCoursePeriod}
                    onChange={(e) => setNewCoursePeriod(e.target.value)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-950/60 p-3 text-xs text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
                  />
                  <button
                    type="submit"
                    className="flex items-center justify-center gap-1.5 w-full rounded-xl bg-indigo-600 py-2.5 text-xs font-semibold text-white hover:bg-indigo-500 transition-all cursor-pointer"
                  >
                    <Plus className="h-4 w-4" />
                    Crear Asignatura
                  </button>
                </form>
              </div>

              <div className="glass-panel p-5 rounded-2xl space-y-3">
                <h3 className="text-sm font-bold text-zinc-300 uppercase tracking-wider">Mis Asignaturas</h3>
                {courses.length === 0 ? (
                  <p className="text-xs text-zinc-500 italic">No has creado asignaturas.</p>
                ) : (
                  <div className="flex flex-col gap-2">
                    {courses.map((c) => (
                      <button
                        key={c.id}
                        onClick={() => setSelectedCourseId(c.id)}
                        className={`w-full text-left p-3 rounded-xl border text-xs font-bold transition-all cursor-pointer ${
                          selectedCourseId === c.id
                            ? "bg-indigo-600/10 border-indigo-500 text-indigo-400"
                            : "border-zinc-800/80 bg-zinc-950/20 text-zinc-400 hover:bg-zinc-900/20"
                        }`}
                      >
                        {c.name}
                        <span className="block text-[10px] text-zinc-500 font-normal mt-0.5">{c.period}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Course Workspace (Center/Right) */}
            <div className="lg:col-span-3 space-y-6">
              {courseStats && selectedCourseId && (
                <>
                  {/* Course metrics */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="glass-panel p-4 rounded-xl space-y-1">
                      <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Estudiantes Inscritos</span>
                      <span className="text-2xl font-black text-white">{courseStats.total_students}</span>
                    </div>
                    <div className="glass-panel p-4 rounded-xl space-y-1">
                      <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Informes Entregados</span>
                      <span className="text-2xl font-black text-white">{courseStats.reports_uploaded}</span>
                    </div>
                    <div className="glass-panel p-4 rounded-xl space-y-1">
                      <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Rendimiento Promedio</span>
                      <span className="text-2xl font-black text-white">
                        {Math.round(courseStats.avg_score_percentage * 100)}%
                      </span>
                    </div>
                    <div className="glass-panel p-4 rounded-xl space-y-1">
                      <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Tasa de Aprobación</span>
                      <span className="text-2xl font-black text-emerald-400">
                        {Math.round(courseStats.pass_rate_percentage * 100)}%
                      </span>
                    </div>
                  </div>

                  {/* Tabbed content inside workspace */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    
                    {/* Enroll Student & List Students */}
                    <div className="glass-panel p-5 rounded-2xl space-y-4">
                      <h3 className="text-sm font-bold text-zinc-300 uppercase tracking-wider flex items-center gap-2">
                        <Users className="h-4.5 w-4.5 text-zinc-400" />
                        Inscribir Alumno
                      </h3>
                      <form onSubmit={handleEnrollStudent} className="flex gap-2">
                        <input
                          type="email"
                          required
                          placeholder="correo@uct.cl"
                          value={enrollEmail}
                          onChange={(e) => setEnrollEmail(e.target.value)}
                          className="flex-1 rounded-xl border border-zinc-800 bg-zinc-950/60 p-2.5 text-xs text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
                        />
                        <button
                          type="submit"
                          className="rounded-xl bg-indigo-600 px-3 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition-colors cursor-pointer"
                        >
                          <Send className="h-4 w-4" />
                        </button>
                      </form>

                      <div className="space-y-2 pt-2 border-t border-zinc-800">
                        <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Estudiantes Inscritos</h4>
                        {courseStats.students.length === 0 ? (
                          <p className="text-xs text-zinc-600 italic">No hay estudiantes en este curso.</p>
                        ) : (
                          <div className="max-h-60 overflow-y-auto space-y-1.5 pr-1">
                            {courseStats.students.map((stud: any) => (
                              <div key={stud.id} className="p-2.5 rounded-lg border border-zinc-900 bg-zinc-950/20 text-xs flex flex-col gap-1">
                                <span className="font-bold text-zinc-300">{stud.name}</span>
                                <span className="text-[10px] text-zinc-500">{stud.email}</span>
                                
                                {/* Status of evaluations */}
                                <div className="mt-1.5 space-y-1 border-t border-zinc-900 pt-1.5">
                                  {stud.evaluations.map((ev: any) => (
                                    <div key={ev.evaluation_id} className="flex justify-between items-center text-[10px]">
                                      <span className="text-zinc-400 truncate max-w-[120px]">{ev.evaluation_title}</span>
                                      <div className="flex gap-1.5 items-center">
                                        <span className="text-zinc-300 font-bold">{ev.score}</span>
                                        {ev.status === "Rendida" && (
                                          <button
                                            onClick={() => handleOpenBankReview(ev.evaluation_id, stud.id)}
                                            className="text-[9px] text-indigo-400 hover:underline"
                                            title="Ver preguntas realizadas"
                                          >
                                            Ver
                                          </button>
                                        )}
                                        {ev.status === "Pendiente Prueba" && (
                                          <button
                                            onClick={() => handleOpenBankReview(ev.evaluation_id, stud.id)}
                                            className="text-[9px] text-yellow-400 font-bold hover:underline"
                                          >
                                            Revisar
                                          </button>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Evaluations list & creation */}
                    <div className="md:col-span-2 glass-panel p-5 rounded-2xl space-y-5">
                      <div className="flex justify-between items-center pb-2 border-b border-zinc-800">
                        <h3 className="text-sm font-bold text-zinc-300 uppercase tracking-wider flex items-center gap-2">
                          <FileText className="h-4.5 w-4.5 text-zinc-400" />
                          Evaluaciones Habilitadas
                        </h3>
                      </div>

                      {/* Evaluations summary */}
                      <div className="space-y-3 max-h-56 overflow-y-auto pr-1">
                        {courseEvals.length === 0 ? (
                          <p className="text-xs text-zinc-500 italic">No hay evaluaciones creadas.</p>
                        ) : (
                          courseEvals.map((ev) => (
                            <div key={ev.id} className="p-3.5 rounded-xl border border-zinc-900 bg-zinc-950/20 space-y-2">
                              <div className="flex justify-between items-start gap-1">
                                <h4 className="text-sm font-bold text-zinc-200">{ev.title}</h4>
                                <span className="text-[10px] font-semibold text-zinc-500 bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded">
                                  {ev.num_questions} preguntas
                                </span>
                              </div>
                              <p className="text-[11px] text-zinc-400">
                                <b>Entrega:</b> {formatDateTime(ev.due_date)} | <b>Ventana:</b> {formatDateTime(ev.start_window)} al {formatDateTime(ev.end_window)}
                              </p>
                              {ev.prompt_teacher && (
                                <p className="text-[10px] text-zinc-500 italic truncate">Tema: {ev.prompt_teacher}</p>
                              )}
                            </div>
                          ))
                        )}
                      </div>

                      {/* Create evaluation form */}
                      <div className="pt-4 border-t border-zinc-800 space-y-3">
                        <h4 className="text-xs font-bold text-zinc-300 uppercase tracking-wider">Programar Nueva Evaluación</h4>
                        <form onSubmit={handleCreateEvaluation} className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                          <div className="sm:col-span-2">
                            <input
                              type="text"
                              required
                              placeholder="Título de la Evaluación, ej: Proyecto Semestral"
                              value={newEvalTitle}
                              onChange={(e) => setNewEvalTitle(e.target.value)}
                              className="w-full rounded-xl border border-zinc-800 bg-zinc-950/60 p-2.5 text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
                            />
                          </div>

                          <div className="sm:col-span-2">
                            <input
                              type="text"
                              placeholder="Prompt Rúbrica / Tema (opcional para guiar a la IA)"
                              value={newEvalPrompt}
                              onChange={(e) => setNewEvalPrompt(e.target.value)}
                              className="w-full rounded-xl border border-zinc-800 bg-zinc-950/60 p-2.5 text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
                            />
                          </div>

                          <div className="space-y-1">
                            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Fecha Límite Informe</label>
                            <input
                              type="datetime-local"
                              required
                              value={newEvalDueDate}
                              onChange={(e) => setNewEvalDueDate(e.target.value)}
                              className="w-full rounded-xl border border-zinc-800 bg-zinc-950/60 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                            />
                          </div>

                          <div className="space-y-1">
                            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Ventana Prueba (Abre)</label>
                            <input
                              type="datetime-local"
                              required
                              value={newEvalStart}
                              onChange={(e) => setNewEvalStart(e.target.value)}
                              className="w-full rounded-xl border border-zinc-800 bg-zinc-950/60 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                            />
                          </div>

                          <div className="space-y-1">
                            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Ventana Prueba (Cierra)</label>
                            <input
                              type="datetime-local"
                              required
                              value={newEvalEnd}
                              onChange={(e) => setNewEvalEnd(e.target.value)}
                              className="w-full rounded-xl border border-zinc-800 bg-zinc-950/60 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                            />
                          </div>

                          <div className="grid grid-cols-2 gap-2">
                            <div className="space-y-1">
                              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Preguntas</label>
                              <input
                                type="number"
                                required
                                value={newEvalQuestions}
                                onChange={(e) => setNewEvalQuestions(Number(e.target.value))}
                                className="w-full rounded-xl border border-zinc-800 bg-zinc-950/60 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                              />
                            </div>
                            <div className="space-y-1">
                              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Tiempo (seg)</label>
                              <input
                                type="number"
                                required
                                value={newEvalTime}
                                onChange={(e) => setNewEvalTime(Number(e.target.value))}
                                className="w-full rounded-xl border border-zinc-800 bg-zinc-950/60 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                              />
                            </div>
                          </div>

                          <div className="sm:col-span-2 pt-2">
                            <button
                              type="submit"
                              className="flex items-center justify-center gap-1.5 w-full rounded-xl bg-indigo-600 py-3 text-xs font-semibold text-white hover:bg-indigo-500 transition-all cursor-pointer"
                            >
                              <Plus className="h-4.5 w-4.5" />
                              Programar Evaluación
                            </button>
                          </div>
                        </form>
                      </div>
                    </div>
                  </div>

                  {/* ======================================= */}
                  {/* QUESTION BANK IA REVIEWER EXPAND PANEL */}
                  {/* ======================================= */}
                  {reviewBank && (
                    <div className="glass-panel p-6 rounded-2xl border-l-4 border-l-purple-500 space-y-6">
                      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
                        <div className="space-y-1">
                          <h3 className="text-lg font-bold text-zinc-200 flex items-center gap-2">
                            <Sparkles className="h-5 w-5 text-purple-400" />
                            Revisión de Preguntas Generadas por IA
                          </h3>
                          <p className="text-xs text-zinc-500">
                            Revisa, edita las alternativas y respuestas correctas antes de aprobar y liberar el cuestionario.
                          </p>
                        </div>

                        <div className="flex items-center gap-3">
                          <button
                            onClick={handleRegenerateBank}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-zinc-850 bg-zinc-900 text-xs text-zinc-300 hover:text-white transition-colors cursor-pointer"
                          >
                            <RefreshCw className="h-3.5 w-3.5" />
                            Regenerar con IA
                          </button>
                          <button
                            onClick={() => setReviewBank(null)}
                            className="p-1.5 rounded-lg border border-zinc-800 text-zinc-400 hover:text-white transition-colors cursor-pointer"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      </div>

                      {/* List of questions for review */}
                      <div className="space-y-4">
                        {reviewBank.questions.map((q: any, qIdx: number) => (
                          <div key={q.id} className="p-4 rounded-xl border border-zinc-900 bg-zinc-950/40 space-y-3">
                            <div className="flex gap-2">
                              <span className="font-bold text-purple-400">{qIdx + 1}.</span>
                              <input
                                type="text"
                                value={q.text}
                                onChange={(e) => handleEditQuestionText(qIdx, e.target.value)}
                                className="flex-1 rounded-lg border border-zinc-800 bg-zinc-950/60 p-2 text-xs text-white focus:border-purple-500 focus:outline-none"
                              />
                            </div>

                            {/* Alternatives */}
                            {q.type === "multiple_choice" && q.options && (
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pl-6">
                                {q.options.map((opt: string, optIdx: number) => (
                                  <div key={optIdx} className="flex items-center gap-2">
                                    <span className="text-[10px] text-zinc-500 font-bold">{String.fromCharCode(65 + optIdx)})</span>
                                    <input
                                      type="text"
                                      value={opt}
                                      onChange={(e) => handleEditQuestionOption(qIdx, optIdx, e.target.value)}
                                      className="flex-1 rounded-lg border border-zinc-850 bg-zinc-950/80 p-2 text-[11px] text-zinc-300 focus:border-purple-500 focus:outline-none"
                                    />
                                    <input
                                      type="radio"
                                      name={`correct-${q.id}`}
                                      checked={q.correct_answer === optIdx.toString()}
                                      onChange={() => handleEditQuestionAnswer(qIdx, optIdx.toString())}
                                      className="h-4 w-4 text-purple-600 focus:ring-purple-500"
                                      title="Marcar como correcta"
                                    />
                                  </div>
                                ))}
                              </div>
                            )}

                            {/* True / False */}
                            {q.type === "true_false" && (
                              <div className="flex gap-4 pl-6 text-xs">
                                <label className="flex items-center gap-2 text-zinc-300">
                                  <input
                                    type="radio"
                                    name={`correct-${q.id}`}
                                    checked={q.correct_answer === "0"}
                                    onChange={() => handleEditQuestionAnswer(qIdx, "0")}
                                    className="text-purple-600"
                                  />
                                  Verdadero (Correcto)
                                </label>
                                <label className="flex items-center gap-2 text-zinc-300">
                                  <input
                                    type="radio"
                                    name={`correct-${q.id}`}
                                    checked={q.correct_answer === "1"}
                                    onChange={() => handleEditQuestionAnswer(qIdx, "1")}
                                    className="text-purple-600"
                                  />
                                  Falso (Correcto)
                                </label>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>

                      {/* Approval Actions */}
                      <div className="flex gap-3 justify-end pt-2 border-t border-zinc-900">
                        <button
                          onClick={() => handleApproveBank(false)}
                          className="flex items-center gap-1 px-4 py-2 rounded-xl border border-zinc-800 text-xs font-semibold text-zinc-400 hover:text-white transition-colors cursor-pointer"
                        >
                          <X className="h-4 w-4" />
                          Rechazar/Editar
                        </button>
                        <button
                          onClick={() => handleApproveBank(true)}
                          className="flex items-center gap-1.5 px-6 py-2.5 rounded-xl bg-purple-600 text-xs font-bold text-white shadow-lg hover:bg-purple-500 transition-all cursor-pointer"
                        >
                          <Check className="h-4.5 w-4.5" />
                          Aprobar y Publicar Cuestionario
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        {/* ==================================== */}
        {/* TAB 2: AVAILABILITY MANAGER */}
        {/* ==================================== */}
        {activeTab === "availability" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Create Availability */}
            <div className="glass-panel p-6 rounded-2xl space-y-4">
              <h2 className="text-lg font-bold text-zinc-100 flex items-center gap-2">
                <Clock className="h-5 w-5 text-indigo-400" />
                Definir Disponibilidad
              </h2>
              <p className="text-xs text-zinc-500 leading-relaxed">
                Define tus bloques semanales recurrentes para defensas orales y verificaciones. El sistema agendará a los estudiantes automáticamente en estos horarios.
              </p>

              <form onSubmit={handleAddAvailability} className="space-y-4 pt-2">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Día de la semana</label>
                  <select
                    value={newAvailDay}
                    onChange={(e) => setNewAvailDay(Number(e.target.value))}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-950/60 p-3 text-xs text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value={0}>Lunes</option>
                    <option value={1}>Martes</option>
                    <option value={2}>Miércoles</option>
                    <option value={3}>Jueves</option>
                    <option value={4}>Viernes</option>
                    <option value={5}>Sábado</option>
                    <option value={6}>Domingo</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Hora Inicio</label>
                    <input
                      type="text"
                      required
                      placeholder="HH:MM (ej. 09:30)"
                      value={newAvailStart}
                      onChange={(e) => setNewAvailStart(e.target.value)}
                      className="w-full rounded-xl border border-zinc-800 bg-zinc-950/60 p-3 text-xs text-white focus:border-indigo-500 focus:outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Hora Término</label>
                    <input
                      type="text"
                      required
                      placeholder="HH:MM (ej. 10:30)"
                      value={newAvailEnd}
                      onChange={(e) => setNewAvailEnd(e.target.value)}
                      className="w-full rounded-xl border border-zinc-800 bg-zinc-950/60 p-3 text-xs text-white focus:border-indigo-500 focus:outline-none"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  className="flex items-center justify-center gap-1.5 w-full rounded-xl bg-indigo-600 py-3 text-xs font-semibold text-white hover:bg-indigo-500 transition-all cursor-pointer"
                >
                  <Plus className="h-4.5 w-4.5" />
                  Agregar Horario
                </button>
              </form>
            </div>

            {/* List Availabilities */}
            <div className="lg:col-span-2 glass-panel p-6 rounded-2xl space-y-4">
              <h2 className="text-lg font-bold text-zinc-100 uppercase tracking-wider">Mis Horarios Registrados</h2>
              
              {availabilities.length === 0 ? (
                <p className="text-sm text-zinc-600 italic">No has ingresado bloques de disponibilidad horaria.</p>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {availabilities.map((a) => (
                    <div 
                      key={a.id} 
                      className="p-4 rounded-xl border border-zinc-900 bg-zinc-950/20 flex items-center justify-between gap-4"
                    >
                      <div className="space-y-1">
                        <span className="font-bold text-zinc-200 text-sm">{getDayName(a.day_of_week)}</span>
                        <p className="text-xs text-zinc-500">Bloque: {a.start_time} - {a.end_time}</p>
                      </div>
                      <button
                        onClick={() => handleDeleteAvailability(a.id)}
                        className="p-2 rounded-lg border border-zinc-900 text-zinc-500 hover:text-red-400 hover:border-red-500/20 transition-all cursor-pointer"
                        title="Eliminar bloque"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ==================================== */}
        {/* TAB 3: APPOINTMENTS & DEFENSES LIST */}
        {/* ==================================== */}
        {activeTab === "appointments" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* List Appointments */}
            <div className="lg:col-span-2 glass-panel p-6 rounded-2xl space-y-4">
              <h2 className="text-lg font-bold text-zinc-100 uppercase tracking-wider">Defensas y Verificaciones Asignadas</h2>
              
              {appointments.length === 0 ? (
                <p className="text-sm text-zinc-600 italic">No hay citas registradas en el sistema.</p>
              ) : (
                <div className="space-y-3">
                  {appointments.map((appt) => (
                    <div 
                      key={appt.id} 
                      className={`p-4 rounded-xl border flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 transition-all ${
                        selectedAppt?.id === appt.id 
                          ? "border-indigo-500 bg-indigo-500/5 shadow-md shadow-indigo-600/5" 
                          : "border-zinc-900 bg-zinc-950/20"
                      }`}
                    >
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border uppercase tracking-wider ${
                            appt.type === "defense"
                              ? "bg-red-500/10 text-red-400 border-red-500/20"
                              : "bg-purple-500/10 text-purple-400 border-purple-500/20"
                          }`}>
                            {appt.type === "defense" ? "Defensa Obligatoria" : "Verificación Aleatoria"}
                          </span>
                          
                          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border uppercase tracking-wider ${
                            appt.status === "completed"
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                          }`}>
                            {appt.status === "pending" ? "Pendiente" : "Finalizado"}
                          </span>
                        </div>

                        <h4 className="font-bold text-zinc-200 text-sm">{appt.student_name}</h4>
                        <p className="text-xs text-zinc-400">
                          <b>Prueba:</b> {appt.evaluation_title} | <b>Horario:</b> {formatDateTime(appt.scheduled_time)}
                        </p>
                        {appt.notes && (
                          <p className="text-[10px] text-zinc-500 italic bg-zinc-950/50 p-2 rounded border border-zinc-900">
                            <b>Notas:</b> {appt.notes}
                          </p>
                        )}
                      </div>

                      {appt.status === "pending" && (
                        <button
                          onClick={() => {
                            setSelectedAppt(appt);
                            setApptFeedbackStatus("completed");
                          }}
                          className="rounded-lg bg-indigo-600 hover:bg-indigo-500 px-4 py-2 text-xs font-bold text-white transition-all cursor-pointer shrink-0"
                        >
                          Calificar Defensa
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Resolve selected Appointment */}
            {selectedAppt ? (
              <div className="glass-panel p-6 rounded-2xl border-l-4 border-l-indigo-500 space-y-4">
                <div className="flex justify-between items-center pb-2 border-b border-zinc-800">
                  <h3 className="text-sm font-bold text-zinc-200 uppercase tracking-wider">
                    Evaluar Defensa
                  </h3>
                  <button
                    onClick={() => setSelectedAppt(null)}
                    className="p-1 rounded border border-zinc-800 text-zinc-500 hover:text-white cursor-pointer"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>

                <div className="text-xs text-zinc-400 space-y-1 bg-zinc-950/40 p-3 rounded-xl border border-zinc-900">
                  <p><b>Alumno:</b> {selectedAppt.student_name}</p>
                  <p><b>Evaluación:</b> {selectedAppt.evaluation_title}</p>
                  <p><b>Fecha cita:</b> {formatDateTime(selectedAppt.scheduled_time)}</p>
                </div>

                <form onSubmit={handleSubmitFeedback} className="space-y-4 pt-2 text-xs">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Estado</label>
                    <select
                      value={apptFeedbackStatus}
                      onChange={(e) => setApptFeedbackStatus(e.target.value)}
                      className="w-full rounded-xl border border-zinc-800 bg-zinc-950/60 p-3 text-xs text-white focus:border-indigo-500 focus:outline-none"
                    >
                      <option value="completed">Completada (Asistió)</option>
                      <option value="cancelled">No Asistió (Reprobada)</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Notas de Retroalimentación</label>
                    <textarea
                      required
                      placeholder="Escribe comentarios sobre la defensa oral del estudiante..."
                      rows={4}
                      value={apptFeedbackNotes}
                      onChange={(e) => setApptFeedbackNotes(e.target.value)}
                      className="w-full rounded-xl border border-zinc-800 bg-zinc-950/60 p-3 text-xs text-white focus:border-indigo-500 focus:outline-none"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Ajuste de Nota Final (Correctas, opcional)</label>
                    <input
                      type="number"
                      placeholder="ej. 4 (vacío para no modificar)"
                      value={apptFeedbackScore}
                      onChange={(e) => setApptFeedbackScore(e.target.value === "" ? "" : Number(e.target.value))}
                      className="w-full rounded-xl border border-zinc-800 bg-zinc-950/60 p-3 text-xs text-white focus:border-indigo-500 focus:outline-none"
                    />
                    <span className="text-[9px] text-zinc-500 block leading-tight mt-1">
                      * Modifica el puntaje obtenido originalmente en la prueba flash por este nuevo valor en el acta oficial.
                    </span>
                  </div>

                  <button
                    type="submit"
                    className="flex items-center justify-center gap-1.5 w-full rounded-xl bg-indigo-600 py-3 font-bold text-white hover:bg-indigo-500 transition-all cursor-pointer"
                  >
                    <CheckCircle2 className="h-4.5 w-4.5" />
                    Registrar Resultado
                  </button>
                </form>
              </div>
            ) : (
              <div className="glass-panel p-6 rounded-2xl text-center p-8 border border-dashed border-zinc-850">
                <Award className="h-8 w-8 text-zinc-600 mx-auto mb-2" />
                <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-wider">Cerrar Citas</h3>
                <p className="text-xs text-zinc-500 leading-relaxed mt-1.5">
                  Selecciona una cita pendiente de la lista para registrar la asistencia del alumno, ingresar notas de retroalimentación o corregir el puntaje oficial de la evaluación.
                </p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

"use client";

import React, { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  BookOpen, Plus, Users, Award, Calendar, FileText, CheckCircle2,
  Trash2, Edit, AlertCircle, RefreshCw, Send, Check, X, BarChart3,
  Clock, Sparkles, Upload, FileUp, Download, Eye, ChevronRight, Sliders,
  HelpCircle, UserCheck, Mail, ShieldAlert, AlertTriangle
} from "lucide-react";
import Navbar from "@/components/Navbar";
import TeacherTutorial from "@/components/TeacherTutorial";
import UploadQueue from "@/components/UploadQueue";
import EvaluationOperations from "@/components/EvaluationOperations";
import AppointmentForm from "@/components/AppointmentForm";
import StudentEditor from "@/components/StudentEditor";
import AdminTeacherContext from "@/components/AdminTeacherContext";
import { api, getToken, getRole, getTeacherContext, request } from "@/lib/api";

export default function TeacherDashboard() {
  const router = useRouter();
  const courseLoad=useRef(0),evalLoad=useRef(0);
  const [loading, setLoading] = useState(true);
  const [studentToEdit,setStudentToEdit]=useState<any>(null);
  const [accountRole,setAccountRole]=useState("");
  const [adminTeacher,setAdminTeacher]=useState<any>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [flashLink, setFlashLink] = useState("");

  // Navigation Tabs
  const [activeTab, changeActiveTab] = useState<
    "courses" | "students" | "evaluations" | "materials" | "reports" | "questions" | "results" | "appointments" | "availability"
  >("courses");

  const setActiveTab=(value:typeof activeTab)=>{const url=new URL(location.href);url.searchParams.set('seccion',value);if(selectedCourseId)url.searchParams.set('curso',String(selectedCourseId));if(selectedEvalId)url.searchParams.set('evaluacion',String(selectedEvalId));history.pushState(null,'',url);changeActiveTab(value);};
  useEffect(()=>{const restore=()=>{const q=new URLSearchParams(location.search);const section=q.get('seccion');if(['courses','students','evaluations','materials','reports','questions','results','appointments','availability'].includes(section||''))changeActiveTab(section as typeof activeTab);else changeActiveTab('courses');const c=Number(q.get('curso'));if(c)setSelectedCourseId(c);const e=Number(q.get('evaluacion'));if(e)setSelectedEvalId(e);};restore();window.addEventListener('popstate',restore);return()=>window.removeEventListener('popstate',restore);},[]);
  // Courses & Selections
  const [courses, setCourses] = useState<any[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [selectedCourse, setSelectedCourse] = useState<any | null>(null);

  // Evaluations
  const [courseEvals, setCourseEvals] = useState<any[]>([]);
  const [selectedEvalId, setSelectedEvalId] = useState<number | null>(null);
  const [selectedEval, setSelectedEval] = useState<any | null>(null);

  // Students list
  const [students, setStudents] = useState<any[]>([]);
  const [newStudentName, setNewStudentName] = useState("");
  const [newStudentEmail, setNewStudentEmail] = useState("");
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvImporting, setCsvImporting] = useState(false);

  // Course Materials
  const [materials, setMaterials] = useState<any[]>([]);
  const [newMaterialTitle, setNewMaterialTitle] = useState("");
  const [newMaterialFile, setNewMaterialFile] = useState<File | null>(null);
  const [uploadingMaterial, setUploadingMaterial] = useState(false);

  // Reports
  const [reports, setReports] = useState<any[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [selectedReport, setSelectedReport] = useState<any | null>(null);
  const [reportMarkdown, setReportMarkdown] = useState<string>("");
  const [previewMdModal, setPreviewMdModal] = useState(false);

  // Bulk Upload
  const [bulkFiles, setBulkFiles] = useState<File[]>([]);
  const [bulkMapping, setBulkMapping] = useState<{ [filename: string]: number }>({});
  const [bulkUploading, setBulkUploading] = useState(false);

  // Question Pool Management
  const [questionBank, setQuestionBank] = useState<any | null>(null);
  const [selectedQIds, setSelectedQIds] = useState<number[]>([]);
  const [newQText, setNewQText] = useState("");
  const [newQType, setNewQType] = useState<"multiple_choice" | "true_false">("multiple_choice");
  const [newQOptions, setNewQOptions] = useState<string[]>(["", "", "", ""]);
  const [newQCorrect, setNewQCorrect] = useState("0");
  const [showAddQModal, setShowAddQModal] = useState(false);

  // Score override
  const [scoreOverrides, setScoreOverrides] = useState<Record<number,string>>({});

  // Evaluation Creation Form
  const [newCourseName, setNewCourseName] = useState("");
  const [newCoursePeriod, setNewCoursePeriod] = useState("");
  const [newEvalTitle, setNewEvalTitle] = useState("");
  const [newEvalRubric, setNewEvalRubric] = useState("");
  const [newEvalRigor, setNewEvalRigor] = useState("medium");
  const [newEvalPoolSize, setNewEvalPoolSize] = useState(20);
  const [newEvalFlashCount, setNewEvalFlashCount] = useState(10);
  const [newEvalTime, setNewEvalTime] = useState(30);
  const [newEvalLowThresh, setNewEvalLowThresh] = useState(0.6);
  const [newEvalHighThresh, setNewEvalHighThresh] = useState(0.4);
  const [newEvalRandomPct, setNewEvalRandomPct] = useState(0.1);

  const [creatingEval,setCreatingEval]=useState(false);
  const [appointmentDraft,setAppointmentDraft]=useState<any>(null);
  // Appointments & Availability
  const [appointments, setAppointments] = useState<any[]>([]);
  const [availabilities, setAvailabilities] = useState<any[]>([]);
  const [selectedAppt, setSelectedAppt] = useState<any | null>(null);
  const [apptStatus, setApptStatus] = useState("completed");
  const [apptNotes, setApptNotes] = useState("");
  const [apptAdjustedScore, setApptAdjustedScore] = useState<string>("");
  const [newAvailDay, setNewAvailDay] = useState(0);
  const [newAvailStart, setNewAvailStart] = useState("09:00");
  const [newAvailEnd, setNewAvailEnd] = useState("11:00");

  // Stats / Results
  const [evalStats, setEvalStats] = useState<any | null>(null);
  const [reviewList, setReviewList] = useState<any[]>([]);

  useEffect(() => {
    const token = getToken();
    const role = getRole();
    if (!token || !["teacher", "admin", "assistant"].includes(role || "")) {
      router.push("/login");
      return;
    }
    if(role==='admin'&&!getTeacherContext()){router.replace('/admin/dashboard');return;}
    loadInitialData();
  }, [router]);

  useEffect(() => {
    if (!selectedCourseId || !selectedEvalId || !getToken()) return;
    let disposed = false; let socket:WebSocket | null = null; let retry:ReturnType<typeof setTimeout>;
    const connect = () => {
      socket = new WebSocket(`ws://127.0.0.1:8000/ws/panel/${selectedCourseId}?token=${encodeURIComponent(getToken() || '')}`);
      socket.onmessage = event => { const data = JSON.parse(event.data); if (data.type === 'STUDENT_TEST_FINISHED') { loadEvalSubData(selectedEvalId); loadAppointments(); } };
      socket.onclose = () => { if(!disposed) retry=setTimeout(connect,3000); };
    };
    connect();
    return () => { disposed=true;clearTimeout(retry);socket?.close(); };
  }, [selectedCourseId, selectedEvalId]);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const me = await api.getMe();
      setAccountRole(me.rol);
      if(me.rol==='admin'){
        const id=getTeacherContext();if(!id){router.replace('/admin/dashboard');return;}
        setAdminTeacher(await request(`/admin/profesores/${id}`));
      }
      if(me.rol==='ayudante'&&location.pathname.startsWith('/teacher/')){router.replace('/assistant/dashboard');return;}
      const crs = await api.getCourses();
      setCourses(crs);
      setSelectedCourseId(crs.find((c:any)=>c.id===Number(new URLSearchParams(location.search).get('curso')))?.id||crs[0]?.id||null);
      setSelectedCourse(crs[0]||null);
      if(!crs.length){setStudents([]);setCourseEvals([]);setSelectedEvalId(null);setSelectedEval(null);setReports([]);setMaterials([]);setEvalStats(null);setReviewList([]);}
      await loadAppointments();
      await loadAvailabilities();
    } catch (err: any) {
      setError(err.message || "Error al cargar datos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedCourseId) {
      const c = courses.find((x) => x.id === selectedCourseId);
      setSelectedCourse(c || null);
      loadCourseSubData(selectedCourseId);
    }
  }, [selectedCourseId]);

  const loadCourseSubData = async (cId: number) => {
    const version=++courseLoad.current;++evalLoad.current;setReports([]);setEvalStats(null);setReviewList([]);setSelectedReportId(null);setQuestionBank(null);
    try {
      const st = await api.getStudents(cId);
      if(version!==courseLoad.current)return;setStudents(st);
      const evs = await api.getCourseEvaluations(cId);
      if(version!==courseLoad.current)return;setCourseEvals(evs);
      if (evs.length > 0) {
        const preferred=evs.find((e:any)=>e.id===Number(new URLSearchParams(location.search).get('evaluacion')))||evs[0];setSelectedEvalId(preferred.id);
        setSelectedEval(preferred);
      } else {
        setSelectedEvalId(null);
        setSelectedEval(null);
        setReports([]);
        setMaterials([]);
      }
    } catch (err: any) {
      setError(err.message || "No se pudieron cargar los datos");
    }
  };

  useEffect(() => {
    if (selectedEvalId && courseEvals.some(x=>x.id===selectedEvalId)) {
      setSelectedAppt(null);setReports([]);setEvalStats(null);setReviewList([]);
      const ev = courseEvals.find((x) => x.id === selectedEvalId);
      setSelectedEval(ev || null);
      if (ev) { setNewEvalTitle(ev.title); setNewEvalRubric(ev.prompt_rubric); setNewEvalRigor(ev.question_rigor); setNewEvalPoolSize(ev.pool_size); setNewEvalFlashCount(ev.flash_questions_count); setNewEvalTime(ev.time_per_question); setNewEvalLowThresh(ev.low_threshold); setNewEvalHighThresh(ev.high_threshold); }
      loadEvalSubData(selectedEvalId);
    }
  }, [selectedEvalId, courseEvals]);

  const loadEvalSubData = async (eId: number) => {
    const version=++evalLoad.current;
    try {
      const [mats,reps,stats,rev]=await Promise.all([api.getMaterials(eId),api.getReports(eId),api.getEvaluationStats(eId),api.getReviewList(eId)]);
      if(version!==evalLoad.current)return;
      setMaterials(mats);setReports(reps);setEvalStats(stats);setReviewList(rev.review_list||[]);
    } catch (err:any) {if(version===evalLoad.current)setError(err.message||'No se pudieron cargar los datos');}
  };

  const loadAppointments = async () => {
    try {
      const data = await api.getAppointments();
      setAppointments(data);
    } catch (err) {}
  };

  const loadAvailabilities = async () => {
    try {
      const data = await api.getTeacherAvailabilities();
      setAvailabilities(data);
    } catch (err) {}
  };

  // --- ACTIONS: Students ---
  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId) return;
    setError("");
    setSuccess("");
    try {
      await api.createStudent(selectedCourseId, {
        name: newStudentName,
        email: newStudentEmail,
      });
      setSuccess("Estudiante agregado correctamente.");
      setNewStudentName("");
      setNewStudentEmail("");
      const st = await api.getStudents(selectedCourseId);
      setStudents(st);
    } catch (err: any) {
      setError(err.message || "Error al agregar estudiante");
    }
  };

  const handleImportCSV = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId || !csvFile) return;
    setError("");
    setSuccess("");
    setCsvImporting(true);
    try {
      const res = await api.importStudentsCSV(selectedCourseId, csvFile);
      setSuccess(`Importación lista: ${res.created} agregados, ${res.skipped} ya existían.`);
      if (res.errores?.length) setError(res.errores.join("; "));
      setCsvFile(null);
      const st = await api.getStudents(selectedCourseId);
      setStudents(st);
    } catch (err: any) {
      setError(err.message || "Error al importar CSV");
    } finally {
      setCsvImporting(false);
    }
  };

  const handleDeleteStudent = async (studentId: number) => {
    if (!selectedCourseId || !confirm("¿Retirar este estudiante de la nómina activa del curso?")) return;
    try {
      await api.deleteStudent(selectedCourseId, studentId);
      setSuccess("Estudiante eliminado.");
      const st = await api.getStudents(selectedCourseId);
      setStudents(st);
    } catch (err: any) {
      setError(err.message || "Error al eliminar");
    }
  };

  // --- ACTIONS: Evaluations ---
  const handleCreateEvaluation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId) return;
    setError("");
    setSuccess("");
    try {
      const save=creatingEval?api.createEvaluation:api.updateEvaluation;
      const created = await save(creatingEval?selectedCourseId:selectedEvalId!, {
        title: newEvalTitle,
        prompt_rubric: newEvalRubric,
        question_rigor: newEvalRigor,
        pool_size: Number(newEvalPoolSize),
        flash_questions_count: Number(newEvalFlashCount),
        time_per_question: Number(newEvalTime),
        low_threshold: Number(newEvalLowThresh),
        high_threshold: Number(newEvalHighThresh),
        random_review_pct: Number(newEvalRandomPct),
      });
      setSuccess(creatingEval?"Evaluación creada.":"Evaluación actualizada.");setCreatingEval(false);
      setSelectedEval(created);
      const evs = await api.getCourseEvaluations(selectedCourseId);
      setCourseEvals(evs);
      setSelectedEvalId(created.id);
      const nextUrl=new URL(location.href);nextUrl.searchParams.set('evaluacion',String(created.id));nextUrl.searchParams.set('curso',String(selectedCourseId));nextUrl.searchParams.set('seccion','materials');history.pushState(null,'',nextUrl);changeActiveTab('materials');
    } catch (err: any) {
      setError(err.message || "Error al crear evaluación");
    }
  };

  // --- ACTIONS: Course Materials ---
  const handleUploadMaterial = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvalId || !newMaterialFile || !newMaterialTitle) return;
    setError("");
    setSuccess("");
    setUploadingMaterial(true);
    try {
      await api.uploadMaterial(selectedEvalId, newMaterialTitle, newMaterialFile);
      setSuccess("Material de apoyo subido y convertido a Markdown para el contexto IA.");
      setNewMaterialTitle("");
      setNewMaterialFile(null);
      const mats = await api.getMaterials(selectedEvalId);
      setMaterials(mats);
    } catch (err: any) {
      setError(err.message || "Error al subir material");
    } finally {
      setUploadingMaterial(false);
    }
  };

  const handleDeleteMaterial = async (matId: number) => {
    if (!selectedEvalId || !confirm("¿Eliminar este material?")) return;
    try {
      await api.deleteMaterial(selectedEvalId, matId);
      setSuccess("Material eliminado.");
      const mats = await api.getMaterials(selectedEvalId);
      setMaterials(mats);
    } catch (err: any) {
      setError(err.message || "Error al eliminar");
    }
  };

  // --- ACTIONS: Bulk Reports Upload ---
  const handleBulkFilesSelect = (files: FileList | null) => {
    if (!files) return;
    const fileArr = Array.from(files);
    setBulkFiles(fileArr);

    const mapping: { [key: string]: number } = {};
    fileArr.forEach((file) => {
      const lower = file.name.toLowerCase();
      const match = students.find(
        (s) =>
          lower.includes(s.name.toLowerCase().split(" ")[0]) ||
          lower.includes(s.email.split("@")[0].toLowerCase())
      );
      if (match) {
        mapping[file.name] = match.id;
      }
    });
    setBulkMapping(mapping);
  };

  const handleExecuteBulkUpload = async () => {
    if (!selectedEvalId || bulkFiles.length === 0) return;
    const unmapped = bulkFiles.filter((f) => !bulkMapping[f.name]);
    if (unmapped.length > 0) {
      setError(`Falta asociar ${unmapped.length} archivo(s) a un estudiante.`);
      return;
    }

    const studentIds = bulkFiles.map((f) => bulkMapping[f.name]);
    setError("");
    setSuccess("");
    setBulkUploading(true);

    try {
      await api.bulkUploadReports(selectedEvalId, studentIds, bulkFiles);
      setSuccess("Archivos en cola. Puedes seguir el avance y reintentar errores individualmente.");
      setBulkFiles([]);
      setBulkMapping({});
      await loadEvalSubData(selectedEvalId);
      setActiveTab("reports");
    } catch (err: any) {
      setError(err.message || "Error en la subida en lote");
    } finally {
      setBulkUploading(false);
    }
  };

  const handleReanalyze = async (reportId: number) => {
    try {
      await api.reanalyzeReport(reportId);
      setSuccess("Reanálisis iniciado.");
      if (selectedEvalId) loadEvalSubData(selectedEvalId);
    } catch (err: any) {
      setError(err.message || "Error al reanalizar");
    }
  };

  const handleScoreOverride = async (reportId: number) => {
    const sid = reports.find((r:any)=>r.id===reportId)?.student_id;
    const num = parseFloat(scoreOverrides[sid] || "");
    if (isNaN(num) || num < 0 || num > 1) {
      setError("La nota debe ser un decimal entre 0.0 y 1.0 (ej. 0.85 = 85%)");
      return;
    }
    try {
      const reason = window.prompt("Justificación pedagógica del logro final:");
      if (!reason?.trim()) { setError("Debe indicar una justificación pedagógica"); return; }
      await api.updateReportScore(reportId, num, reason);
      setSuccess("Nota actualizada correctamente.");
      setScoreOverrides(previous=>({...previous,[sid]:""}));
      if (selectedEvalId) loadEvalSubData(selectedEvalId);
    } catch (err: any) {
      setError(err.message || "Error al modificar nota");
    }
  };

  const handlePreviewMarkdown = async (reportId: number) => {
    try {
      const data = await api.getReportMarkdown(reportId);
      setReportMarkdown(data.markdown || "Sin contenido Markdown extraído.");
      setPreviewMdModal(true);
    } catch (err: any) {
      setError("No se pudo cargar el Markdown");
    }
  };

  // --- ACTIONS: Question Pool ---
  const handleOpenQuestions = async (report: any) => {
    setSelectedReport(report);
    setSelectedReportId(report.id);
    setActiveTab("questions");
    try {
      const bank = await api.getQuestionBank(report.id);
      setQuestionBank(bank);
      setSelectedQIds(bank.selected_question_ids || []);
    } catch (err: any) {
      setError(err.message || "Banco de preguntas no disponible aún.");
      setQuestionBank(null);
    }
  };

  const handleToggleSelectQuestion = (qId: number) => {
    setSelectedQIds((prev) =>
      prev.includes(qId) ? prev.filter((id) => id !== qId) : [...prev, qId]
    );
  };

  const handleSelectRandom = async () => {
    if (!selectedReportId) return;
    try {
      const updatedBank = await api.selectRandomQuestions(selectedReportId);
      setQuestionBank(updatedBank);
      setSelectedQIds(updatedBank.selected_question_ids || []);
      setSuccess("Preguntas seleccionadas aleatoriamente.");
    } catch (err: any) {
      setError(err.message || "Error al seleccionar aleatoriamente");
    }
  };

  const handleSaveSelectedQuestions = async () => {
    if (!selectedReportId) return;
    try {
      const updatedBank = await api.selectQuestions(selectedReportId, selectedQIds);
      setQuestionBank(updatedBank);
      setSuccess("Selección de preguntas guardada.");
    } catch (err: any) {
      setError(err.message || "Error al guardar selección");
    }
  };

  const handleSendFlashTest = async () => {
    if (!selectedReportId) return;
    if (selectedQIds.length === 0) {
      setError("Debes seleccionar al menos una pregunta antes de enviar.");
      return;
    }
    setError("");
    try {
      await api.selectQuestions(selectedReportId, selectedQIds);
      const dispatch = await api.sendFlashTest(selectedReportId);
      const item = dispatch.items?.[0];
      if (!item) { setError('El test ya fue completado o no hay preguntas seleccionadas.'); return; }
      setSuccess(item.correo_enviado ? 'Correo enviado con el enlace de verificación.' : 'Enlace disponible. SMTP no envió correo.');
      setFlashLink(item.enlace_test);
      if (selectedEvalId) loadEvalSubData(selectedEvalId);
      const bank = await api.getQuestionBank(selectedReportId);
      setQuestionBank(bank);
    } catch (err: any) {
      setError(err.message || "Error al enviar el Flash Test");
    }
  };

  const handleCreateCustomQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReportId || !newQText) return;
    try {
      await api.createQuestion(selectedReportId, {
        text: newQText,
        type: newQType,
        options: newQType === "multiple_choice" ? newQOptions : ["Verdadero", "Falso"],
        correct_answer: newQCorrect,
        limit_seconds: selectedEval?.time_per_question || 30,
      });
      setSuccess("Pregunta agregada al pool.");
      setShowAddQModal(false);
      setNewQText("");
      setNewQOptions(["", "", "", ""]);
      setNewQCorrect("0");
      const bank = await api.getQuestionBank(selectedReportId);
      setQuestionBank(bank);
    } catch (err: any) {
      setError(err.message || "Error al crear pregunta");
    }
  };

  const handleEditQuestion = async (question:any) => {
    const text=window.prompt('Enunciado de la pregunta:',question.text);if(!text)return;
    const raw=window.prompt('Alternativas (lista JSON):',JSON.stringify(question.options));if(!raw)return;
    const answer=window.prompt('Letra de la alternativa correcta:',String.fromCharCode(65+Number(question.correct_answer)));if(!answer)return;
    try { const options=JSON.parse(raw); if(!Array.isArray(options)||options.some(v=>typeof v!=='string'))throw new Error('Indique una lista de textos');
      await api.updateQuestion(selectedReportId!,question.id,{text,options,correct_answer:String(answer.trim().toUpperCase().charCodeAt(0)-65)});
      setQuestionBank(await api.getQuestionBank(selectedReportId!));setSuccess('Pregunta actualizada');
    }catch(error:any){setError(error.message);}
  };

  const handleDeleteQuestion = async (qId: number) => {
    if (!selectedReportId || !confirm("¿Eliminar pregunta del pool?")) return;
    try {
      await api.deleteQuestion(selectedReportId, qId);
      setSuccess("Pregunta eliminada.");
      const bank = await api.getQuestionBank(selectedReportId);
      setQuestionBank(bank);
      setSelectedQIds((prev) => prev.filter((id) => id !== qId));
    } catch (err: any) {
      setError(err.message || "Error al eliminar");
    }
  };

  // --- ACTIONS: Appointments & Availability ---
  const handleSubmitApptFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAppt) return;
    try {
      await api.submitAppointmentFeedback(selectedAppt.id, {
        status: apptStatus,
        notes: apptNotes,
        adjusted_score: apptAdjustedScore !== "" ? parseFloat(apptAdjustedScore) : null,
      });
      setSuccess("Cita registrada y calificación final actualizada.");
      setSelectedAppt(null);
      setApptNotes("");
      setApptAdjustedScore("");
      loadAppointments();
      if (selectedEvalId) loadEvalSubData(selectedEvalId);
    } catch (err: any) {
      setError(err.message || "Error al guardar feedback");
    }
  };

  const handleAddAvailability = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.addTeacherAvailability({
        day_of_week: Number(newAvailDay),
        start_time: newAvailStart,
        end_time: newAvailEnd,
      });
      setSuccess("Horario de disponibilidad agregado.");
      loadAvailabilities();
    } catch (err: any) {
      setError(err.message || "Error al agregar horario");
    }
  };

  const handleDeleteAvailability = async (id: number) => {
    try {
      await api.deleteTeacherAvailability(id);
      loadAvailabilities();
    } catch (err: any) {
      setError("Error al eliminar horario");
    }
  };

  const scheduleDefense = (studentId:number) => setAppointmentDraft({estudiante_id:studentId});
  const saveAppointment=async(studentId:number,date:string,block:string)=>{if(!selectedCourseId)return;if(appointmentDraft?.id)await api.rescheduleAppointment(appointmentDraft.id,date,block);else await api.scheduleAppointment(selectedCourseId,{estudiante_id:studentId,fecha:date,bloque:block,actividad_id:selectedEvalId&&selectedEvalId<0?-selectedEvalId:null});setSuccess('Cita guardada con la fecha elegida.');await loadAppointments();if(selectedEvalId)await loadEvalSubData(selectedEvalId);};

  const getDayName = (d: number) =>
    ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][d] || "";

  if (loading) {
    return (
      <div className="ie-shell ie-teacher-view flex min-h-screen flex-col">
        <Navbar />
        <div className="flex flex-1 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
        </div>
      </div>
    );
  }

  return (
    <div className="ie-shell ie-teacher-view flex min-h-screen flex-col pb-20">
      <Navbar />
      {appointmentDraft&&<AppointmentForm students={students} initial={appointmentDraft} onSave={saveAppointment} onClose={()=>setAppointmentDraft(null)}/>}
      <TeacherTutorial onStep={setActiveTab} assistant={accountRole==='ayudante'}/>
      {studentToEdit&&selectedCourseId&&<StudentEditor courseId={selectedCourseId} student={studentToEdit} onClose={()=>setStudentToEdit(null)} onSaved={()=>loadCourseSubData(selectedCourseId)}/>}
      <main className="max-w-7xl w-full mx-auto px-4 sm:px-6 mt-6 flex flex-col gap-6">
        {adminTeacher&&<AdminTeacherContext person={adminTeacher} courses={courses} onChanged={loadInitialData}/>}
        <div className="flex justify-between items-center"><span className="text-xs text-zinc-500">{accountRole==='ayudante'?'Ayudantía · Nómina de solo lectura':'Docencia · Cursos asignados'}</span><button className="ie-button" onClick={()=>window.dispatchEvent(new Event("integryeval:open-tutorial"))}><BookOpen size={16}/>Guía de uso</button></div>
        {/* Top Header & Course / Eval Pickers */}
        <div className="glass-panel p-5 rounded-2xl border border-zinc-800 bg-zinc-950/40 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-indigo-400" />
              {adminTeacher?`Espacio de ${adminTeacher.nombre}`:accountRole==='ayudante'?'Panel de Evaluación · Ayudante':'Panel de Evaluación Docente'}
            </h1>
            <p className="text-xs text-zinc-400 mt-0.5">
              Gestión semi-automatizada: análisis con IA, pool de preguntas y defensa flash.
            </p>
          </div>

          <div className="ie-course-controls flex flex-wrap items-center gap-3">
            {/* Course Selector */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-zinc-400">Curso:</span>
              <select
                data-tour="course-selector"
                aria-label="Asignatura activa"
                value={selectedCourseId || ""}
                onChange={(e) => {const id=Number(e.target.value);const url=new URL(location.href);url.searchParams.set('curso',String(id));url.searchParams.delete('evaluacion');history.pushState(null,'',url);setSelectedCourseId(id);}}
                className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs text-white focus:border-indigo-500 focus:outline-none"
              >
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.period})
                  </option>
                ))}
              </select>
            </div>

            {/* Evaluation Selector */}
            {courseEvals.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-zinc-400">Evaluación:</span>
                <select
                  value={selectedEvalId || ""}
                  aria-label="Evaluación activa" onChange={(e) => {const id=Number(e.target.value);const url=new URL(location.href);url.searchParams.set('evaluacion',String(id));if(selectedCourseId)url.searchParams.set('curso',String(selectedCourseId));history.pushState(null,'',url);setSelectedEvalId(id);setSelectedReportId(null);setSelectedReport(null);setQuestionBank(null);setCreatingEval(false);}}
                  className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs text-indigo-300 font-medium focus:border-indigo-500 focus:outline-none"
                >
                  {courseEvals.map((ev) => (
                    <option key={ev.id} value={ev.id}>
                      {ev.title}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>

        {selectedCourseId&&selectedEval&&<EvaluationOperations courseId={selectedCourseId} evaluation={selectedEval} onChanged={async()=>{const evs=await api.getCourseEvaluations(selectedCourseId);setCourseEvals(evs);setSelectedEval(evs.find((ev:any)=>ev.id===selectedEvalId)||null);}}/>}
        {/* Global Notifications */}
        {error && (
          <div className="flex items-center justify-between rounded-xl bg-red-500/10 border border-red-500/20 p-4 text-xs text-red-400">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError("")} className="text-red-400 hover:text-white">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}
        {success && (
          <div className="flex items-center justify-between rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-4 text-xs text-emerald-400">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span>{success}</span>
            </div>
            <button onClick={() => setSuccess("")} className="text-emerald-400 hover:text-white">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {flashLink && <div className="glass-panel p-4 rounded-xl text-sm text-indigo-300"><a href={flashLink} target="_blank" rel="noopener noreferrer">Abrir Flash Test del estudiante ↗</a><p className="text-xs text-zinc-400 mt-2">{flashLink}</p></div>}
        {/* Main Tab Navigation */}
        <div className="flex border-b border-zinc-800 overflow-x-auto gap-1 pb-1 text-xs">
          {[
            { id: "courses", label: "1. Cursos", icon: BookOpen },
            { id: "students", label: "2. Estudiantes (Roster)", icon: Users },
            { id: "evaluations", label: "3. Parámetros Evaluación", icon: Sliders },
            { id: "materials", label: "4. Materiales de Apoyo", icon: FileText },
            { id: "reports", label: "5. Trabajos & Análisis IA", icon: FileUp },
            { id: "questions", label: "6. Pool de Preguntas", icon: HelpCircle },
            { id: "results", label: "7. Resultados & Citas", icon: BarChart3 },
            { id: "appointments", label: "8. Citas de Oficina", icon: UserCheck },
            { id: "availability", label: "9. Disponibilidad", icon: Calendar },
          ].map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                data-tour={`tab-${tab.id}`}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-1.5 px-4 py-2.5 rounded-t-xl font-semibold border-b-2 transition-all whitespace-nowrap ${
                  active
                    ? "border-indigo-500 bg-indigo-950/20 text-indigo-400"
                    : "border-transparent text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/40"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* ========================================================= */}
        {/* TAB 1: COURSES */}
        {/* ========================================================= */}
        {activeTab === "courses" && (
          <div className="grid grid-cols-1 gap-6">
            <div className="glass-panel p-5 rounded-2xl border border-zinc-800 bg-zinc-950/40 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-indigo-400" /> Asignaturas asignadas
              </h3>
              {!courses.length && <p className="ie-empty">Aún no tienes asignaturas asignadas. Solicita al administrador que te dé acceso a un curso.</p>}
              <p className="text-xs text-zinc-400">El administrador crea las asignaturas y asigna a sus docentes. Puedes trabajar con la nómina, materiales e informes de tus cursos.</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {courses.map((c) => (
                  <div
                    key={c.id}
                    onClick={() => setSelectedCourseId(c.id)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${
                      selectedCourseId === c.id
                        ? "border-indigo-500 bg-indigo-950/30 ring-1 ring-indigo-500"
                        : "border-zinc-800 bg-zinc-900/40 hover:border-zinc-700"
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <h4 className="font-bold text-sm text-white">{c.name}</h4>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono">
                        {c.period}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-400 mt-2">
                      Estudiantes registrados: <span className="text-indigo-400 font-semibold">{c.student_count || 0}</span>
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 2: STUDENTS (ROSTER) */}
        {/* ========================================================= */}
        {activeTab === "students" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {accountRole!=='ayudante'&&<div className="space-y-6">
              {/* CSV Upload */}
              <div className="glass-panel p-5 rounded-2xl border border-zinc-800 bg-zinc-950/40 space-y-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Upload className="h-4 w-4 text-indigo-400" /> Cargar Lista CSV
                </h3>
                <p className="text-xs text-zinc-400">
                  Carga un archivo CSV con columnas <b>Nombre</b> y <b>Correo</b>. Los alumnos no requieren crearse cuenta.
                </p>
                <form data-tour="csv-import" onSubmit={handleImportCSV} className="space-y-3">
                  <input
                    type="file"
                    accept=".csv"
                    required
                    onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                    className="w-full text-xs text-zinc-400 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
                  />
                  <button
                    type="submit"
                    disabled={csvImporting || !csvFile}
                    className="w-full rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 py-2.5 text-xs font-bold text-white transition-colors"
                  >
                    {csvImporting ? "Importando..." : "Importar Estudiantes"}
                  </button>
                </form>
              </div>

              {/* Add Single Student */}
              <div className="glass-panel p-5 rounded-2xl border border-zinc-800 bg-zinc-950/40 space-y-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Plus className="h-4 w-4 text-indigo-400" /> Agregar Individual
                </h3>
                <form onSubmit={handleCreateStudent} className="space-y-3">
                  <input
                    type="text"
                    required
                    placeholder="Nombre Completo"
                    value={newStudentName}
                    onChange={(e) => setNewStudentName(e.target.value)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-900/80 p-2.5 text-xs text-white focus:border-indigo-500 focus:outline-none"
                  />
                  <input
                    type="email"
                    required
                    placeholder="estudiante@universidad.cl"
                    value={newStudentEmail}
                    onChange={(e) => setNewStudentEmail(e.target.value)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-900/80 p-2.5 text-xs text-white focus:border-indigo-500 focus:outline-none"
                  />
                  <button
                    type="submit"
                    className="w-full rounded-xl bg-zinc-800 hover:bg-zinc-700 py-2.5 text-xs font-bold text-white transition-colors"
                  >
                    Agregar Estudiante
                  </button>
                </form>
              </div>
            </div>}

            {accountRole==='ayudante'&&<div className="ie-readonly-note">Puedes consultar los alumnos del curso. Agregar, importar, editar o retirar alumnos corresponde al profesor y al superadministrador.</div>}
            {/* Students Table */}
            <div className={`${accountRole==='ayudante'?'md:col-span-3':'md:col-span-2'} glass-panel p-5 rounded-2xl border border-zinc-800 bg-zinc-950/40 space-y-4`}>
              <div className="flex justify-between items-center">
                <h3 data-tour="student-roster" className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Users className="h-4 w-4 text-indigo-400" /> Nómina del Curso ({students.length})
                </h3>
              </div>

              {students.length === 0 ? (
                <p className="text-xs text-zinc-500 italic py-8 text-center">
                  {accountRole==='ayudante'?'El curso todavía no tiene alumnos. El profesor o el superadministrador debe cargar la nómina.':'No hay estudiantes registrados en este curso. Sube un CSV o agrégalos manualmente.'}
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-zinc-800 text-zinc-400">
                        <th className="pb-2">ID</th>
                        <th className="pb-2">Nombre</th>
                        <th className="pb-2">Correo</th>
                        <th className="pb-2 text-right">Acción</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-900">
                      {students.map((s) => (
                        <tr key={s.id} className="hover:bg-zinc-900/30">
                          <td className="py-2.5 text-zinc-500 font-mono">{s.id}</td>
                          <td className="py-2.5 font-semibold text-white">{s.name}</td>
                          <td className="py-2.5 text-zinc-400">{s.email}</td>
                          <td className="py-2.5 text-right">
{accountRole!=='ayudante'&&<><button className="text-indigo-300 text-xs mr-3" onClick={()=>setStudentToEdit(s)}>Editar</button>
                            <button
                              onClick={() => handleDeleteStudent(s.id)}
                              className="text-red-400 hover:text-red-300 p-1"
                              title="Retirar estudiante"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button></>}
{accountRole==='ayudante'&&<span className="ie-muted">Solo lectura</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 3: EVALUATIONS & PARAMETERS */}
        {/* ========================================================= */}
        {activeTab === "evaluations" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Create Evaluation Form */}
            <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-zinc-800 bg-zinc-950/40 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Sliders className="h-4 w-4 text-indigo-400" /> {creatingEval?"Nueva evaluación":"Parámetros de la evaluación seleccionada"}
              </h3>
              <p className="text-xs text-zinc-400">
                Define la pauta de corrección y el rigor del análisis. La IA evaluará los trabajos basándose en estas directrices.
              </p>

              <form onSubmit={handleCreateEvaluation} className="space-y-4 text-xs">
                <div>
                  <label className="font-bold text-zinc-300 block mb-1">Título de la Evaluación</label>
                  <input
                    type="text"
                    required
                    placeholder="ej. Informe Final de Investigación Interdisciplinaria"
                    value={newEvalTitle}
                    onChange={(e) => setNewEvalTitle(e.target.value)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-900 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="font-bold text-zinc-300 block mb-1">
                    Prompt / Pauta de Corrección para la IA
                  </label>
                  <textarea
                    rows={4}
                    placeholder="Describe los criterios de evaluación: metodología, conclusiones, profundidad técnica, uso de fuentes..."
                    data-tour="rubric" value={newEvalRubric}
                    onChange={(e) => setNewEvalRubric(e.target.value)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-900 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="font-bold text-zinc-300 block mb-1">Rigor de Preguntas</label>
                    <select
                      value={newEvalRigor}
                      onChange={(e) => setNewEvalRigor(e.target.value)}
                      className="w-full rounded-xl border border-zinc-800 bg-zinc-900 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                    >
                      <option value="high">Estricto (Detalles y citas exactas)</option>
                      <option value="medium">Medio (Conceptos y metodología)</option>
                      <option value="low">Laxo (Comprensión general)</option>
                    </select>
                  </div>

                  <div>
                    <label className="font-bold text-zinc-300 block mb-1">Pool Total de Preguntas</label>
                    <input
                      type="number"
                      data-tour="question-settings" value={newEvalPoolSize}
                      onChange={(e) => setNewEvalPoolSize(Number(e.target.value))}
                      className="w-full rounded-xl border border-zinc-800 bg-zinc-900 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="font-bold text-zinc-300 block mb-1">Preguntas para el Flash Test</label>
                    <input
                      type="number"
                      value={newEvalFlashCount}
                      onChange={(e) => setNewEvalFlashCount(Number(e.target.value))}
                      className="w-full rounded-xl border border-zinc-800 bg-zinc-900 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                  <div>
                    <label className="font-bold text-zinc-300 block mb-1">Tiempo por Pregunta (seg)</label>
                    <input
                      type="number"
                      value={newEvalTime}
                      onChange={(e) => setNewEvalTime(Number(e.target.value))}
                      className="w-full rounded-xl border border-zinc-800 bg-zinc-900 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="font-bold text-zinc-300 block mb-1">Coherencia mínima (0–1)</label>
                    <input
                      type="number"
                      min="0" max="1"
                      step="0.05"
                      value={newEvalLowThresh}
                      onChange={(e) => setNewEvalLowThresh(Number(e.target.value))}
                      className="w-full rounded-xl border border-zinc-800 bg-zinc-900 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="font-bold text-zinc-300 block mb-1">Umbral de alerta IA (0–1)</label>
                    <input
                      type="number"
                      min="0" max="1"
                      step="0.05"
                      value={newEvalHighThresh}
                      onChange={(e) => setNewEvalHighThresh(Number(e.target.value))}
                      className="w-full rounded-xl border border-zinc-800 bg-zinc-900 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                    />
                  </div>


                </div>

                <button
                  type="submit"
                  className="w-full rounded-xl bg-indigo-600 hover:bg-indigo-500 py-3 text-xs font-bold text-white transition-colors"
                >
                  {creatingEval?"Crear evaluación":"Guardar evaluación"}
                </button>
              </form>
            </div>

            {/* List of existing evaluations */}
            <div className="glass-panel p-5 rounded-2xl border border-zinc-800 bg-zinc-950/40 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <FileText className="h-4 w-4 text-indigo-400" /> Evaluaciones de la asignatura
              </h3>
              <button className="ie-button ie-primary" onClick={()=>{setCreatingEval(true);setNewEvalTitle('');setNewEvalRubric('');}}>Nueva evaluación</button>
              {creatingEval&&<button className="ie-button" onClick={()=>{setCreatingEval(false);if(selectedEval){setNewEvalTitle(selectedEval.title);setNewEvalRubric(selectedEval.prompt_rubric);}}}>Cancelar creación</button>}
              <div className="space-y-3">
                {courseEvals.map((ev) => (
                  <div
                    key={ev.id}
                    onClick={() => setSelectedEvalId(ev.id)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                      selectedEvalId === ev.id
                        ? "border-indigo-500 bg-indigo-950/30 ring-1 ring-indigo-500"
                        : "border-zinc-800 bg-zinc-900/40 hover:border-zinc-700"
                    }`}
                  >
                    <h4 className="font-bold text-xs text-white">{ev.title}</h4>
                    <div className="mt-2 flex flex-wrap gap-2 text-[10px] text-zinc-400">
                      <span className="bg-zinc-800 px-2 py-0.5 rounded">Rigor: {ev.question_rigor}</span>
                      <span className="bg-zinc-800 px-2 py-0.5 rounded">Pool: {ev.pool_size}</span>
                      <span className="bg-zinc-800 px-2 py-0.5 rounded">Flash: {ev.flash_questions_count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 4: COURSE MATERIALS */}
        {/* ========================================================= */}
        {activeTab === "materials" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-panel p-5 rounded-2xl border border-zinc-800 bg-zinc-950/40 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Upload className="h-4 w-4 text-indigo-400" /> Subir Material del Curso
              </h3>
              <p className="text-xs text-zinc-400">
                Sube syllabus, guías o bibliografía en PDF, Markdown o TXT. La IA los convertirá a Markdown y los usará como base de conocimiento para evaluar con justicia y precisión.
              </p>

              <form data-tour="material-upload" onSubmit={handleUploadMaterial} className="space-y-3">
                <input
                  type="text"
                  required
                  placeholder="Título, ej. Guía de Metodología y Rúbrica"
                  value={newMaterialTitle}
                  onChange={(e) => setNewMaterialTitle(e.target.value)}
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-900/80 p-2.5 text-xs text-white focus:border-indigo-500 focus:outline-none"
                />
                <input
                  type="file"
                  accept=".pdf,.md,.txt,.markdown"
                  required
                  onChange={(e) => setNewMaterialFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-zinc-400 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
                />
                <button
                  type="submit"
                  disabled={uploadingMaterial}
                  className="w-full rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 py-2.5 text-xs font-bold text-white transition-colors"
                >
                  {uploadingMaterial ? "Procesando PDF a Markdown..." : "Subir y Analizar Material"}
                </button>
              </form>
            </div>

            <div className="md:col-span-2 glass-panel p-5 rounded-2xl border border-zinc-800 bg-zinc-950/40 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-indigo-400" /> Materiales de Apoyo Activos ({materials.length})
              </h3>
              {materials.length === 0 ? (
                <p className="text-xs text-zinc-500 italic py-8 text-center">
                  No has subido documentos de apoyo para esta evaluación.
                </p>
              ) : (
                <div className="space-y-3">
                  {materials.map((m) => (
                    <div
                      key={m.id}
                      className="p-3.5 rounded-xl border border-zinc-800 bg-zinc-900/30 flex justify-between items-center text-xs"
                    >
                      <div>
                        <h4 className="font-bold text-white">{m.title}</h4>
                        <p className="text-[10px] text-zinc-500 mt-0.5">
                          Subido el {new Date(m.uploaded_at).toLocaleDateString("es-CL")}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDeleteMaterial(m.id)}
                        className="text-red-400 hover:text-red-300 p-1.5"
                        title="Eliminar material"
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

        {/* ========================================================= */}
        {/* TAB 5: REPORTS & BULK UPLOAD & AI ANALYSIS */}
        {/* ========================================================= */}
        {activeTab === "reports" && (
          <div className="space-y-6">
            {/* Bulk Upload Dropzone & Mapping */}
            <div className="glass-panel p-6 rounded-2xl border border-zinc-800 bg-zinc-950/40 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <FileUp className="h-4 w-4 text-indigo-400" /> Subida en Lote de Trabajos de Estudiantes
              </h3>
              <p className="text-xs text-zinc-400">
                Selecciona todos los PDFs descargados de la plataforma de la universidad. El sistema detectará automáticamente el estudiante correspondiente o puedes mapearlo manualmente.
              </p>

              <div className="flex flex-col sm:flex-row items-center gap-4">
                <input
                  type="file"
                  multiple
                  accept=".pdf,.md,.txt,.markdown"
                  data-tour="report-upload" onChange={(e) => handleBulkFilesSelect(e.target.files)}
                  className="w-full sm:w-auto text-xs text-zinc-400 file:mr-3 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
                />
                {bulkFiles.length > 0 && (
                  <button
                    onClick={handleExecuteBulkUpload}
                    disabled={bulkUploading}
                    className="w-full sm:w-auto rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 px-6 py-2.5 text-xs font-bold text-white transition-colors"
                  >
                    {bulkUploading ? "Analizando Trabajos con IA..." : `Procesar ${bulkFiles.length} Trabajos`}
                  </button>
                )}
              </div>

              {/* Mapping files to students */}
              {bulkFiles.length > 0 && (
                <div className="mt-4 border-t border-zinc-800 pt-4 space-y-2 max-h-60 overflow-y-auto">
                  <h4 className="text-xs font-bold text-zinc-300">Asociación de Archivos:</h4>
                  {bulkFiles.map((file) => (
                    <div
                      key={file.name}
                      className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 p-2 rounded-lg bg-zinc-900 text-xs"
                    >
                      <span className="font-mono text-zinc-300 truncate max-w-sm">{file.name}</span>
                      <select
                        value={bulkMapping[file.name] || ""}
                        onChange={(e) =>
                          setBulkMapping((prev) => ({
                            ...prev,
                            [file.name]: Number(e.target.value),
                          }))
                        }
                        className="rounded-lg border border-zinc-800 bg-zinc-950 p-1.5 text-xs text-white focus:border-indigo-500"
                      >
                        <option value="">-- Seleccionar Estudiante --</option>
                        {students.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.name} ({s.email})
                          </option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {selectedCourseId&&selectedEvalId&&<UploadQueue courseId={selectedCourseId} evaluationId={selectedEvalId} onCompleted={()=>loadEvalSubData(selectedEvalId)}/>}
            {/* Reports Table & Analysis Status */}
            <details key={selectedEvalId} className="glass-panel p-6 rounded-2xl border border-zinc-800 bg-zinc-950/40 space-y-4">
                <summary className="text-sm font-bold text-white uppercase tracking-wider cursor-pointer">
                  Análisis IA · {selectedEval?.title} ({reports.length} trabajos)
                </summary>
                <button
                  onClick={() => selectedEvalId && loadEvalSubData(selectedEvalId)}
                  className="flex items-center gap-1 text-xs text-zinc-400 hover:text-white"
                >
                  <RefreshCw className="h-3.5 w-3.5" /> Actualizar
                </button>

              {reports.length === 0 ? (
                <p className="text-xs text-zinc-500 italic py-8 text-center">
                  No hay trabajos subidos para esta evaluación.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-zinc-800 text-zinc-400">
                        <th className="pb-3">Estudiante</th>
                        <th className="pb-3">Estado Análisis</th>
                        <th className="pb-3">Nota Preliminar IA</th>
                        <th className="pb-3">Detección IA</th>
                        <th className="pb-3">Flash Test</th>
                        <th className="pb-3 text-right">Acciones</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-900">
                      {reports.map((r) => {
                        const statusBadges: Record<string, React.ReactNode> = {
                          pending: <span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-400">Pendiente</span>,
                          processing: <span className="px-2 py-0.5 rounded bg-yellow-950/60 text-yellow-400 animate-pulse">Analizando...</span>,
                          completed: <span className="px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400">Completado</span>,
                          error: <span className="px-2 py-0.5 rounded bg-red-950/60 text-red-400">Error</span>,
                        };
                        const statusBadge = statusBadges[r.analysis_status] || null;

                        const aiPct = r.ai_detected_percentage != null ? Math.round(r.ai_detected_percentage * 100) : null;
                        const scorePct = r.final_score_percentage != null ? Math.round(r.final_score_percentage * 100) : (r.ai_score_percentage != null ? Math.round(r.ai_score_percentage * 100) : null);

                        return (
                          <tr key={r.id} className="hover:bg-zinc-900/30">
                            <td className="py-3">
                              <div className="font-bold text-white">{r.student_name}</div>
                              <div className="text-[10px] text-zinc-500">{r.student_email}</div>
                            </td>
                            <td className="py-3">{statusBadge}<p className="text-xs text-zinc-400">{r.analysis_engine}{r.analysis_fallback?' · respaldo simulado':''}</p></td>
                            <td className="py-3 font-semibold text-white">
                              {scorePct != null ? `${scorePct}%` : "--"}
                            </td>
                            <td className="py-3">
                              {aiPct != null ? (
                                <span className={aiPct > 40 ? "text-red-400 font-bold" : "text-zinc-300"}>
                                  {aiPct}% {aiPct > 40 && "⚠️"}
                                </span>
                              ) : "--"}
                            </td>
                            <td className="py-3">
                              {r.flash_completed ? (
                                <span className="text-emerald-400 font-bold">Rendido</span>
                              ) : r.flash_email_sent ? (
                                <span className="text-indigo-400">Correo Enviado</span>
                              ) : (
                                <span className="text-zinc-500">No enviado</span>
                              )}
                            </td>
                            <td className="py-3 text-right space-x-2">
                              <button
                                onClick={() => handlePreviewMarkdown(r.id)}
                                className="text-zinc-400 hover:text-white p-1"
                                title="Ver Markdown extraído"
                              >
                                <Eye className="h-4 w-4 inline" />
                              </button>
                              <button
                                onClick={() => handleOpenQuestions(r)}
                                className="px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-[11px] font-bold text-white inline-flex items-center gap-1"
                              >
                                <HelpCircle className="h-3 w-3" /> Pool Preguntas
                              </button>
                              <button
                                onClick={() => handleReanalyze(r.id)}
                                className="text-zinc-400 hover:text-white p-1"
                                title="Reanalizar con IA"
                              >
                                <RefreshCw className="h-4 w-4 inline" />
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </details>
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 6: QUESTION POOL MANAGEMENT */}
        {/* ========================================================= */}
        {activeTab === "questions" && (
          <div className="space-y-6">
            <div className="glass-panel p-6 rounded-2xl border border-zinc-800 bg-zinc-950/40 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div>
                <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                  Estudiante: {selectedReport?.student_name}
                </span>
                <h2 data-tour="questions-pool" className="text-lg font-bold text-white mt-0.5">
                  Pool de Preguntas Flash ({questionBank?.questions?.length || 0} disponibles)
                </h2>
                <p className="text-xs text-zinc-400">
                  Selecciona las {selectedEval?.flash_questions_count || 10} preguntas que se enviarán al estudiante por correo. Puedes editarlas o agregar preguntas propias.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={handleSelectRandom}
                  className="px-3 py-2 rounded-xl border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-xs font-semibold text-zinc-200 flex items-center gap-1.5"
                >
                  <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                  Selección Aleatoria ({selectedEval?.flash_questions_count || 10})
                </button>
                <button
                  onClick={() => setShowAddQModal(true)}
                  className="px-3 py-2 rounded-xl border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-xs font-semibold text-zinc-200 flex items-center gap-1.5"
                >
                  <Plus className="h-3.5 w-3.5" />
                  Agregar Pregunta Propia
                </button>
                <button
                  data-tour="flash-dispatch" onClick={handleSendFlashTest}
                  disabled={selectedQIds.length === 0}
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-xs font-bold text-white shadow-lg flex items-center gap-1.5"
                >
                  <Mail className="h-3.5 w-3.5" />
                  Aprobar y Enviar Flash Test ({selectedQIds.length})
                </button>
              </div>
            </div>

            {/* Questions List */}
            {!questionBank || questionBank.questions.length === 0 ? (
              <div className="glass-panel p-8 text-center text-xs text-zinc-500 rounded-2xl border border-zinc-800">
                El banco de preguntas aún no ha sido generado para este informe. Espera que termine el análisis.
              </div>
            ) : (
              <div className="space-y-3">
                {questionBank.questions.map((q: any, idx: number) => {
                  const isSelected = selectedQIds.includes(q.id);
                  return (
                    <div
                      key={q.id}
                      className={`p-4 rounded-xl border transition-all ${
                        isSelected
                          ? "border-indigo-500 bg-indigo-950/20"
                          : "border-zinc-800 bg-zinc-950/40"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-start gap-3">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => handleToggleSelectQuestion(q.id)}
                            className="mt-1 h-4 w-4 rounded border-zinc-700 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                          />
                          <div>
                            <span className="text-[10px] font-bold text-zinc-500 uppercase mr-2">
                              #{idx + 1} {q.is_custom && "• Creada por Profesor"}
                            </span>
                            <p className="text-sm font-semibold text-white mt-0.5">{q.text}</p>

                            {/* Options */}
                            {q.options && (
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3">
                                {q.options.map((opt: string, oIdx: number) => {
                                  const isCorrect = String(oIdx) === String(q.correct_answer);
                                  return (
                                    <div
                                      key={oIdx}
                                      className={`p-2 rounded-lg text-xs flex items-center justify-between ${
                                        isCorrect
                                          ? "bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 font-semibold"
                                          : "bg-zinc-900/60 border border-zinc-800/80 text-zinc-400"
                                      }`}
                                    >
                                      <span>
                                        {String.fromCharCode(65 + oIdx)}. {opt}
                                      </span>
                                      {isCorrect && <Check className="h-3.5 w-3.5 text-emerald-400" />}
                                    </div>
                                  );
                                })}
                              </div>
                            )}
                          </div>
                        </div>

                        <button className="text-indigo-300 p-1" title="Editar pregunta" onClick={()=>handleEditQuestion(q)}><Edit className="h-4 w-4"/></button>
                        <button
                          onClick={() => handleDeleteQuestion(q.id)}
                          className="text-zinc-500 hover:text-red-400 p-1"
                          title="Eliminar del pool"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 7: RESULTS & REVIEW LIST */}
        {/* ========================================================= */}
        {activeTab === "results" && (
          <div className="space-y-6">
            {/* Stats Overview */}
            {evalStats && (
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <div className="glass-panel p-4 rounded-xl border border-zinc-800 bg-zinc-950/40">
                  <span className="text-[10px] font-bold text-zinc-500 uppercase">Promedio IA</span>
                  <p className="text-2xl font-bold text-white mt-1">
                    {evalStats.avg_ai_score != null ? `${Math.round(evalStats.avg_ai_score * 100)}%` : "--"}
                  </p>
                </div>
                <div className="glass-panel p-4 rounded-xl border border-zinc-800 bg-zinc-950/40">
                  <span className="text-[10px] font-bold text-zinc-500 uppercase">Flash Tests Rendidos</span>
                  <p className="text-2xl font-bold text-white mt-1">
                    {evalStats.flash_test?.completed || 0}
                  </p>
                </div>
                <div className="glass-panel p-4 rounded-xl border border-zinc-800 bg-zinc-950/40">
                  <span className="text-[10px] font-bold text-zinc-500 uppercase">Convocados a Oficina</span>
                  <p className="text-2xl font-bold text-yellow-400 mt-1">
                    {reviewList.length}
                  </p>
                </div>
                <div className="glass-panel p-4 rounded-xl border border-zinc-800 bg-zinc-950/40">
                  <span className="text-[10px] font-bold text-zinc-500 uppercase">Citas Pendientes</span>
                  <p className="text-2xl font-bold text-indigo-400 mt-1">
                    {evalStats.appointments?.pending || 0}
                  </p>
                </div>
              </div>
            )}

            {/* Flagged Students for Office Review */}
            <div className="glass-panel p-6 rounded-2xl border border-yellow-500/30 bg-yellow-950/10 space-y-4">
              <h3 className="text-sm font-bold text-yellow-300 uppercase tracking-wider flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-400" /> Lista de Convocatoria a Oficina ({reviewList.length})
              </h3>
              <p className="text-xs text-zinc-400">
                Alumnos que requieren revisión por sus indicadores de análisis o Flash Test. Elige la fecha y el horario de cada cita; no se agenda automáticamente.
              </p>

              {reviewList.length === 0 ? (
                <p className="text-xs text-zinc-500 italic py-4">No hay estudiantes convocados a oficina por ahora.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-zinc-800 text-zinc-400">
                        <th className="pb-2">Estudiante</th>
                        <th className="pb-2">Motivo</th>
                        <th className="pb-2">Nota IA</th>
                        <th className="pb-2">Flash Score</th>
                        <th className="pb-2">Cita</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-900">
                      {reviewList.map((item, i) => (
                        <tr key={i} className="hover:bg-zinc-900/30">
                          <td className="py-2.5 font-bold text-white">{item.student_name}<br/><button className="text-indigo-300 text-xs" onClick={()=>scheduleDefense(item.student_id)}>Agendar defensa</button></td>
                          <td className="py-2.5">
                            <span className="px-2 py-0.5 rounded bg-yellow-950 text-yellow-300 font-mono text-[10px]">
                              {item.review_reason}
                            </span>
                          </td>
                          <td className="py-2.5 text-zinc-300">
                            {item.ai_score != null ? `${Math.round(item.ai_score * 100)}%` : "--"}
                          </td>
                          <td className="py-2.5 text-zinc-300">
                            {item.flash_score != null ? `${Math.round(item.flash_score * 100)}%` : "--"}
                          </td>
                          <td className="py-2.5 text-indigo-400 font-semibold">
                            {item.appointment_time
                              ? new Date(item.appointment_time).toLocaleString("es-CL", {
                                  day: "2-digit",
                                  month: "short",
                                  hour: "2-digit",
                                  minute: "2-digit",
                                })
                              : "Agendando..."}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Complete Students Results Table with Score Adjustments */}
            <div className="glass-panel p-6 rounded-2xl border border-zinc-800 bg-zinc-950/40 space-y-4">
              <h3 data-tour="results" className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Users className="h-4 w-4 text-indigo-400" /> Calificaciones Finales y Ajustes
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-zinc-800 text-zinc-400">
                      <th className="pb-3">Estudiante</th>
                      <th className="pb-3">Nota Preliminar IA</th>
                      <th className="pb-3">Flash Test</th>
                      <th className="pb-3">Calificación Final</th>
                      <th className="pb-3 text-right">Ajuste Manual</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-900">
                    {evalStats?.students?.map((st: any) => (
                      <tr key={st.student_id} className="hover:bg-zinc-900/30">
                        <td className="py-3 font-semibold text-white">{st.student_name}</td>
                        <td className="py-3 text-zinc-300">
                          {st.ai_score != null ? `${Math.round(st.ai_score * 100)}%` : "--"}
                        </td>
                        <td className="py-3">
                          {st.flash_score != null ? (
                            <span className="font-bold text-indigo-300">{Math.round(st.flash_score * 100)}%</span>
                          ) : (
                            <span className="text-zinc-600">Pendiente</span>
                          )}
                        </td>
                        <td className="py-3 font-bold text-emerald-400 text-sm">
                          {st.final_score != null ? `${Math.round(st.final_score * 100)}%` : (st.ai_score != null ? `${Math.round(st.ai_score * 100)}%` : "--")}
                        </td>
                        <td className="py-3 text-right">
                          <div className="inline-flex items-center gap-1.5">
                            <input
                              type="number"
                              step="0.01"
                              placeholder="0.0-1.0"
                              value={scoreOverrides[st.student_id] || ""}
                              onChange={(e) => setScoreOverrides(previous=>({...previous,[st.student_id]:e.target.value}))}
                              className="w-16 rounded border border-zinc-800 bg-zinc-900 p-1 text-[11px] text-white"
                            />
                            <button
                              onClick={() => {
                                const rep = reports.find((r) => r.student_id === st.student_id);
                                if (rep) handleScoreOverride(rep.id);
                              }}
                              className="px-2 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-[10px] font-bold text-white"
                            >
                              Guardar
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 8: APPOINTMENTS FEEDBACK */}
        {/* ========================================================= */}
        {activeTab === "appointments" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Appointments List */}
            <div className="md:col-span-2 glass-panel p-6 rounded-2xl border border-zinc-800 bg-zinc-950/40 space-y-4">
              <h3 data-tour="appointments" className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Calendar className="h-4 w-4 text-indigo-400" /> Citas de revisión ({appointments.filter(a=>a.course_id===selectedCourseId&&((a.actividad_id||null)===(selectedEvalId&&selectedEvalId<0?-selectedEvalId:null))).length})
              </h3>

              <button className="ie-button ie-primary" disabled={!students.length} onClick={()=>setAppointmentDraft({})}>Agendar revisión</button>
              {appointments.filter(a=>a.course_id===selectedCourseId&&((a.actividad_id||null)===(selectedEvalId&&selectedEvalId<0?-selectedEvalId:null))).length === 0 ? (
                <p className="text-xs text-zinc-500 italic py-8 text-center">
                  No hay citas de oficina agendadas actualmente.
                </p>
              ) : (
                <div className="space-y-3">
                  {appointments.filter(a=>a.course_id===selectedCourseId&&((a.actividad_id||null)===(selectedEvalId&&selectedEvalId<0?-selectedEvalId:null))).map((appt) => (
                    <div
                      key={appt.id}
                      onClick={() => {setSelectedAppt(appt);setApptStatus(appt.status==='cancelled'?'cancelled':'completed');setApptNotes(appt.notes||'');setApptAdjustedScore('');}}
                      className={`p-4 rounded-xl border cursor-pointer transition-all ${
                        selectedAppt?.id === appt.id
                          ? "border-indigo-500 bg-indigo-950/30 ring-1 ring-indigo-500"
                          : "border-zinc-800 bg-zinc-900/40 hover:border-zinc-700"
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-bold text-sm text-white">{appt.student_name}</h4>
                          <p className="text-xs text-zinc-400">{appt.evaluation_title}</p>
                        </div>
                        <span
                          className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                            appt.status === "pending"
                              ? "bg-yellow-950 text-yellow-300"
                              : "bg-emerald-950 text-emerald-300"
                          }`}
                        >
                          {appt.status === "pending" ? "Pendiente" : "Completada"}
                        </span>
                      </div>
                      <div className="mt-2 text-xs text-zinc-400 flex items-center gap-2">
                        <Clock className="h-3.5 w-3.5 text-indigo-400" />
                        {new Date(appt.scheduled_time).toLocaleString("es-CL", {
                          weekday: "long",
                          day: "2-digit",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </div>
                      <button className="ie-button" onClick={e=>{e.stopPropagation();setAppointmentDraft(appt);}}>Cambiar fecha y hora</button>
                      {appt.notes && <p className="text-[11px] text-zinc-500 mt-2 italic">{appt.notes}</p>}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Complete Meeting / Feedback Form */}
            <div className="glass-panel p-6 rounded-2xl border border-zinc-800 bg-zinc-950/40 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Edit className="h-4 w-4 text-indigo-400" /> Registrar Resultado de Cita
              </h3>
              {selectedAppt ? (
                <form onSubmit={handleSubmitApptFeedback} className="space-y-4 text-xs">
                  <div>
                    <span className="text-[10px] text-zinc-500 block">Estudiante</span>
                    <p className="font-bold text-white text-sm">{selectedAppt.student_name}</p>
                  </div>

                  <div>
                    <label className="font-bold text-zinc-300 block mb-1">Estado de la Cita</label>
                    <select
                      value={apptStatus}
                      onChange={(e) => setApptStatus(e.target.value)}
                      className="w-full rounded-xl border border-zinc-800 bg-zinc-900 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                    >
                      <option value="completed">Completada (Reunión realizada)</option>
                      <option value="cancelled">Cancelada / No asistió</option>
                    </select>
                  </div>

                  <div>
                    <label className="font-bold text-zinc-300 block mb-1">
                      Ajustar Calificación Final (0.0 a 1.0)
                    </label>
                    <input
                      type="number"
                      min="0" max="1"
                      step="0.05"
                      placeholder="ej. 0.90 (90%) si justificó bien"
                      value={apptAdjustedScore}
                      onChange={(e) => setApptAdjustedScore(e.target.value)}
                      className="w-full rounded-xl border border-zinc-800 bg-zinc-900 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="font-bold text-zinc-300 block mb-1">Notas / Justificación</label>
                    <textarea
                      rows={3}
                      placeholder="El estudiante explicó detalladamente la metodología y resolvió las dudas..."
                      value={apptNotes}
                      onChange={(e) => setApptNotes(e.target.value)}
                      className="w-full rounded-xl border border-zinc-800 bg-zinc-900 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full rounded-xl bg-indigo-600 hover:bg-indigo-500 py-3 text-xs font-bold text-white transition-colors"
                  >
                    Guardar y Cerrar Cita
                  </button>
                </form>
              ) : (
                <p className="text-xs text-zinc-500 italic py-8 text-center">
                  Selecciona una cita de la lista para registrar el resultado y modificar la calificación.
                </p>
              )}
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 9: TEACHER AVAILABILITY */}
        {/* ========================================================= */}
        {activeTab === "availability" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-panel p-5 rounded-2xl border border-zinc-800 bg-zinc-950/40 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Clock className="h-4 w-4 text-indigo-400" /> Agregar Bloque Horario
              </h3>
              <p className="text-xs text-zinc-400">
                El sistema usará estos bloques semanales para agendar automáticamente las defensas de los alumnos convocados.
              </p>

              <form onSubmit={handleAddAvailability} className="space-y-3 text-xs">
                <div>
                  <label className="font-bold text-zinc-300 block mb-1">Día de la Semana</label>
                  <select
                    value={newAvailDay}
                    onChange={(e) => setNewAvailDay(Number(e.target.value))}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-900 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value={0}>Lunes</option>
                    <option value={1}>Martes</option>
                    <option value={2}>Miércoles</option>
                    <option value={3}>Jueves</option>
                    <option value={4}>Viernes</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="font-bold text-zinc-300 block mb-1">Inicio (HH:MM)</label>
                    <input
                      type="time"
                      value={newAvailStart}
                      onChange={(e) => setNewAvailStart(e.target.value)}
                      className="w-full rounded-xl border border-zinc-800 bg-zinc-900 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="font-bold text-zinc-300 block mb-1">Fin (HH:MM)</label>
                    <input
                      type="time"
                      value={newAvailEnd}
                      onChange={(e) => setNewAvailEnd(e.target.value)}
                      className="w-full rounded-xl border border-zinc-800 bg-zinc-900 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  className="w-full rounded-xl bg-indigo-600 hover:bg-indigo-500 py-2.5 text-xs font-bold text-white transition-colors"
                >
                  Agregar Horario
                </button>
              </form>
            </div>

            <div className="md:col-span-2 glass-panel p-5 rounded-2xl border border-zinc-800 bg-zinc-950/40 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Calendar className="h-4 w-4 text-indigo-400" /> Mis Horarios de Atención Semanales ({availabilities.length})
              </h3>

              {availabilities.length === 0 ? (
                <p className="text-xs text-zinc-500 italic py-8 text-center">
                  No has registrado horarios. Puedes elegir la fecha y hora al agendar cada cita.
                </p>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {availabilities.map((av) => (
                    <div
                      key={av.id}
                      className="p-3.5 rounded-xl border border-zinc-800 bg-zinc-900/40 flex justify-between items-center text-xs"
                    >
                      <div>
                        <span className="font-bold text-white text-sm">{getDayName(av.day_of_week)}</span>
                        <p className="text-zinc-400 font-mono mt-0.5">
                          {av.start_time} - {av.end_time} hrs
                        </p>
                      </div>
                      <button
                        onClick={() => handleDeleteAvailability(av.id)}
                        className="text-red-400 hover:text-red-300 p-1.5"
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
      </main>

      {/* ========================================================= */}
      {/* MODAL: Add Custom Question */}
      {/* ========================================================= */}
      {showAddQModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 max-w-lg w-full space-y-4 text-xs">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-bold text-white">Agregar Pregunta Personalizada al Pool</h3>
              <button onClick={() => setShowAddQModal(false)} className="text-zinc-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleCreateCustomQuestion} className="space-y-3">
              <div>
                <label className="font-bold text-zinc-300 block mb-1">Enunciado de la Pregunta</label>
                <textarea
                  rows={2}
                  required
                  placeholder="¿Cuál fue el resultado obtenido en la sección 3.2?"
                  value={newQText}
                  onChange={(e) => setNewQText(e.target.value)}
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-950 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="font-bold text-zinc-300 block mb-1">Tipo de Pregunta</label>
                <select
                  value={newQType}
                  onChange={(e) => setNewQType(e.target.value as any)}
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-950 p-2.5 text-white focus:border-indigo-500 focus:outline-none"
                >
                  <option value="multiple_choice">Selección Múltiple (4 alternativas)</option>
                  <option value="true_false">Verdadero / Falso</option>
                </select>
              </div>

              {newQType === "multiple_choice" && (
                <div className="space-y-2">
                  <label className="font-bold text-zinc-300 block">Alternativas y Respuesta Correcta</label>
                  {newQOptions.map((opt, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="font-bold text-zinc-500">{String.fromCharCode(65 + i)})</span>
                      <input
                        type="text"
                        required
                        placeholder={`Opción ${String.fromCharCode(65 + i)}`}
                        value={opt}
                        onChange={(e) => {
                          const arr = [...newQOptions];
                          arr[i] = e.target.value;
                          setNewQOptions(arr);
                        }}
                        className="flex-1 rounded-lg border border-zinc-800 bg-zinc-950 p-2 text-white focus:border-indigo-500 focus:outline-none"
                      />
                      <input
                        type="radio"
                        name="correct-ans"
                        checked={newQCorrect === String(i)}
                        onChange={() => setNewQCorrect(String(i))}
                        className="h-4 w-4 text-indigo-600"
                        title="Marcar como correcta"
                      />
                    </div>
                  ))}
                </div>
              )}

              {newQType === "true_false" && (
                <div className="flex gap-4">
                  <label className="flex items-center gap-2 text-white">
                    <input
                      type="radio"
                      name="correct-tf"
                      checked={newQCorrect === "0"}
                      onChange={() => setNewQCorrect("0")}
                    />
                    Verdadero es la correcta
                  </label>
                  <label className="flex items-center gap-2 text-white">
                    <input
                      type="radio"
                      name="correct-tf"
                      checked={newQCorrect === "1"}
                      onChange={() => setNewQCorrect("1")}
                    />
                    Falso es la correcta
                  </label>
                </div>
              )}

              <button
                type="submit"
                className="w-full rounded-xl bg-indigo-600 hover:bg-indigo-500 py-2.5 font-bold text-white transition-colors"
              >
                Guardar Pregunta
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* MODAL: Preview Markdown of Student Report */}
      {/* ========================================================= */}
      {previewMdModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 max-w-3xl w-full max-h-[85vh] flex flex-col space-y-4 text-xs">
            <div className="flex justify-between items-center border-b border-zinc-800 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <FileText className="h-4 w-4 text-indigo-400" /> Vista Previa del Trabajo Convertido a Markdown
              </h3>
              <button onClick={() => setPreviewMdModal(false)} className="text-zinc-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto bg-zinc-950 p-4 rounded-xl font-mono text-zinc-300 whitespace-pre-wrap leading-relaxed">
              {reportMarkdown}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { api, getToken, getRole, getTeacherContext, request } from "@/lib/api";
import { TAB_IDS, type TabId } from "./types";

export type EvalForm = {
  title: string;
  rubric: string;
  rigor: string;
  poolSize: number;
  flashCount: number;
  time: number;
  lowThresh: number;
  highThresh: number;
  randomPct: number;
};

export const EMPTY_EVAL_FORM: EvalForm = {
  title: "",
  rubric: "",
  rigor: "medium",
  poolSize: 20,
  flashCount: 10,
  time: 30,
  lowThresh: 0.6,
  highThresh: 0.4,
  randomPct: 0.1,
};

function useDashboardState() {
  const router = useRouter();
  const courseLoad = useRef(0);
  const evalLoad = useRef(0);

  const [loading, setLoading] = useState(true);
  const [accountRole, setAccountRole] = useState("");
  const [adminTeacher, setAdminTeacher] = useState<any>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [flashLink, setFlashLink] = useState("");

  const [activeTab, changeActiveTab] = useState<TabId>("courses");

  const [courses, setCourses] = useState<any[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [selectedCourse, setSelectedCourse] = useState<any | null>(null);
  const [courseEvals, setCourseEvals] = useState<any[]>([]);
  const [selectedEvalId, setSelectedEvalId] = useState<number | null>(null);
  const [selectedEval, setSelectedEval] = useState<any | null>(null);

  const [students, setStudents] = useState<any[]>([]);
  const [materials, setMaterials] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [evalStats, setEvalStats] = useState<any | null>(null);
  const [reviewList, setReviewList] = useState<any[]>([]);
  const [appointments, setAppointments] = useState<any[]>([]);
  const [availabilities, setAvailabilities] = useState<any[]>([]);

  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [selectedReport, setSelectedReport] = useState<any | null>(null);
  const [questionBank, setQuestionBank] = useState<any | null>(null);
  const [selectedQIds, setSelectedQIds] = useState<number[]>([]);

  const [creatingEval, setCreatingEval] = useState(false);
  const [evalForm, setEvalForm] = useState<EvalForm>(EMPTY_EVAL_FORM);

  const [appointmentDraft, setAppointmentDraft] = useState<any>(null);
  const [studentToEdit, setStudentToEdit] = useState<any>(null);

  const openTab = (value: TabId, ids?: { courseId?: number | null; evalId?: number | null }) => {
    const courseId = ids?.courseId !== undefined ? ids.courseId : selectedCourseId;
    const evalId = ids?.evalId !== undefined ? ids.evalId : selectedEvalId;
    const url = new URL(location.href);
    url.searchParams.set("seccion", value);
    if (courseId) url.searchParams.set("curso", String(courseId));
    if (evalId) url.searchParams.set("evaluacion", String(evalId));
    history.pushState(null, "", url);
    changeActiveTab(value);
  };
  const setActiveTab = (value: TabId) => openTab(value);

  const selectCourse = (id: number) => {
    const url = new URL(location.href);
    url.searchParams.set("curso", String(id));
    url.searchParams.delete("evaluacion");
    history.pushState(null, "", url);
    setSelectedCourseId(id);
  };

  const selectEvaluation = (id: number) => {
    const url = new URL(location.href);
    url.searchParams.set("evaluacion", String(id));
    if (selectedCourseId) url.searchParams.set("curso", String(selectedCourseId));
    history.pushState(null, "", url);
    setSelectedEvalId(id);
    setSelectedReportId(null);
    setSelectedReport(null);
    setQuestionBank(null);
    setCreatingEval(false);
  };

  useEffect(() => {
    const restore = () => {
      const q = new URLSearchParams(location.search);
      const section = q.get("seccion");
      if (TAB_IDS.includes(section as TabId)) changeActiveTab(section as TabId);
      else changeActiveTab("courses");
      const c = Number(q.get("curso"));
      if (c) setSelectedCourseId(c);
      const e = Number(q.get("evaluacion"));
      if (e) setSelectedEvalId(e);
    };
    restore();
    window.addEventListener("popstate", restore);
    return () => window.removeEventListener("popstate", restore);
  }, []);

  const loadAppointments = async () => {
    try {
      setAppointments(await api.getAppointments());
    } catch (err) {}
  };

  const loadAvailabilities = async () => {
    try {
      setAvailabilities(await api.getTeacherAvailabilities());
    } catch (err) {}
  };

  const loadEvalSubData = async (eId: number) => {
    const version = ++evalLoad.current;
    try {
      const [mats, reps, stats, rev] = await Promise.all([
        api.getMaterials(eId),
        api.getReports(eId),
        api.getEvaluationStats(eId),
        api.getReviewList(eId),
      ]);
      if (version !== evalLoad.current) return;
      setMaterials(mats);
      setReports(reps);
      setEvalStats(stats);
      setReviewList(rev.review_list || []);
    } catch (err: any) {
      if (version === evalLoad.current) setError(err.message || "No se pudieron cargar los datos");
    }
  };

  const loadCourseSubData = async (cId: number) => {
    const version = ++courseLoad.current;
    ++evalLoad.current;
    setReports([]);
    setEvalStats(null);
    setReviewList([]);
    setSelectedReportId(null);
    setQuestionBank(null);
    try {
      const st = await api.getStudents(cId);
      if (version !== courseLoad.current) return;
      setStudents(st);
      const evs = await api.getCourseEvaluations(cId);
      if (version !== courseLoad.current) return;
      setCourseEvals(evs);
      if (evs.length > 0) {
        const preferred =
          evs.find((e: any) => e.id === Number(new URLSearchParams(location.search).get("evaluacion"))) ||
          evs[0];
        setSelectedEvalId(preferred.id);
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

  const refreshStudents = async () => {
    if (!selectedCourseId) return;
    setStudents(await api.getStudents(selectedCourseId));
  };

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const me = await api.getMe();
      setAccountRole(me.rol);
      if (me.rol === "admin") {
        const id = getTeacherContext();
        if (!id) {
          router.replace("/admin/dashboard");
          return;
        }
        setAdminTeacher(await request(`/admin/profesores/${id}`));
      }
      if (me.rol === "ayudante" && location.pathname.startsWith("/teacher/")) {
        router.replace("/assistant/dashboard");
        return;
      }
      const crs = await api.getCourses();
      setCourses(crs);
      setSelectedCourseId(
        crs.find((c: any) => c.id === Number(new URLSearchParams(location.search).get("curso")))?.id ||
          crs[0]?.id ||
          null,
      );
      setSelectedCourse(crs[0] || null);
      if (!crs.length) {
        setStudents([]);
        setCourseEvals([]);
        setSelectedEvalId(null);
        setSelectedEval(null);
        setReports([]);
        setMaterials([]);
        setEvalStats(null);
        setReviewList([]);
      }
      await loadAppointments();
      await loadAvailabilities();
    } catch (err: any) {
      setError(err.message || "Error al cargar datos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const token = getToken();
    const role = getRole();
    if (!token || !["teacher", "admin", "assistant"].includes(role || "")) {
      router.push("/login");
      return;
    }
    if (role === "admin" && !getTeacherContext()) {
      router.replace("/admin/dashboard");
      return;
    }
    loadInitialData();
  }, [router]);

  useEffect(() => {
    if (!selectedCourseId || !selectedEvalId || !getToken()) return;
    let disposed = false;
    let socket: WebSocket | null = null;
    let retry: ReturnType<typeof setTimeout>;
    const connect = () => {
      socket = new WebSocket(
        `ws://127.0.0.1:8000/ws/panel/${selectedCourseId}?token=${encodeURIComponent(getToken() || "")}`,
      );
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "STUDENT_TEST_FINISHED") {
          loadEvalSubData(selectedEvalId);
          loadAppointments();
        }
      };
      socket.onclose = () => {
        if (!disposed) retry = setTimeout(connect, 3000);
      };
    };
    connect();
    return () => {
      disposed = true;
      clearTimeout(retry);
      socket?.close();
    };
  }, [selectedCourseId, selectedEvalId]);

  useEffect(() => {
    if (selectedCourseId) {
      setSelectedCourse(courses.find((x) => x.id === selectedCourseId) || null);
      loadCourseSubData(selectedCourseId);
    }
  }, [selectedCourseId]);

  useEffect(() => {
    if (selectedEvalId && courseEvals.some((x) => x.id === selectedEvalId)) {
      setReports([]);
      setEvalStats(null);
      setReviewList([]);
      const ev = courseEvals.find((x) => x.id === selectedEvalId);
      setSelectedEval(ev || null);
      if (ev) {
        setEvalForm((form) => ({
          ...form,
          title: ev.title,
          rubric: ev.prompt_rubric,
          rigor: ev.question_rigor,
          poolSize: ev.pool_size,
          flashCount: ev.flash_questions_count,
          time: ev.time_per_question,
          lowThresh: ev.low_threshold,
          highThresh: ev.high_threshold,
        }));
      }
      loadEvalSubData(selectedEvalId);
    }
  }, [selectedEvalId, courseEvals]);

  const openReportQuestions = async (report: any) => {
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

  const scheduleDefense = (studentId: number) => setAppointmentDraft({ estudiante_id: studentId });

  const saveAppointment = async (studentId: number, date: string, block: string) => {
    if (!selectedCourseId) return;
    if (appointmentDraft?.id) await api.rescheduleAppointment(appointmentDraft.id, date, block);
    else
      await api.scheduleAppointment(selectedCourseId, {
        estudiante_id: studentId,
        fecha: date,
        bloque: block,
        actividad_id: selectedEvalId && selectedEvalId < 0 ? -selectedEvalId : null,
      });
    setSuccess("Cita guardada con la fecha elegida.");
    await loadAppointments();
    if (selectedEvalId) await loadEvalSubData(selectedEvalId);
  };

  const activityId = selectedEvalId && selectedEvalId < 0 ? -selectedEvalId : null;

  return {

    loading, accountRole, adminTeacher, error, setError, success, setSuccess, flashLink, setFlashLink,

    activeTab, setActiveTab, openTab, selectCourse, selectEvaluation,

    courses, selectedCourseId, setSelectedCourseId, selectedCourse,
    courseEvals, setCourseEvals, selectedEvalId, setSelectedEvalId, selectedEval, setSelectedEval,
    activityId,

    students, setStudents, materials, setMaterials, reports, evalStats, reviewList,
    appointments, availabilities,

    selectedReportId, selectedReport, questionBank, setQuestionBank, selectedQIds, setSelectedQIds,
    openReportQuestions,

    creatingEval, setCreatingEval, evalForm, setEvalForm,

    appointmentDraft, setAppointmentDraft, studentToEdit, setStudentToEdit,
    scheduleDefense, saveAppointment,

    loadInitialData, loadCourseSubData, loadEvalSubData, loadAppointments, loadAvailabilities,
    refreshStudents,
  };
}

export type DashboardValue = ReturnType<typeof useDashboardState>;

const DashboardContext = createContext<DashboardValue | null>(null);

export function DashboardProvider({ children }: { children: ReactNode }) {
  const value = useDashboardState();
  return <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>;
}

export function useDashboard(): DashboardValue {
  const value = useContext(DashboardContext);
  if (!value) throw new Error("useDashboard debe usarse dentro de <DashboardProvider>");
  return value;
}

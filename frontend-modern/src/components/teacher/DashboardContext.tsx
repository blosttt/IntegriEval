"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
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
  low: number;
  high: number;
  randomPct: number;
};

const initialEvalForm: EvalForm = {
  title: "",
  rubric: "",
  rigor: "medium",
  poolSize: 20,
  flashCount: 10,
  time: 30,
  low: 0.6,
  high: 0.4,
  randomPct: 0.1,
};

type OpenTabOverrides = { courseId?: number | null; evalId?: number | null };

export type DashboardState = {
  loading: boolean;
  accountRole: string;
  adminTeacher: any;
  isAssistant: boolean;
  error: string;
  setError: Dispatch<SetStateAction<string>>;
  success: string;
  setSuccess: Dispatch<SetStateAction<string>>;
  flashLink: string;
  setFlashLink: Dispatch<SetStateAction<string>>;

  activeTab: TabId;
  setActiveTab: (value: TabId) => void;
  openTab: (value: TabId, overrides?: OpenTabOverrides) => void;

  courses: any[];
  selectedCourseId: number | null;
  setSelectedCourseId: Dispatch<SetStateAction<number | null>>;
  pickCourse: (id: number) => void;
  selectedCourse: any;

  courseEvals: any[];
  setCourseEvals: Dispatch<SetStateAction<any[]>>;
  selectedEvalId: number | null;
  setSelectedEvalId: Dispatch<SetStateAction<number | null>>;
  pickEvaluation: (id: number) => void;
  selectedEval: any;
  setSelectedEval: Dispatch<SetStateAction<any>>;
  activityId: number | null;

  evalForm: EvalForm;
  patchEvalForm: (patch: Partial<EvalForm>) => void;
  creatingEval: boolean;
  setCreatingEval: Dispatch<SetStateAction<boolean>>;

  students: any[];
  setStudents: Dispatch<SetStateAction<any[]>>;
  studentToEdit: any;
  setStudentToEdit: Dispatch<SetStateAction<any>>;

  materials: any[];
  setMaterials: Dispatch<SetStateAction<any[]>>;

  reports: any[];
  selectedReportId: number | null;
  setSelectedReportId: Dispatch<SetStateAction<number | null>>;
  selectedReport: any;
  setSelectedReport: Dispatch<SetStateAction<any>>;
  reportMarkdown: string;
  setReportMarkdown: Dispatch<SetStateAction<string>>;
  previewMdModal: boolean;
  setPreviewMdModal: Dispatch<SetStateAction<boolean>>;

  questionBank: any;
  setQuestionBank: Dispatch<SetStateAction<any>>;
  selectedQIds: number[];
  setSelectedQIds: Dispatch<SetStateAction<number[]>>;

  evalStats: any;
  reviewList: any[];

  appointments: any[];
  availabilities: any[];
  selectedAppt: any;
  setSelectedAppt: Dispatch<SetStateAction<any>>;
  appointmentDraft: any;
  setAppointmentDraft: Dispatch<SetStateAction<any>>;
  saveAppointment: (studentId: number, date: string, block: string) => Promise<void>;

  loadInitialData: () => Promise<void>;
  loadCourseSubData: (courseId: number) => Promise<void>;
  loadEvalSubData: (evalId: number) => Promise<void>;
  loadAppointments: () => Promise<void>;
  loadAvailabilities: () => Promise<void>;
  refreshCourseEvals: () => Promise<void>;

  drafts: Map<string, unknown>;
};

const DashboardContext = createContext<DashboardState | null>(null);

export function useDashboard(): DashboardState {
  const value = useContext(DashboardContext);
  if (!value) throw new Error("useDashboard debe usarse dentro de DashboardProvider");
  return value;
}

export function usePersistentState<T>(
  key: string,
  initial: T | (() => T),
): [T, Dispatch<SetStateAction<T>>] {
  const { drafts } = useDashboard();
  const [value, setValue] = useState<T>(() =>
    drafts.has(key)
      ? (drafts.get(key) as T)
      : typeof initial === "function"
        ? (initial as () => T)()
        : initial,
  );
  const set = useCallback<Dispatch<SetStateAction<T>>>(
    (next) => {
      setValue((previous) => {
        const resolved =
          typeof next === "function" ? (next as (prev: T) => T)(previous) : next;
        drafts.set(key, resolved);
        return resolved;
      });
    },
    [drafts, key],
  );
  return [value, set];
}

export function DashboardProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const courseLoad = useRef(0);
  const evalLoad = useRef(0);
  const draftStore = useRef<Map<string, unknown>>(new Map());

  const [loading, setLoading] = useState(true);
  const [studentToEdit, setStudentToEdit] = useState<any>(null);
  const [accountRole, setAccountRole] = useState("");
  const [adminTeacher, setAdminTeacher] = useState<any>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [flashLink, setFlashLink] = useState("");

  const [activeTab, changeActiveTab] = useState<TabId>("courses");

  const [courses, setCourses] = useState<any[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [selectedCourse, setSelectedCourse] = useState<any>(null);

  const [courseEvals, setCourseEvals] = useState<any[]>([]);
  const [selectedEvalId, setSelectedEvalId] = useState<number | null>(null);
  const [selectedEval, setSelectedEval] = useState<any>(null);

  const [students, setStudents] = useState<any[]>([]);
  const [materials, setMaterials] = useState<any[]>([]);

  const [reports, setReports] = useState<any[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [selectedReport, setSelectedReport] = useState<any>(null);
  const [reportMarkdown, setReportMarkdown] = useState("");
  const [previewMdModal, setPreviewMdModal] = useState(false);

  const [questionBank, setQuestionBank] = useState<any>(null);
  const [selectedQIds, setSelectedQIds] = useState<number[]>([]);

  const [evalForm, setEvalForm] = useState<EvalForm>(initialEvalForm);
  const [creatingEval, setCreatingEval] = useState(false);

  const [appointmentDraft, setAppointmentDraft] = useState<any>(null);
  const [appointments, setAppointments] = useState<any[]>([]);
  const [availabilities, setAvailabilities] = useState<any[]>([]);
  const [selectedAppt, setSelectedAppt] = useState<any>(null);

  const [evalStats, setEvalStats] = useState<any>(null);
  const [reviewList, setReviewList] = useState<any[]>([]);

  const activityId = selectedEvalId && selectedEvalId < 0 ? -selectedEvalId : null;

  const patchEvalForm = (patch: Partial<EvalForm>) =>
    setEvalForm((previous) => ({ ...previous, ...patch }));

  const openTab = (value: TabId, overrides: OpenTabOverrides = {}) => {
    const courseId = overrides.courseId ?? selectedCourseId;
    const evalId = overrides.evalId ?? selectedEvalId;
    const url = new URL(location.href);
    url.searchParams.set("seccion", value);
    if (courseId) url.searchParams.set("curso", String(courseId));
    if (evalId) url.searchParams.set("evaluacion", String(evalId));
    history.pushState(null, "", url);
    changeActiveTab(value);
  };

  const setActiveTab = (value: TabId) => openTab(value);

  const pickCourse = (id: number) => {
    const url = new URL(location.href);
    url.searchParams.set("curso", String(id));
    url.searchParams.delete("evaluacion");
    history.pushState(null, "", url);
    setSelectedCourseId(id);
  };

  const pickEvaluation = (id: number) => {
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
      const query = new URLSearchParams(location.search);
      const section = query.get("seccion");
      if (TAB_IDS.includes(section as TabId)) changeActiveTab(section as TabId);
      else changeActiveTab("courses");
      const course = Number(query.get("curso"));
      if (course) setSelectedCourseId(course);
      const evaluation = Number(query.get("evaluacion"));
      if (evaluation) setSelectedEvalId(evaluation);
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

  const loadEvalSubData = async (evalId: number) => {
    const version = ++evalLoad.current;
    try {
      const [mats, reps, stats, review] = await Promise.all([
        api.getMaterials(evalId),
        api.getReports(evalId),
        api.getEvaluationStats(evalId),
        api.getReviewList(evalId),
      ]);
      if (version !== evalLoad.current) return;
      setMaterials(mats);
      setReports(reps);
      setEvalStats(stats);
      setReviewList(review.review_list || []);
    } catch (err: any) {
      if (version === evalLoad.current) setError(err.message || "No se pudieron cargar los datos");
    }
  };

  const loadCourseSubData = async (courseId: number) => {
    const version = ++courseLoad.current;
    ++evalLoad.current;
    setReports([]);
    setEvalStats(null);
    setReviewList([]);
    setSelectedReportId(null);
    setQuestionBank(null);
    try {
      const roster = await api.getStudents(courseId);
      if (version !== courseLoad.current) return;
      setStudents(roster);
      const evaluations = await api.getCourseEvaluations(courseId);
      if (version !== courseLoad.current) return;
      setCourseEvals(evaluations);
      if (evaluations.length > 0) {
        const preferred =
          evaluations.find(
            (e: any) => e.id === Number(new URLSearchParams(location.search).get("evaluacion")),
          ) || evaluations[0];
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
      const list = await api.getCourses();
      setCourses(list);
      setSelectedCourseId(
        list.find((c: any) => c.id === Number(new URLSearchParams(location.search).get("curso")))
          ?.id ||
          list[0]?.id ||
          null,
      );
      setSelectedCourse(list[0] || null);
      if (!list.length) {
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

  const refreshCourseEvals = async () => {
    if (!selectedCourseId) return;
    const evaluations = await api.getCourseEvaluations(selectedCourseId);
    setCourseEvals(evaluations);
    setSelectedEval(evaluations.find((ev: any) => ev.id === selectedEvalId) || null);
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
      setSelectedAppt(null);
      setReports([]);
      setEvalStats(null);
      setReviewList([]);
      const evaluation = courseEvals.find((x) => x.id === selectedEvalId);
      setSelectedEval(evaluation || null);
      if (evaluation) {
        patchEvalForm({
          title: evaluation.title,
          rubric: evaluation.prompt_rubric,
          rigor: evaluation.question_rigor,
          poolSize: evaluation.pool_size,
          flashCount: evaluation.flash_questions_count,
          time: evaluation.time_per_question,
          low: evaluation.low_threshold,
          high: evaluation.high_threshold,
        });
      }
      loadEvalSubData(selectedEvalId);
    }
  }, [selectedEvalId, courseEvals]);

  const saveAppointment = async (studentId: number, date: string, block: string) => {
    if (!selectedCourseId) return;
    if (appointmentDraft?.id) await api.rescheduleAppointment(appointmentDraft.id, date, block);
    else
      await api.scheduleAppointment(selectedCourseId, {
        estudiante_id: studentId,
        fecha: date,
        bloque: block,
        actividad_id: activityId,
      });
    setSuccess("Cita guardada con la fecha elegida.");
    await loadAppointments();
    if (selectedEvalId) await loadEvalSubData(selectedEvalId);
  };

  const value: DashboardState = {
    loading,
    accountRole,
    adminTeacher,
    isAssistant: accountRole === "ayudante",
    error,
    setError,
    success,
    setSuccess,
    flashLink,
    setFlashLink,
    activeTab,
    setActiveTab,
    openTab,
    courses,
    selectedCourseId,
    setSelectedCourseId,
    pickCourse,
    selectedCourse,
    courseEvals,
    setCourseEvals,
    selectedEvalId,
    setSelectedEvalId,
    pickEvaluation,
    selectedEval,
    setSelectedEval,
    activityId,
    evalForm,
    patchEvalForm,
    creatingEval,
    setCreatingEval,
    students,
    setStudents,
    studentToEdit,
    setStudentToEdit,
    materials,
    setMaterials,
    reports,
    selectedReportId,
    setSelectedReportId,
    selectedReport,
    setSelectedReport,
    reportMarkdown,
    setReportMarkdown,
    previewMdModal,
    setPreviewMdModal,
    questionBank,
    setQuestionBank,
    selectedQIds,
    setSelectedQIds,
    evalStats,
    reviewList,
    appointments,
    availabilities,
    selectedAppt,
    setSelectedAppt,
    appointmentDraft,
    setAppointmentDraft,
    saveAppointment,
    loadInitialData,
    loadCourseSubData,
    loadEvalSubData,
    loadAppointments,
    loadAvailabilities,
    refreshCourseEvals,
    drafts: draftStore.current,
  };

  return <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>;
}

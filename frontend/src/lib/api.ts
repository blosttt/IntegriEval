const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://127.0.0.1:8000/api";

export const getApiBase = () => API_BASE;
export const getWsBase = () => WS_BASE;

// ── Auth helpers ─────────────────────────────────────────────────────────────
export const getToken = () =>
  typeof window !== "undefined" ? localStorage.getItem("integrieval_token") : null;

export const saveToken = (token: string, role: string, name: string) => {
  if (typeof window !== "undefined") {
    localStorage.setItem("integrieval_token", token);
    localStorage.setItem("integrieval_role", role);
    localStorage.setItem("integrieval_name", name);
  }
};

export const logout = () => {
  if (typeof window !== "undefined") {
    localStorage.removeItem("integrieval_token");
    localStorage.removeItem("integrieval_role");
    localStorage.removeItem("integrieval_name");
  }
};

export const getRole = () =>
  typeof window !== "undefined" ? localStorage.getItem("integrieval_role") : null;

export const getName = () =>
  typeof window !== "undefined" ? localStorage.getItem("integrieval_name") : null;

// ── Generic fetch wrapper ────────────────────────────────────────────────────
async function request(endpoint: string, options: RequestInit = {}) {
  const token = getToken();
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

  if (!response.ok) {
    let errorDetail = "Ocurrió un error inesperado";
    try {
      const errData = await response.json();
      errorDetail = errData.detail || errorDetail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  // ── Auth ──────────────────────────────────────────────────────────────────
  register: (body: any) =>
    request("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  login: async (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);
    const data = await request("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
    });
    if (data.access_token) saveToken(data.access_token, data.role, data.name);
    return data;
  },

  getMe: () => request("/auth/me"),

  // ── Courses ───────────────────────────────────────────────────────────────
  getCourses: () => request("/courses/"),
  getCourse: (courseId: number) => request(`/courses/${courseId}`),
  createCourse: (body: any) =>
    request("/courses/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  // ── Students (no-account, managed by teacher) ─────────────────────────────
  getStudents: (courseId: number) => request(`/courses/${courseId}/students`),

  createStudent: (courseId: number, body: { name: string; email: string }) =>
    request(`/courses/${courseId}/students`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  importStudentsCSV: (courseId: number, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request(`/courses/${courseId}/students/import`, {
      method: "POST",
      body: formData,
    });
  },

  deleteStudent: (courseId: number, studentId: number) =>
    request(`/courses/${courseId}/students/${studentId}`, { method: "DELETE" }),

  // ── Evaluations ───────────────────────────────────────────────────────────
  getCourseEvaluations: (courseId: number) => request(`/courses/${courseId}/evaluations`),
  getEvaluation: (evalId: number) => request(`/evaluations/${evalId}`),

  createEvaluation: (courseId: number, body: any) =>
    request(`/courses/${courseId}/evaluations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  updateEvaluation: (evalId: number, body: any) =>
    request(`/evaluations/${evalId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  deleteEvaluation: (evalId: number) =>
    request(`/evaluations/${evalId}`, { method: "DELETE" }),

  // ── Course Materials ──────────────────────────────────────────────────────
  getMaterials: (evalId: number) => request(`/evaluations/${evalId}/materials`),

  uploadMaterial: (evalId: number, title: string, file: File) => {
    const formData = new FormData();
    formData.append("title", title);
    formData.append("file", file);
    return request(`/evaluations/${evalId}/materials`, {
      method: "POST",
      body: formData,
    });
  },

  deleteMaterial: (evalId: number, materialId: number) =>
    request(`/evaluations/${evalId}/materials/${materialId}`, { method: "DELETE" }),

  // ── Reports ───────────────────────────────────────────────────────────────
  getReports: (evalId: number) => request(`/reports/evaluation/${evalId}`),
  getReport: (reportId: number) => request(`/reports/${reportId}`),
  getReportMarkdown: (reportId: number) => request(`/reports/${reportId}/markdown`),

  uploadSingleReport: (evalId: number, studentId: number, file: File) => {
    const formData = new FormData();
    formData.append("evaluation_id", evalId.toString());
    formData.append("student_id", studentId.toString());
    formData.append("file", file);
    return request("/reports/upload-single", { method: "POST", body: formData });
  },

  bulkUploadReports: (evalId: number, studentIds: number[], files: File[]) => {
    const formData = new FormData();
    formData.append("evaluation_id", evalId.toString());
    formData.append("student_ids", JSON.stringify(studentIds));
    files.forEach((f) => formData.append("files", f));
    return request("/reports/bulk-upload", { method: "POST", body: formData });
  },

  updateReportScore: (reportId: number, score: number) =>
    request(`/reports/${reportId}/score`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ teacher_score_override: score }),
    }),

  reanalyzeReport: (reportId: number) =>
    request(`/reports/${reportId}/reanalyze`, { method: "POST" }),

  // ── Question Pool ─────────────────────────────────────────────────────────
  getQuestionBank: (reportId: number) => request(`/reports/${reportId}/questions`),

  updateQuestion: (reportId: number, questionId: number, body: any) =>
    request(`/reports/${reportId}/questions/${questionId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  createQuestion: (reportId: number, body: any) =>
    request(`/reports/${reportId}/questions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  deleteQuestion: (reportId: number, questionId: number) =>
    request(`/reports/${reportId}/questions/${questionId}`, { method: "DELETE" }),

  selectRandomQuestions: (reportId: number) =>
    request(`/reports/${reportId}/questions/select-random`, { method: "POST" }),

  selectQuestions: (reportId: number, questionIds: number[]) =>
    request(`/reports/${reportId}/questions/select`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question_ids: questionIds }),
    }),

  sendFlashTest: (reportId: number) =>
    request(`/reports/${reportId}/send-flash`, { method: "POST" }),

  // ── Flash Test (no-auth, token-based) ────────────────────────────────────
  validateFlashToken: (token: string) => request(`/flash/validate/${token}`),
  getFlashResult: (sessionId: number, token: string) =>
    request(`/flash/${sessionId}/result?token=${token}`),

  // ── Appointments ──────────────────────────────────────────────────────────
  getAppointments: () => request("/appointments/"),
  rescheduleAppointment: (apptId: number, newTimeIso: string) =>
    request(`/appointments/${apptId}/reschedule`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_time: newTimeIso }),
    }),
  submitAppointmentFeedback: (apptId: number, body: any) =>
    request(`/appointments/${apptId}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  getTeacherAvailabilities: () => request("/appointments/availability"),
  addTeacherAvailability: (body: any) =>
    request("/appointments/availability", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  deleteTeacherAvailability: (availId: number) =>
    request(`/appointments/availability/${availId}`, { method: "DELETE" }),

  // ── Dashboard & Analytics ─────────────────────────────────────────────────
  getCourseStats: (courseId: number) => request(`/dashboard/course/${courseId}/stats`),
  getEvaluationStats: (evalId: number) => request(`/dashboard/evaluation/${evalId}/stats`),
  getReviewList: (evalId: number) => request(`/dashboard/review-list/${evalId}`),
  getAuditLogs: (limit = 50, offset = 0) =>
    request(`/dashboard/audit-logs?limit=${limit}&offset=${offset}`),
  getSystemMetrics: () => request("/dashboard/system-metrics"),
};

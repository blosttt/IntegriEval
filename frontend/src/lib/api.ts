const API_BASE = "http://127.0.0.1:8000/api";
const WS_BASE = "ws://127.0.0.1:8000/api";

export const getApiBase = () => API_BASE;
export const getWsBase = () => WS_BASE;

// Helper to get token
export const getToken = () => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("integrieval_token");
  }
  return null;
};

// Helper to save token
export const saveToken = (token: string, role: string, name: string) => {
  if (typeof window !== "undefined") {
    localStorage.setItem("integrieval_token", token);
    localStorage.setItem("integrieval_role", role);
    localStorage.setItem("integrieval_name", name);
  }
};

// Helper to clear session
export const logout = () => {
  if (typeof window !== "undefined") {
    localStorage.removeItem("integrieval_token");
    localStorage.removeItem("integrieval_role");
    localStorage.removeItem("integrieval_name");
  }
};

export const getRole = () => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("integrieval_role");
  }
  return null;
};

export const getName = () => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("integrieval_name");
  }
  return null;
};

// Generic fetch wrapper
async function request(endpoint: string, options: RequestInit = {}) {
  const token = getToken();
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = "Ocurrió un error inesperado";
    try {
      const errData = await response.json();
      errorDetail = errData.detail || errorDetail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const api = {
  // --- Auth ---
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

    if (data.access_token) {
      saveToken(data.access_token, data.role, data.name);
    }
    return data;
  },

  loginSSOMock: async (email: string, name: string) => {
    const data = await request("/auth/sso/google-mock", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, name }),
    });

    if (data.access_token) {
      saveToken(data.access_token, data.role, data.name);
    }
    return data;
  },

  getMe: () => request("/auth/me"),

  // --- Courses ---
  getCourses: () => request("/courses/"),
  getCourse: (courseId: number) => request(`/courses/${courseId}`),
  createCourse: (body: any) => 
    request("/courses/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  enrollStudent: (courseId: number, studentEmail: string) => 
    request(`/courses/${courseId}/enroll`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ student_email: studentEmail }),
    }),
  getCourseStudents: (courseId: number) => request(`/courses/${courseId}/students`),

  // --- Evaluations ---
  createEvaluation: (courseId: number, body: any) => 
    request(`/courses/${courseId}/evaluations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  getCourseEvaluations: (courseId: number) => request(`/courses/${courseId}/evaluations`),
  getEvaluation: (evalId: number) => request(`/evaluations/${evalId}`),
  getEvaluationStudentStatus: (evalId: number) => request(`/evaluations/${evalId}/status`),

  // --- Reports & Parsing ---
  uploadReport: (evaluationId: number, file: File) => {
    const formData = new FormData();
    formData.append("evaluation_id", evaluationId.toString());
    formData.append("file", file);

    return request("/reports/upload", {
      method: "POST",
      // Note: do not set Content-Type header when sending FormData; the browser sets it automatically with the boundary
      body: formData,
    });
  },

  // --- Questions Review (Teacher) ---
  getStudentQuestionBank: (evaluationId: number, studentId: number) => 
    request(`/questions/evaluation/${evaluationId}/student/${studentId}`),
  reviewQuestionBank: (bankId: number, body: any) => 
    request(`/questions/bank/${bankId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  regenerateQuestionBank: (evaluationId: number, studentId: number) => 
    request(`/questions/evaluation/${evaluationId}/regenerate/${studentId}`, {
      method: "POST",
    }),

  // --- Session Control ---
  startSession: (evaluationId: number) => 
    request("/session/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ evaluation_id: evaluationId }),
    }),
  getSessionStatus: (sessionId: number) => request(`/session/${sessionId}/status`),

  // --- Appointments / Scheduling ---
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
    request(`/appointments/availability/${availId}`, {
      method: "DELETE",
    }),

  // --- Dashboards & Analytics ---
  getCourseStats: (courseId: number) => request(`/dashboard/course/${courseId}/stats`),
  getEvaluationStats: (evalId: number) => request(`/dashboard/evaluation/${evalId}/stats`),
  getAuditLogs: (limit = 50, offset = 0) => request(`/dashboard/audit-logs?limit=${limit}&offset=${offset}`),
  getSystemMetrics: () => request("/dashboard/system-metrics"),
};

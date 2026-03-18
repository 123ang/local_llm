const API_BASE = "/api";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  // Only set JSON content-type if body is not FormData and caller didn't set Content-Type
  if (!(options.body instanceof FormData) && !(options.body instanceof URLSearchParams)) {
    if (!headers["Content-Type"]) headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    if (res.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const message = Array.isArray(err.detail)
      ? err.detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join(". ")
      : (err.detail || "Request failed");
    throw new ApiError(message, res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // Auth
  login: (email: string, password: string) => {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    return request<{ access_token: string; user: any }>("/auth/login", {
      method: "POST",
      body: form,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },
  getMe: () => request<any>("/auth/me"),

  // Companies
  getCompanies: () => request<any[]>("/companies"),
  createCompany: (data: { name: string; description?: string }) =>
    request<any>("/companies", { method: "POST", body: JSON.stringify(data) }),
  updateCompany: (id: number, data: any) =>
    request<any>(`/companies/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  // Users
  getUsers: (companyId?: number) =>
    request<any[]>(`/users${companyId ? `?company_id=${companyId}` : ""}`),
  createUser: (data: any) =>
    request<any>("/users", { method: "POST", body: JSON.stringify(data) }),
  updateUser: (id: number, data: any) =>
    request<any>(`/users/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  // Documents
  getDocuments: (companyId: number) => request<any[]>(`/documents/${companyId}`),
  uploadDocument: (companyId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<any>(`/documents/${companyId}`, { method: "POST", body: form });
  },
  deleteDocument: (companyId: number, docId: number) =>
    request<void>(`/documents/${companyId}/${docId}`, { method: "DELETE" }),

  // FAQ
  getFAQ: (companyId: number) => request<any[]>(`/faq/${companyId}`),
  createFAQ: (companyId: number, data: any) =>
    request<any>(`/faq/${companyId}`, { method: "POST", body: JSON.stringify(data) }),
  updateFAQ: (companyId: number, faqId: number, data: any) =>
    request<any>(`/faq/${companyId}/${faqId}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteFAQ: (companyId: number, faqId: number) =>
    request<void>(`/faq/${companyId}/${faqId}`, { method: "DELETE" }),

  // Datasets
  getDatasets: (companyId: number) => request<any[]>(`/datasets/${companyId}`),
  createManualTable: (companyId: number, data: any) =>
    request<any>(`/datasets/${companyId}/manual`, { method: "POST", body: JSON.stringify(data) }),
  uploadTableAndData: (companyId: number, file: File, displayName: string, description: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("display_name", displayName);
    form.append("description", description);
    return request<any>(`/datasets/${companyId}/upload-table`, { method: "POST", body: form });
  },
  uploadDataToTable: (companyId: number, datasetId: number, file: File, mode: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("mode", mode);
    return request<any>(`/datasets/${companyId}/${datasetId}/upload-data`, { method: "POST", body: form });
  },
  previewCSV: (companyId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<any>(`/datasets/${companyId}/preview-csv`, { method: "POST", body: form });
  },
  previewSQL: (companyId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<any>(`/datasets/${companyId}/preview-sql`, { method: "POST", body: form });
  },
  uploadSQL: (companyId: number, file: File, displayName: string, description: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("display_name", displayName);
    form.append("description", description);
    return request<any>(`/datasets/${companyId}/upload-sql`, { method: "POST", body: form });
  },
  getDatasetRows: (companyId: number, datasetId: number, limit = 100, offset = 0) =>
    request<{ columns: string[]; rows: Record<string, unknown>[]; total: number }>(
      `/datasets/${companyId}/${datasetId}/rows?limit=${limit}&offset=${offset}`
    ),

  // Chat
  getChatSessions: () => request<any[]>("/chat/sessions"),
  getChatMessages: (sessionId: number) => request<any[]>(`/chat/sessions/${sessionId}/messages`),
  sendMessage: async (message: string, sessionId?: number, companyId?: number, sources?: string[]) => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 120_000); // 2 min for slow LLM
    try {
      return await request<any>("/chat", {
        method: "POST",
        body: JSON.stringify({ message, session_id: sessionId, company_id: companyId, sources: sources ?? undefined }),
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timeout);
    }
  },
  deleteSession: (sessionId: number) =>
    request<void>(`/chat/sessions/${sessionId}`, { method: "DELETE" }),

  // Audit
  getAuditLogs: (companyId?: number, limit = 100, offset = 0) =>
    request<any[]>(`/audit?${companyId ? `company_id=${companyId}&` : ""}limit=${limit}&offset=${offset}`),

  // Generic request (for one-off calls)
  request: <T = any>(path: string, options?: RequestInit) => request<T>(path, options),
};

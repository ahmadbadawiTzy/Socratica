// API base URL from environment
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

// Token storage keys
const ACCESS_KEY = "socratica_access";
const REFRESH_KEY = "socratica_refresh";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_KEY);
}
export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}
export function setTokens(access: string, refresh: string) {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}
export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  isFormData?: boolean
): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!isFormData) headers["Content-Type"] = "application/json";

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: isFormData ? (body as FormData) : body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || err.error?.message || "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserProfile {
  id: string;
  email: string;
  display_name: string;
  system_role: string;
}

export const api = {
  auth: {
    register: (email: string, password: string, display_name: string) =>
      request<UserProfile>("POST", "/api/v1/auth/register", { email, password, display_name }),
    login: async (email: string, password: string): Promise<UserProfile> => {
      const res = await request<TokenResponse>("POST", "/api/v1/auth/login", { email, password });
      setTokens(res.access_token, res.refresh_token);
      return api.auth.me();
    },
    logout: () => { clearTokens(); },
    me: () => request<UserProfile>("GET", "/api/v1/auth/me"),
  },

  // ── Courses ────────────────────────────────────────────────────────────────
  courses: {
    list: () => request<Course[]>("GET", "/api/v1/courses"),
    create: (code: string, name: string, description?: string) =>
      request<Course>("POST", "/api/v1/courses", { code, name, description }),
    get: (id: string) => request<Course>("GET", `/api/v1/courses/${id}`),
  },

  // ── Documents ─────────────────────────────────────────────────────────────
  documents: {
    list: (courseId: string) =>
      request<DocumentItem[]>("GET", `/api/v1/courses/${courseId}/documents`),
    upload: (courseId: string, formData: FormData) =>
      request<DocumentItem>("POST", `/api/v1/courses/${courseId}/documents`, formData, true),
    delete: (courseId: string, documentId: string) =>
      request<void>("DELETE", `/api/v1/courses/${courseId}/documents/${documentId}`),
  },

  // ── Conversations ─────────────────────────────────────────────────────────
  conversations: {
    list: () => request<ConversationListItem[]>("GET", "/api/v1/conversations"),
    create: (courseId: string, mode?: string, title?: string) =>
      request<ConversationListItem>("POST", "/api/v1/conversations", { course_id: courseId, mode: mode || "qa", title }),
    get: (id: string) => request<Conversation>("GET", `/api/v1/conversations/${id}`),
    delete: (id: string) => request<void>("DELETE", `/api/v1/conversations/${id}`),
    sendMessage: (conversationId: string, content: string, mode?: string) =>
      request<SendMessageResponse>("POST", `/api/v1/conversations/${conversationId}/messages`, { content, mode }),
  },


  // ── Escalations ───────────────────────────────────────────────────────────
  escalations: {
    list: () => request<EscalationItem[]>("GET", "/api/v1/escalations"),
    listByCourse: (courseId: string) =>
      request<EscalationItem[]>("GET", `/api/v1/escalations/course/${courseId}`),
  },
};



// ── Types ─────────────────────────────────────────────────────────────────────

export interface Course {
  id: string;
  code: string;
  name: string;
  description: string | null;
  is_active: boolean;
  document_count?: number;
}

export interface DocumentItem {
  id: string;
  document_name: string;
  original_filename: string;
  document_type: string | null;
  ingestion_status: string;
  ingestion_error: string | null;
  meeting: string | null;
  chapter: string | null;
  file_size_bytes: number | null;
}

export interface Citation {
  document_name: string;
  page: string | null;
  section: string | null;
  chunk_id: string | null;
  document_id: string | null;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations: Citation[] | null;
  meta: Record<string, unknown> | null;
  created_at: string;
}

export interface ConversationListItem {
  id: string;
  course_id: string;
  title: string | null;
  mode: string;
  is_active: boolean;
  created_at: string;
}

export interface Conversation extends ConversationListItem {
  messages: Message[];
}

export interface SendMessageResponse {
  conversation_id: string;
  user_message_id: string;
  assistant_message_id: string;
  content: string;
  citations: Citation[];
  mode: string;
  status: string;
  escalation_id: string | null;
}

export interface EscalationItem {
  id: string;
  conversation_id: string;
  course_id: string;
  question: string;
  reason: string;
  context_summary: string | null;
  status: string;
  resolution_note: string | null;
  created_at: string;
}

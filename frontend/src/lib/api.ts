// Typed API client for the CareerSetu backend. Centralises the base URL, JWT
// bearer token, JSON handling and error surfacing so pages stay declarative.

const API_BASE = "https://career-setu-azure.vercel.app/api/v1";
  // (import.meta.env.VITE_API_BASE_URL as string | undefined)
  // "http://localhost:8000/api/v1";

/** Absolute base URL of the backend API — used for full-page OAuth redirects. */
export const apiBaseUrl = API_BASE;

const TOKEN_KEY = "careersetu_token";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}
export function setToken(token: string) {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    /* storage unavailable — token stays in-memory for this tab only */
  }
}
export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function parse(res: Response): Promise<any> {
  if (res.status === 204) return null;
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

type Options = { auth?: boolean; signal?: AbortSignal };

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  opts: Options = {},
): Promise<T> {
  const headers: Record<string, string> = {};
  const isForm = body instanceof FormData;
  if (body !== undefined && !isForm) headers["Content-Type"] = "application/json";
  if (opts.auth !== false) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: isForm ? (body as FormData) : body !== undefined ? JSON.stringify(body) : undefined,
      signal: opts.signal,
    });
  } catch {
    throw new ApiError("Can't reach the CareerSetu API. Is the backend running?", 0);
  }

  const data = await parse(res);
  if (!res.ok) {
    const detail =
      (data && typeof data === "object" && (data.detail || data.message)) ||
      (typeof data === "string" && data) ||
      `Request failed (${res.status})`;
    throw new ApiError(
      Array.isArray(detail) ? detail.map((d: any) => d.msg || d).join("; ") : String(detail),
      res.status,
    );
  }
  return data as T;
}

export const api = {
  get: <T>(p: string, o?: Options) => request<T>("GET", p, undefined, o),
  post: <T>(p: string, b?: unknown, o?: Options) => request<T>("POST", p, b, o),
  del: <T>(p: string, o?: Options) => request<T>("DELETE", p, undefined, o),
  base: API_BASE,
};

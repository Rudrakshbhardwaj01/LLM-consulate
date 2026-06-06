const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function apiUrl(path: string): string {
  const base = API_BASE.replace(/\/$/, "");
  const normalized = path.startsWith("/") ? path : `/${path}`;
  const withApi = normalized.startsWith("/api/") ? normalized : `/api${normalized}`;
  return `${base}${withApi}`;
}

export function getSessionHeaders(sessionId: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    "X-Session-Id": sessionId,
  };
}

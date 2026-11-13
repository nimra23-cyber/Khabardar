/**
 * Minimal API client with standard-envelope handling (Task 2.14).
 *
 * The backend returns `{ ok: true, data }` on success and
 * `{ ok: false, error: { code, message, operation } }` on failure. This client
 * surfaces a typed result so the UI can render errors safely (never leaking raw
 * internals) and preserve user input on failure (Req 22.7).
 *
 * The backend base URL is configurable via `VITE_API_BASE_URL` (set at build
 * time for the deployed frontend). It defaults to a relative base so a local
 * dev proxy / same-origin deployment works without configuration.
 */

export interface ApiError {
  code: string;
  message: string;
  operation: string;
}

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: ApiError };

const RAW_BASE =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || "";
// Normalize: strip a single trailing slash so we can join with "/api/...".
export const API_BASE = RAW_BASE.replace(/\/$/, "");

function buildUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${p}`;
}

async function parseEnvelope<T>(resp: Response): Promise<ApiResult<T>> {
  let body: unknown;
  try {
    body = await resp.json();
  } catch {
    return {
      ok: false,
      error: {
        code: "BAD_RESPONSE",
        message: "The server returned an unreadable response.",
        operation: "network",
      },
    };
  }
  const b = body as Record<string, unknown>;
  if (b && b.ok === true) {
    return { ok: true, data: b.data as T };
  }
  if (b && b.ok === false && b.error) {
    return { ok: false, error: b.error as ApiError };
  }
  return {
    ok: false,
    error: {
      code: "UNEXPECTED",
      message: "The server returned an unexpected response.",
      operation: "network",
    },
  };
}

export async function apiPost<T>(
  path: string,
  payload: unknown,
): Promise<ApiResult<T>> {
  try {
    const resp = await fetch(buildUrl(path), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return await parseEnvelope<T>(resp);
  } catch {
    return {
      ok: false,
      error: {
        code: "NETWORK_ERROR",
        message: "Could not reach the server. Check your connection and try again.",
        operation: "network",
      },
    };
  }
}

export async function apiGet<T>(path: string): Promise<ApiResult<T>> {
  try {
    const resp = await fetch(buildUrl(path), { method: "GET" });
    return await parseEnvelope<T>(resp);
  } catch {
    return {
      ok: false,
      error: {
        code: "NETWORK_ERROR",
        message: "Could not reach the server. Check your connection and try again.",
        operation: "network",
      },
    };
  }
}

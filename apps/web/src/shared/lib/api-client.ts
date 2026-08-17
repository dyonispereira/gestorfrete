import type { ApiErrorBody, AuthTokens } from "@gestorfrete/types";

import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "./token-storage";

const API_BASE_URL = `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1`;

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: ApiErrorBody["error"]["details"];

  constructor(status: number, body: ApiErrorBody) {
    super(body.error.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.error.code;
    this.details = body.error.details;
  }
}

/** Fired when a refresh attempt itself fails — the session is genuinely over. */
export class SessionExpiredError extends Error {
  constructor() {
    super("Sessão expirada");
    this.name = "SessionExpiredError";
  }
}

let refreshInFlight: Promise<void> | null = null;

async function refreshSession(): Promise<void> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) throw new SessionExpiredError();

  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    clearTokens();
    throw new SessionExpiredError();
  }

  const tokens = (await response.json()) as AuthTokens;
  setTokens(tokens.access_token, tokens.refresh_token);
}

interface ApiFetchOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  /** Set by the retried call after a 401 to avoid an infinite refresh loop. */
  _isRetry?: boolean;
}

/**
 * Thin wrapper around `fetch` for the frozen `docs/api/openapi.yaml` contract:
 * base URL + `/api/v1`, Bearer auth, JSON in/out, and a single
 * refresh-and-retry on `401` (concurrent 401s share one in-flight refresh).
 */
export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { body, _isRetry, headers, ...rest } = options;
  const accessToken = getAccessToken();

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401 && !_isRetry && getRefreshToken()) {
    refreshInFlight ??= refreshSession().finally(() => {
      refreshInFlight = null;
    });
    await refreshInFlight;
    return apiFetch<T>(path, { ...options, _isRetry: true });
  }

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as ApiErrorBody | null;
    throw new ApiError(
      response.status,
      errorBody ?? { error: { code: "UNKNOWN_ERROR", message: response.statusText } }
    );
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

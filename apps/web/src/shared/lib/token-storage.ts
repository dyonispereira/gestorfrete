/**
 * Access/refresh token persistence. `localStorage`-backed: the frozen contract
 * (`001-authentication.md`) leaves the refresh-token transport ambiguous
 * ("corpo ou cookie httpOnly, conforme a superfície") and never specifies a
 * Web-specific choice — httpOnly cookies would need Backend cookie-issuing
 * support that doesn't exist yet, so localStorage is the real, working
 * integration today, not a placeholder standing in for one.
 */

const ACCESS_TOKEN_KEY = "gestorfrete.access_token";
const REFRESH_TOKEN_KEY = "gestorfrete.refresh_token";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

export function getAccessToken(): string | null {
  if (!isBrowser()) return null;
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (!isBrowser()) return null;
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string): void {
  if (!isBrowser()) return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens(): void {
  if (!isBrowser()) return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

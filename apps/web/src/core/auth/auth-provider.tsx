"use client";

import * as React from "react";

import { apiFetch } from "@/shared/lib/api-client";
import { clearTokens, getAccessToken, setTokens } from "@/shared/lib/token-storage";
import type { LoginResponse } from "@gestorfrete/types";

interface AuthContextValue {
  /** `null` until the first client render resolves token presence (avoids SSR flash). */
  isAuthenticated: boolean | null;
  isLoggingIn: boolean;
  loginError: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = React.createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = React.useState<boolean | null>(null);
  const [isLoggingIn, setIsLoggingIn] = React.useState(false);
  const [loginError, setLoginError] = React.useState<string | null>(null);

  React.useEffect(() => {
    setIsAuthenticated(Boolean(getAccessToken()));
  }, []);

  const login = React.useCallback(async (email: string, password: string) => {
    setIsLoggingIn(true);
    setLoginError(null);
    try {
      const response = await apiFetch<LoginResponse>("/auth/login", {
        method: "POST",
        body: { email, password },
      });
      setTokens(response.access_token, response.refresh_token);
      setIsAuthenticated(true);
    } catch (error) {
      setLoginError(error instanceof Error ? error.message : "Não foi possível entrar.");
      throw error;
    } finally {
      setIsLoggingIn(false);
    }
  }, []);

  const logout = React.useCallback(() => {
    apiFetch("/auth/logout", { method: "POST" }).catch(() => {
      // Encerrar a sessão localmente mesmo se a chamada ao Backend falhar
      // (rede indisponível, sessão já expirada no servidor, etc.) — o usuário
      // sempre consegue sair do próprio navegador.
    });
    clearTokens();
    setIsAuthenticated(false);
  }, []);

  const value = React.useMemo(
    () => ({ isAuthenticated, isLoggingIn, loginError, login, logout }),
    [isAuthenticated, isLoggingIn, loginError, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = React.useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
}

"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";

import { useAuth } from "@/core/auth/auth-provider";
import { apiFetch } from "@/shared/lib/api-client";
import type { AuthUser, MeResponse, Session, TenantContext } from "@gestorfrete/types";

interface SessionContextValue {
  user: AuthUser | null;
  tenant: TenantContext | null;
  session: Session | null;
  isLoading: boolean;
  error: Error | null;
}

const SessionContext = React.createContext<SessionContextValue | null>(null);

/**
 * Owns `GET /auth/me` — the single source of truth for the authenticated
 * User/Tenant/Session (`identity_access`, D208). Only fetches once
 * `AuthProvider` confirms a token exists; `TenantBrandingProvider` and
 * `PermissionsProvider` both read from this context rather than re-fetching.
 */
export function SessionProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();

  const { data, isLoading, error } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: () => apiFetch<MeResponse>("/auth/me"),
    enabled: isAuthenticated === true,
  });

  const value = React.useMemo<SessionContextValue>(
    () => ({
      user: data?.user ?? null,
      tenant: data?.tenant ?? null,
      session: data?.session ?? null,
      isLoading: isAuthenticated === null || (isAuthenticated && isLoading),
      error: error as Error | null,
    }),
    [data, isLoading, error, isAuthenticated]
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionContextValue {
  const context = React.useContext(SessionContext);
  if (!context) throw new Error("useSession must be used within a SessionProvider");
  return context;
}

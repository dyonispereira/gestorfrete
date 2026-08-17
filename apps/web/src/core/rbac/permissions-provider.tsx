"use client";

import * as React from "react";
import { useQueries } from "@tanstack/react-query";

import { useSession } from "@/core/tenant/session-provider";
import { apiFetch } from "@/shared/lib/api-client";
import type { Role } from "@gestorfrete/types";

interface PermissionsContextValue {
  /** Effective permission codes across every Role the User holds (`modulo.recurso.acao`). */
  permissions: Set<string>;
  isLoading: boolean;
  hasPermission: (code: string) => boolean;
  hasAnyPermission: (codes: string[]) => boolean;
}

const PermissionsContext = React.createContext<PermissionsContextValue | null>(null);

/**
 * Resolves RBAC the same way the Backend does (`identity_access`,
 * `RBAC_MATRIX.md`): a User has Roles, a Role carries permission codes —
 * there is no separate "my permissions" endpoint, so this unions
 * `GET /roles/{id}` across every Role UUID on `User.roles`.
 */
export function PermissionsProvider({ children }: { children: React.ReactNode }) {
  const { user } = useSession();
  const roleIds = user?.roles ?? [];

  const roleQueries = useQueries({
    queries: roleIds.map((roleId) => ({
      queryKey: ["roles", roleId],
      queryFn: () => apiFetch<Role>(`/roles/${roleId}`),
      enabled: roleIds.length > 0,
      staleTime: 5 * 60_000,
    })),
  });

  const isLoading = roleIds.length > 0 && roleQueries.some((query) => query.isLoading);

  const permissions = React.useMemo(() => {
    const codes = new Set<string>();
    for (const query of roleQueries) {
      for (const code of query.data?.permissions ?? []) codes.add(code);
    }
    return codes;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roleQueries.map((q) => q.dataUpdatedAt).join(",")]);

  const hasPermission = React.useCallback((code: string) => permissions.has(code), [permissions]);
  const hasAnyPermission = React.useCallback(
    (codes: string[]) => codes.some((code) => permissions.has(code)),
    [permissions]
  );

  const value = React.useMemo(
    () => ({ permissions, isLoading, hasPermission, hasAnyPermission }),
    [permissions, isLoading, hasPermission, hasAnyPermission]
  );

  return <PermissionsContext.Provider value={value}>{children}</PermissionsContext.Provider>;
}

export function usePermissions(): PermissionsContextValue {
  const context = React.useContext(PermissionsContext);
  if (!context) throw new Error("usePermissions must be used within a PermissionsProvider");
  return context;
}

"use client";

import * as React from "react";

import { useSession } from "@/core/tenant/session-provider";

interface PermissionsContextValue {
  /** Effective permission codes across every Role the User holds (`modulo.recurso.acao`). */
  permissions: Set<string>;
  isLoading: boolean;
  hasPermission: (code: string) => boolean;
  hasAnyPermission: (codes: string[]) => boolean;
}

const PermissionsContext = React.createContext<PermissionsContextValue | null>(null);

/**
 * Correção RBAC pós-Lote 2: as permissões efetivas vêm prontas de
 * `GET /auth/me` (`MeResponse.permissions`, calculado pelo Backend via
 * `AuthorizationService.get_permission_codes` — a mesma lógica que
 * `require_permission` usa para autorizar cada endpoint). Antes, este
 * provider refazia o cálculo no Frontend unindo `GET /roles/{id}` por Role,
 * o que exigia `identity_access.role.view` — uma permissão administrativa
 * que um usuário operacional comum não tem, e sem ela NENHUMA permissão era
 * resolvida (o menu inteiro colapsava para só o Dashboard). `GET /roles/{id}`
 * continua existindo e protegido, só não é mais consultado para este fim.
 */
export function PermissionsProvider({ children }: { children: React.ReactNode }) {
  const { permissions: permissionCodes, isLoading } = useSession();

  const permissions = React.useMemo(() => new Set(permissionCodes), [permissionCodes]);

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

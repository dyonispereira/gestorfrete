"use client";

import * as React from "react";

import { Button, Checkbox, toast } from "@gestorfrete/ui";
import type { Permission, Role } from "@gestorfrete/types";

import { useAllPermissionsQuery } from "@/modules/identity/hooks/use-permissions-catalog";
import { useUpdateRoleMutation } from "@/modules/identity/hooks/use-roles";
import { ApiError } from "@/shared/lib/api-client";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

interface PermissionMatrixProps {
  role: Role;
  editable: boolean;
}

/**
 * Every checkbox here comes from `GET /permissions` (`useAllPermissionsQuery`)
 * — never a list written in this file. Saving PATCHes `/roles/{id}` with the
 * new `permissions` code array; the Backend re-validates every code against
 * the same catalog (D216).
 */
export function PermissionMatrix({ role, editable }: PermissionMatrixProps) {
  const catalogQuery = useAllPermissionsQuery();
  const updateRole = useUpdateRoleMutation(role.id);

  const [selected, setSelected] = React.useState<Set<string>>(new Set(role.permissions));

  React.useEffect(() => {
    setSelected(new Set(role.permissions));
  }, [role.permissions]);

  const catalog = catalogQuery.data;
  const grouped = React.useMemo(() => {
    const byModule = new Map<string, Permission[]>();
    for (const permission of catalog ?? []) {
      const list = byModule.get(permission.module) ?? [];
      list.push(permission);
      byModule.set(permission.module, list);
    }
    return Array.from(byModule.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [catalog]);

  const isDirty = React.useMemo(() => {
    if (selected.size !== role.permissions.length) return true;
    return role.permissions.some((code) => !selected.has(code));
  }, [selected, role.permissions]);

  function toggle(code: string) {
    if (!editable) return;
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(code)) next.delete(code);
      else next.add(code);
      return next;
    });
  }

  function toggleModule(codes: string[], allSelected: boolean) {
    if (!editable) return;
    setSelected((current) => {
      const next = new Set(current);
      for (const code of codes) {
        if (allSelected) next.delete(code);
        else next.add(code);
      }
      return next;
    });
  }

  async function handleSave() {
    try {
      await updateRole.mutateAsync({ permissions: Array.from(selected) });
      toast.success("Permissões atualizadas.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível salvar as permissões.");
    }
  }

  if (catalogQuery.isLoading) return <LoadingState rows={6} />;
  if (catalogQuery.error)
    return (
      <ErrorState
        description="Não foi possível carregar o catálogo de permissões."
        onRetry={() => catalogQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      {editable ? (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">{selected.size} permissões selecionadas</p>
          <Button onClick={handleSave} disabled={!isDirty || updateRole.isPending}>
            {updateRole.isPending ? "Salvando…" : "Salvar permissões"}
          </Button>
        </div>
      ) : null}

      <div className="flex flex-col divide-y divide-border rounded-md border border-border">
        {grouped.map(([module, permissions]) => {
          const codes = (permissions ?? []).map((p) => p.code);
          const allSelected = codes.length > 0 && codes.every((code) => selected.has(code));
          return (
            <div key={module} className="flex flex-col gap-3 p-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-foreground">{module}</h3>
                {editable ? (
                  <button
                    type="button"
                    className="text-xs text-muted-foreground hover:text-foreground hover:underline"
                    onClick={() => toggleModule(codes, allSelected)}
                  >
                    {allSelected ? "Desmarcar todas" : "Marcar todas"}
                  </button>
                ) : null}
              </div>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {(permissions ?? []).map((permission) => (
                  <label key={permission.id} className="flex items-start gap-2 text-sm">
                    <Checkbox
                      className="mt-0.5"
                      checked={selected.has(permission.code)}
                      disabled={!editable}
                      onCheckedChange={() => toggle(permission.code)}
                    />
                    <span className="flex flex-col">
                      <span>{permission.name}</span>
                      <span className="text-xs text-muted-foreground">{permission.code}</span>
                    </span>
                  </label>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

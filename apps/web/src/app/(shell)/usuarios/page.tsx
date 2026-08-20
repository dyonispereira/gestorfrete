"use client";

import * as React from "react";
import { Plus, Users as UsersIcon } from "lucide-react";

import { Button, Input, Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { UserStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useUsersQuery } from "@/modules/identity/hooks/use-users";
import { UsersTable } from "@/modules/identity/components/users-table";
import { UserFormDrawer } from "@/modules/identity/components/user-form-drawer";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const STATUS_OPTIONS: Array<{ value: "all" | UserStatus; label: string }> = [
  { value: "all", label: "Todos os status" },
  { value: "ATIVO", label: "Ativo" },
  { value: "INATIVO", label: "Inativo" },
  { value: "BLOQUEADO", label: "Bloqueado" },
];

export default function UsersPage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [status, setStatus] = React.useState<"all" | UserStatus>("all");
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const usersQuery = useUsersQuery({ page, limit: 20, search, status: status === "all" ? undefined : status });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Usuários</h1>
          <p className="text-sm text-muted-foreground">Contas de acesso do tenant.</p>
        </div>
        {hasPermission("identity_access.user.create") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Novo usuário
          </Button>
        ) : null}
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          placeholder="Buscar por nome ou e-mail…"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPage(1);
          }}
          className="sm:max-w-xs"
        />
        <Select
          value={status}
          onValueChange={(value) => {
            setStatus(value as "all" | UserStatus);
            setPage(1);
          }}
        >
          <SelectTrigger className="sm:w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUS_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {usersQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : usersQuery.error ? (
        <ErrorState
          title="Não foi possível carregar os usuários"
          description={usersQuery.error instanceof Error ? usersQuery.error.message : undefined}
          onRetry={() => usersQuery.refetch()}
        />
      ) : usersQuery.data && usersQuery.data.data.length > 0 ? (
        <>
          <UsersTable users={usersQuery.data.data} />
          <Pagination
            page={usersQuery.data.meta.pagination.page}
            limit={usersQuery.data.meta.pagination.limit}
            total={usersQuery.data.meta.pagination.total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={UsersIcon} title="Nenhum usuário encontrado" description="Ajuste a busca/filtro ou crie o primeiro usuário." />
      )}

      <UserFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}

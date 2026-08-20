"use client";

import * as React from "react";
import { Plus, Users as UsersIcon } from "lucide-react";

import { Button, Input, Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { ClientStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useClientsQuery } from "@/modules/crm/hooks/use-clients";
import { ClientsTable } from "@/modules/crm/components/clients-table";
import { ClientFormDrawer } from "@/modules/crm/components/client-form-drawer";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const STATUS_OPTIONS: Array<{ value: "all" | ClientStatus; label: string }> = [
  { value: "all", label: "Todos os status" },
  { value: "ATIVO", label: "Ativo" },
  { value: "INATIVO", label: "Inativo" },
];

export default function ClientsPage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [status, setStatus] = React.useState<"all" | ClientStatus>("all");
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const clientsQuery = useClientsQuery({ page, limit: 20, search, status: status === "all" ? undefined : status });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Clientes</h1>
          <p className="text-sm text-muted-foreground">Clientes da transportadora.</p>
        </div>
        {hasPermission("crm.client.create") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Novo cliente
          </Button>
        ) : null}
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          placeholder="Buscar por razão social ou documento…"
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
            setStatus(value as "all" | ClientStatus);
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

      {clientsQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : clientsQuery.error ? (
        <ErrorState
          title="Não foi possível carregar os clientes"
          description={clientsQuery.error instanceof Error ? clientsQuery.error.message : undefined}
          onRetry={() => clientsQuery.refetch()}
        />
      ) : clientsQuery.data && clientsQuery.data.data.length > 0 ? (
        <>
          <ClientsTable clients={clientsQuery.data.data} />
          <Pagination
            page={clientsQuery.data.meta.pagination.page}
            limit={clientsQuery.data.meta.pagination.limit}
            total={clientsQuery.data.meta.pagination.total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={UsersIcon} title="Nenhum cliente encontrado" description="Ajuste a busca/filtro ou crie o primeiro cliente." />
      )}

      <ClientFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}

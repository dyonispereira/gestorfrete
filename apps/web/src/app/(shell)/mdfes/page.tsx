"use client";

import * as React from "react";
import { FileStack, Plus } from "lucide-react";

import { Button, Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { MdfeStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useMdfesQuery } from "@/modules/documents/hooks/use-mdfes";
import { MdfesTable } from "@/modules/documents/components/mdfes-table";
import { MdfeFormDrawer } from "@/modules/documents/components/mdfe-form-drawer";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const STATUS_OPTIONS: Array<{ value: "all" | MdfeStatus; label: string }> = [
  { value: "all", label: "Todos os status" },
  { value: "PENDENTE", label: "Pendente" },
  { value: "AUTORIZADO", label: "Autorizado" },
  { value: "ENCERRADO", label: "Encerrado" },
  { value: "CANCELADO", label: "Cancelado" },
];

export default function MdfesPage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [status, setStatus] = React.useState<"all" | MdfeStatus>("all");
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const mdfesQuery = useMdfesQuery({ page, limit: 20, status: status === "all" ? undefined : status });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">MDF-e</h1>
          <p className="text-sm text-muted-foreground">Manifestos consolidando CT-e Autorizados de uma viagem.</p>
        </div>
        {hasPermission("documents.mdfe.issue") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Novo MDF-e
          </Button>
        ) : null}
      </div>

      <Select
        value={status}
        onValueChange={(value) => {
          setStatus(value as "all" | MdfeStatus);
          setPage(1);
        }}
      >
        <SelectTrigger className="sm:w-56">
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

      {mdfesQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : mdfesQuery.error ? (
        <ErrorState
          title="Não foi possível carregar os MDF-e"
          description={mdfesQuery.error instanceof Error ? mdfesQuery.error.message : undefined}
          onRetry={() => mdfesQuery.refetch()}
        />
      ) : mdfesQuery.data && mdfesQuery.data.data.length > 0 ? (
        <>
          <MdfesTable mdfes={mdfesQuery.data.data} />
          <Pagination
            page={mdfesQuery.data.meta.pagination.page}
            limit={mdfesQuery.data.meta.pagination.limit}
            total={mdfesQuery.data.meta.pagination.total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={FileStack} title="Nenhum MDF-e encontrado" description="Ajuste o filtro ou crie o primeiro MDF-e." />
      )}

      <MdfeFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}

"use client";

import * as React from "react";
import { Plus, Route } from "lucide-react";

import { Button, Input, Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { TripOperationalStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useTripsQuery } from "@/modules/freight/hooks/use-trips";
import { TripFormDrawer } from "@/modules/freight/components/trip-form-drawer";
import { TripsTable } from "@/modules/freight/components/trips-table";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const STATUS_OPTIONS: Array<{ value: "all" | TripOperationalStatus; label: string }> = [
  { value: "all", label: "Todos os status" },
  { value: "RASCUNHO", label: "Rascunho" },
  { value: "PLANEJADA", label: "Planejada" },
  { value: "AGUARDANDO_CHECKLIST", label: "Aguardando checklist" },
  { value: "LIBERADA", label: "Liberada" },
  { value: "EM_DESLOCAMENTO", label: "Em deslocamento" },
  { value: "CARREGANDO", label: "Carregando" },
  { value: "EM_TRANSITO", label: "Em trânsito" },
  { value: "EM_ENTREGA", label: "Em entrega" },
  { value: "FINALIZADA", label: "Finalizada" },
  { value: "INTERROMPIDA", label: "Interrompida" },
  { value: "CANCELADA", label: "Cancelada" },
];

/**
 * Não existe um endpoint dedicado de "Painel de Viagens Ativas" (`PRODUCT_MAP.md`) — esta lista,
 * com o filtro de status operacional, é quem cobre esse item do V1: filtrar por um status ativo
 * (ex. "Em trânsito") já é o painel, sem inventar uma tela/endpoint que não existe no Backend.
 */
export default function TripsPage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [codigo, setCodigo] = React.useState("");
  const [status, setStatus] = React.useState<"all" | TripOperationalStatus>("all");
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const tripsQuery = useTripsQuery({
    page,
    limit: 20,
    codigo: codigo || undefined,
    status_operacional: status === "all" ? undefined : status,
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Viagens</h1>
          <p className="text-sm text-muted-foreground">Viagens, entregas, ocorrências e recursos alocados.</p>
        </div>
        {hasPermission("freight.trip.create") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Nova viagem
          </Button>
        ) : null}
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          placeholder="Buscar por código…"
          value={codigo}
          onChange={(event) => {
            setCodigo(event.target.value);
            setPage(1);
          }}
          className="sm:max-w-xs"
        />
        <Select
          value={status}
          onValueChange={(value) => {
            setStatus(value as "all" | TripOperationalStatus);
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
      </div>

      {tripsQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : tripsQuery.error ? (
        <ErrorState
          title="Não foi possível carregar as viagens"
          description={tripsQuery.error instanceof Error ? tripsQuery.error.message : undefined}
          onRetry={() => tripsQuery.refetch()}
        />
      ) : tripsQuery.data && tripsQuery.data.data.length > 0 ? (
        <>
          <TripsTable trips={tripsQuery.data.data} />
          <Pagination
            page={tripsQuery.data.meta.pagination.page}
            limit={tripsQuery.data.meta.pagination.limit}
            total={tripsQuery.data.meta.pagination.total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={Route} title="Nenhuma viagem encontrada" description="Ajuste a busca/filtro ou crie a primeira viagem." />
      )}

      <TripFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}

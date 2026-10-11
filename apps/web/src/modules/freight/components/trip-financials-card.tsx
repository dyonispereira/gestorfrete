"use client";

import * as React from "react";

import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, toast } from "@gestorfrete/ui";
import type { Trip } from "@gestorfrete/types";

import { useTripFinancialsQuery } from "@/modules/freight/hooks/use-trip-financials";
import { useRemovePriceTableApplicationMutation } from "@/modules/freight/hooks/use-trips";
import { ApplyPriceTableDrawer } from "@/modules/freight/components/apply-price-table-drawer";
import { ApiError } from "@/shared/lib/api-client";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

function formatMoney(value: string | undefined): string {
  if (value === undefined) return "—";
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

/**
 * D389 — cada grupo de campo (previsto/realizado/margem) vem `null` quando o ator não tem a
 * permissão correspondente (`financial.trip_predicted_value.view` / `_actual_value.view` /
 * `_margin.view`), nunca um `403` parcial. `null` é renderizado como "—", não como erro.
 *
 * Lote 2 (`GESTORFRETE — PROMPT MESTRE`) — "frete de compra previsto" e "impostos estimados"
 * nunca aparecem como R$ 0,00: esses motores (Acerto de Transportadores/Lote 5, Motor Tributário/
 * Lote 9) ainda não existem, então o valor desconhecido é rotulado explicitamente como tal, nunca
 * confundido com um zero confirmado.
 */
export function TripFinancialsCard({ trip, canEdit }: { trip: Trip; canEdit: boolean }) {
  const [applyDrawerOpen, setApplyDrawerOpen] = React.useState(false);
  const financialsQuery = useTripFinancialsQuery(trip.id);
  const removeApplication = useRemovePriceTableApplicationMutation();

  async function handleRemove() {
    try {
      await removeApplication.mutateAsync({ tripId: trip.id, variables: undefined });
      toast.success("Aplicação de Tabela de Frete removida.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível remover a aplicação.");
    }
  }

  if (financialsQuery.isLoading) return <LoadingState rows={3} />;
  if (financialsQuery.error)
    return (
      <ErrorState
        title="Não foi possível carregar o financeiro da viagem"
        description="Verifique se você tem permissão para visualizar algum grupo de valor financeiro."
        onRetry={() => financialsQuery.refetch()}
      />
    );

  const financials = financialsQuery.data;
  if (!financials) return null;

  const hasApplication = Boolean(trip.snapshots.applied_price_table_application_id);

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader className="flex flex-row items-start justify-between">
          <div>
            <CardTitle>Tabela de frete aplicada</CardTitle>
            <CardDescription>Define o frete de venda previsto — valor congelado na aplicação.</CardDescription>
          </div>
          {canEdit ? (
            hasApplication ? (
              <Button size="sm" variant="outline" onClick={handleRemove} disabled={removeApplication.isPending}>
                {removeApplication.isPending ? "Removendo…" : "Remover aplicação"}
              </Button>
            ) : (
              <Button size="sm" onClick={() => setApplyDrawerOpen(true)}>
                Aplicar tabela de frete
              </Button>
            )
          ) : null}
        </CardHeader>
        {!hasApplication ? (
          <CardContent className="text-sm text-muted-foreground">Nenhuma tabela de frete aplicada ainda.</CardContent>
        ) : null}
      </Card>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Previsto</CardTitle>
            <CardDescription>Congelado na programação da viagem.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-2 text-sm">
            <Row label="Frete de venda previsto" value={formatMoney(financials.predicted_revenue)} />
            <Row
              label="Frete de compra previsto"
              value="Não disponível — Acerto de Transportadores ainda não implementado"
              muted
            />
            <Row label="Custo previsto" value={formatMoney(financials.predicted_cost)} />
            <Row
              label="Impostos estimados"
              value="Não disponível — motor tributário ainda não implementado"
              muted
            />
            <Row label="Margem prevista" value={formatMoney(financials.predicted_margin)} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Realizado</CardTitle>
            <CardDescription>Atualizado por eventos de outros módulos (nunca editável aqui).</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-2 text-sm">
            <Row label="Receita realizada" value={formatMoney(financials.actual_revenue)} />
            <Row label="Custo realizado" value={formatMoney(financials.actual_cost)} />
            <Row label="Margem realizada" value={formatMoney(financials.actual_margin)} />
            <Row label="Desvio financeiro" value={formatMoney(financials.financial_deviation)} />
          </CardContent>
        </Card>
      </div>

      <ApplyPriceTableDrawer open={applyDrawerOpen} onOpenChange={setApplyDrawerOpen} tripId={trip.id} />
    </div>
  );
}

function Row({ label, value, muted }: { label: string; value: string; muted?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-muted-foreground">{label}</span>
      <span className={muted ? "text-xs italic text-muted-foreground" : "font-medium"}>{value}</span>
    </div>
  );
}

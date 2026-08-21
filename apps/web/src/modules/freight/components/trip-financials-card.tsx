"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@gestorfrete/ui";

import { useTripFinancialsQuery } from "@/modules/freight/hooks/use-trip-financials";
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
 */
export function TripFinancialsCard({ tripId }: { tripId: string }) {
  const financialsQuery = useTripFinancialsQuery(tripId);

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

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Previsto</CardTitle>
          <CardDescription>Congelado na programação da viagem.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 text-sm">
          <Row label="Receita prevista" value={formatMoney(financials.predicted_revenue)} />
          <Row label="Custo previsto" value={formatMoney(financials.predicted_cost)} />
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
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

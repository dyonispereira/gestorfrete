"use client";

import { useParams } from "next/navigation";

import { Badge, Card, CardContent, CardHeader, CardTitle, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";

import { useDriverResultDetailQuery } from "@/modules/analytics/hooks/use-management-results";
import { ResultSummaryCards } from "@/modules/analytics/components/result-summary-cards";
import { TripResultsTable } from "@/modules/analytics/components/trip-results-table";
import { formatMoney } from "@/modules/analytics/lib/format";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

const ORIGIN_LABEL: Record<string, string> = {
  ABASTECIMENTO: "Abastecimento",
  COMPRA: "Compra",
  AJUSTE_MANUAL: "Ajuste Manual",
};

/** Drill-down do Motorista — regra explícita do usuário: nunca herda automaticamente todo custo do
 * Veículo. `trips` mostra as Viagens que compõem o Custo Viagens; `linked_costs` mostra só o que foi
 * explicitamente lançado contra ele — os dois nunca se confundem. */
export default function DriverResultDetailPage() {
  const params = useParams<{ id: string }>();
  const query = useDriverResultDetailQuery(params.id, {});
  useBreadcrumbLabel(`/resultados/motoristas/${params.id}`, query.data?.result.name);

  if (query.isLoading) return <LoadingState rows={6} />;
  if (query.error || !query.data)
    return <ErrorState title="Não foi possível carregar o resultado do Motorista" onRetry={() => query.refetch()} />;

  const { result, trips, linked_costs: linkedCosts } = query.data;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">{result.name}</h1>
      </div>

      <ResultSummaryCards totals={result.totals} />

      <Card>
        <CardHeader>
          <CardTitle>Composição do custo</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 text-sm">
          <div className="flex items-center justify-between gap-2">
            <span className="text-muted-foreground">Custo das Viagens executadas</span>
            <span className="font-medium">{formatMoney(result.trip_cost_realized)}</span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="text-muted-foreground">Custo explicitamente vinculado (nunca herdado do Veículo)</span>
            <span className="font-medium">{formatMoney(result.linked_cost_realized)}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Viagens</CardTitle>
        </CardHeader>
        <CardContent>
          <TripResultsTable trips={trips} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Custos vinculados</CardTitle>
        </CardHeader>
        <CardContent>
          {linkedCosts.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nenhum lançamento explicitamente vinculado a este Motorista.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Origem</TableHead>
                  <TableHead>Competência</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Valor</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {linkedCosts.map((cost) => (
                  <TableRow key={cost.accounts_payable_id}>
                    <TableCell>{ORIGIN_LABEL[cost.origin] ?? cost.origin}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(cost.accounting_period).toLocaleDateString("pt-BR")}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{cost.status}</Badge>
                    </TableCell>
                    <TableCell className="text-right font-medium">{formatMoney(cost.value)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

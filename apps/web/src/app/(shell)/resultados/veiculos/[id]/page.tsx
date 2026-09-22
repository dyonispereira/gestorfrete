"use client";

import { useParams } from "next/navigation";
import Link from "next/link";

import { Badge, Card, CardContent, CardHeader, CardTitle, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";

import { useVehicleResultDetailQuery } from "@/modules/analytics/hooks/use-management-results";
import { ResultSummaryCards } from "@/modules/analytics/components/result-summary-cards";
import { TripResultsTable } from "@/modules/analytics/components/trip-results-table";
import { formatMoney } from "@/modules/analytics/lib/format";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

const ORIGIN_LABEL: Record<string, string> = {
  ORDEM_SERVICO: "Manutenção (OS)",
  ABASTECIMENTO: "Abastecimento",
  COMPRA: "Compra",
  AJUSTE_MANUAL: "Ajuste Manual",
};

/** Drill-down "Veículo → resultado → viagens → custos → OS/CP de origem" (pedido explícito do
 * usuário) — cada real de Manutenção/Outros Custos é rastreável até a Conta a Pagar de origem. */
export default function VehicleResultDetailPage() {
  const params = useParams<{ id: string }>();
  const query = useVehicleResultDetailQuery(params.id, {});
  useBreadcrumbLabel(`/resultados/veiculos/${params.id}`, query.data?.result.plate);

  if (query.isLoading) return <LoadingState rows={6} />;
  if (query.error || !query.data)
    return <ErrorState title="Não foi possível carregar o resultado do Veículo" onRetry={() => query.refetch()} />;

  const { result, trips, cost_origins: costOrigins } = query.data;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">{result.plate}</h1>
        <p className="text-sm text-muted-foreground">{result.model}</p>
      </div>

      <ResultSummaryCards totals={result.totals} />

      <Card>
        <CardHeader>
          <CardTitle>Resultado Operacional de Viagens × Resultado Total</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 text-sm">
          <div className="flex items-center justify-between gap-2">
            <span className="text-muted-foreground">Resultado Operacional de Viagens (sem custo fora de viagem)</span>
            <span className="font-medium">{formatMoney(result.operational_result)}</span>
          </div>
          <div className="flex items-center justify-between gap-2 border-t border-border pt-2">
            <span className="text-muted-foreground">Manutenção Realizada</span>
            <span className="font-medium">{formatMoney(result.maintenance_cost_realized)}</span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="text-muted-foreground">Outros Custos Realizados</span>
            <span className="font-medium">{formatMoney(result.other_costs_realized)}</span>
          </div>
          <div className="flex items-center justify-between gap-2 border-t border-border pt-2 text-base">
            <span className="font-semibold text-foreground">Resultado Total do Veículo</span>
            <span className={`font-semibold ${Number(result.totals.realized_margin) < 0 ? "text-destructive" : "text-foreground"}`}>
              {formatMoney(result.totals.realized_margin)}
            </span>
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
          <CardTitle>Custos fora de Viagem — origem</CardTitle>
        </CardHeader>
        <CardContent>
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
              {costOrigins.map((origin) => (
                <TableRow key={origin.accounts_payable_id}>
                  <TableCell>
                    {origin.maintenance_order_id ? (
                      <Link href={`/ordens-servico/${origin.maintenance_order_id}`} className="text-primary hover:underline">
                        {ORIGIN_LABEL[origin.origin] ?? origin.origin}
                      </Link>
                    ) : (
                      ORIGIN_LABEL[origin.origin] ?? origin.origin
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {new Date(origin.accounting_period).toLocaleDateString("pt-BR")}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{origin.status}</Badge>
                  </TableCell>
                  <TableCell className="text-right font-medium">{formatMoney(origin.value)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

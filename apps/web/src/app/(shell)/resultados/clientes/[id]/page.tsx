"use client";

import { useParams } from "next/navigation";
import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { InvoiceStatus } from "@gestorfrete/types";

import { useClientResultDetailQuery } from "@/modules/analytics/hooks/use-management-results";
import { ResultSummaryCards } from "@/modules/analytics/components/result-summary-cards";
import { TripResultsTable } from "@/modules/analytics/components/trip-results-table";
import { InvoiceStatusBadge } from "@/modules/financial/components/invoice-status-badge";
import { formatMoney } from "@/modules/analytics/lib/format";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

/** Drill-down "Cliente → resultado → Faturas → Viagens → CT-es" (pedido explícito do usuário) —
 * `Custo` aqui é só o custo operacional de Viagem do Cliente, nunca Manutenção/frota (gap
 * registrado em docs/domain/012-resultado-gerencial.md). */
export default function ClientResultDetailPage() {
  const params = useParams<{ id: string }>();
  const query = useClientResultDetailQuery(params.id, {});
  useBreadcrumbLabel(`/resultados/clientes/${params.id}`, query.data?.result.name);

  if (query.isLoading) return <LoadingState rows={6} />;
  if (query.error || !query.data)
    return <ErrorState title="Não foi possível carregar o resultado do Cliente" onRetry={() => query.refetch()} />;

  const { result, trips, invoices } = query.data;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">{result.name}</h1>
        {result.trade_name ? <p className="text-sm text-muted-foreground">{result.trade_name}</p> : null}
      </div>

      <ResultSummaryCards totals={result.totals} />

      <Card>
        <CardHeader>
          <CardTitle>Faturas</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Número</TableHead>
                <TableHead>Emissão</TableHead>
                <TableHead>Viagens</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Valor total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {invoices.map((invoice) => (
                <TableRow key={invoice.invoice_id}>
                  <TableCell className="font-medium">
                    <Link href={`/faturas/${invoice.invoice_id}`} className="text-primary hover:underline">
                      {invoice.invoice_number}
                    </Link>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {new Date(invoice.issue_date).toLocaleDateString("pt-BR")}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{invoice.trip_count}</TableCell>
                  <TableCell>
                    <InvoiceStatusBadge status={invoice.status as InvoiceStatus} />
                  </TableCell>
                  <TableCell className="text-right font-medium">{formatMoney(invoice.total_value)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
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
    </div>
  );
}

"use client";

import { GitBranch } from "lucide-react";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { ExpenseAllocationCriterion } from "@gestorfrete/types";

import { useExpenseAllocationsQuery } from "@/modules/financial/hooks/use-accounts-payable";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const CRITERION_LABEL: Record<ExpenseAllocationCriterion, string> = {
  KM_RODADO: "Km rodado",
  NUMERO_VIAGENS: "Número de viagens",
  PESO_TRANSPORTADO: "Peso transportado",
};

function formatMoney(value: string): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

/** Rateio (D393) — a via física que alimenta `Trip.custo_realizado` quando o alvo é uma viagem;
 * quando o alvo é só o Centro de Custo (ex.: OS sem viagem associada), o custo não entra em
 * margem de viagem nenhuma — visível aqui, não escondido. */
export function ExpenseAllocationsTab({ accountsPayableId }: { accountsPayableId: string }) {
  const allocationsQuery = useExpenseAllocationsQuery(accountsPayableId);

  if (allocationsQuery.isLoading) return <LoadingState rows={2} />;
  if (allocationsQuery.error)
    return <ErrorState description="Não foi possível carregar os rateios." onRetry={() => allocationsQuery.refetch()} />;

  const allocations = allocationsQuery.data?.data ?? [];
  if (allocations.length === 0) return <EmptyState icon={GitBranch} title="Nenhum rateio registrado" />;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Alvo</TableHead>
          <TableHead>Critério</TableHead>
          <TableHead>Valor rateado</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {allocations.map((allocation) => (
          <TableRow key={allocation.id}>
            <TableCell className="font-mono text-xs text-muted-foreground">
              {allocation.trip_id ? `Viagem ${allocation.trip_id}` : "Centro de custo (sem viagem)"}
            </TableCell>
            <TableCell className="text-muted-foreground">{CRITERION_LABEL[allocation.criterion]}</TableCell>
            <TableCell className="font-medium">{formatMoney(allocation.allocated_value)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

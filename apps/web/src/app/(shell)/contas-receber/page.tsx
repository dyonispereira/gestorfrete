"use client";

import * as React from "react";
import Link from "next/link";
import { Landmark } from "lucide-react";

import {
  Badge,
  Input,
  Pagination,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@gestorfrete/ui";
import type { ReceivableStatus } from "@gestorfrete/types";

import { useAccountsReceivableGlobalListQuery } from "@/modules/financial/hooks/use-accounts-receivable";
import { useClientsQuery } from "@/modules/crm/hooks/use-clients";
import { ReceivableStatusBadge } from "@/modules/financial/components/receivable-status-badge";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

function formatMoney(value: string): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatCompetencia(value: string): string {
  const [year, month] = value.split("-");
  return `${month}/${year}`;
}

const STATUS_OPTIONS: Array<{ value: "all" | ReceivableStatus; label: string }> = [
  { value: "all", label: "Todos os status" },
  { value: "PENDENTE", label: "Pendente" },
  { value: "VENCIDA", label: "Vencida" },
  { value: "PARCIALMENTE_RECEBIDO", label: "Parcialmente recebida" },
  { value: "RECEBIDA", label: "Recebida" },
  { value: "CONCILIADA", label: "Conciliada" },
];

/**
 * "O que tenho para receber hoje" — consulta agregada entre Faturas (Lote Financeiro, Parte 2.1).
 * Ownership não muda: a baixa em si (Confirmar recebimento) continua só dentro da Fatura — esta
 * tela é puramente de consulta, com link para cada Fatura de origem.
 */
export default function AccountsReceivableGlobalPage() {
  const [page, setPage] = React.useState(1);
  const [status, setStatus] = React.useState<"all" | ReceivableStatus>("all");
  const [clientId, setClientId] = React.useState("all");
  const [accountingPeriodMonth, setAccountingPeriodMonth] = React.useState("");
  const [dueDateGte, setDueDateGte] = React.useState("");
  const [dueDateLte, setDueDateLte] = React.useState("");

  const receivablesQuery = useAccountsReceivableGlobalListQuery({
    page, limit: 20, status: status === "all" ? undefined : status,
    client_id: clientId === "all" ? undefined : clientId,
    accounting_period: accountingPeriodMonth ? `${accountingPeriodMonth}-01` : undefined,
    due_date__gte: dueDateGte || undefined, due_date__lte: dueDateLte || undefined,
  });
  const clientsQuery = useClientsQuery({ limit: 100 });
  const clientNames = new Map((clientsQuery.data?.data ?? []).map((c) => [c.id, c.razao_social]));

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Contas a Receber</h1>
        <p className="text-sm text-muted-foreground">O que há para receber em todas as Faturas, com origem rastreável até cada uma.</p>
      </div>

      <div className="flex flex-wrap gap-3">
        <Select value={status} onValueChange={(v) => { setStatus(v as "all" | ReceivableStatus); setPage(1); }}>
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
        <Select value={clientId} onValueChange={(v) => { setClientId(v); setPage(1); }}>
          <SelectTrigger className="sm:w-56">
            <SelectValue placeholder="Todos os clientes" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os clientes</SelectItem>
            {clientsQuery.data?.data.map((client) => (
              <SelectItem key={client.id} value={client.id}>
                {client.razao_social}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Input
          type="month" className="sm:w-40" aria-label="Competência" value={accountingPeriodMonth}
          onChange={(event) => { setAccountingPeriodMonth(event.target.value); setPage(1); }}
        />
        <Input
          type="date" className="sm:w-44" aria-label="Vencimento de" value={dueDateGte}
          onChange={(event) => { setDueDateGte(event.target.value); setPage(1); }}
        />
        <Input
          type="date" className="sm:w-44" aria-label="Vencimento até" value={dueDateLte}
          onChange={(event) => { setDueDateLte(event.target.value); setPage(1); }}
        />
      </div>

      {receivablesQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : receivablesQuery.error ? (
        <ErrorState
          title="Não foi possível carregar as contas a receber"
          description={receivablesQuery.error instanceof Error ? receivablesQuery.error.message : undefined}
          onRetry={() => receivablesQuery.refetch()}
        />
      ) : receivablesQuery.data && receivablesQuery.data.data.length > 0 ? (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Cliente</TableHead>
                <TableHead>Fatura</TableHead>
                <TableHead>Parcela</TableHead>
                <TableHead>Competência</TableHead>
                <TableHead>Vencimento</TableHead>
                <TableHead>Valor</TableHead>
                <TableHead>Recebido</TableHead>
                <TableHead>Saldo</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {receivablesQuery.data.data.map((receivable) => (
                <TableRow key={receivable.id}>
                  <TableCell className="font-medium">
                    {receivable.client_id ? (clientNames.get(receivable.client_id) ?? "—") : "—"}
                  </TableCell>
                  <TableCell>
                    <Link href={`/faturas/${receivable.invoice_id}`} className="flex items-center gap-2 text-primary hover:underline">
                      <Landmark className="h-4 w-4" />
                      Ver fatura
                    </Link>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{receivable.installment_number}</TableCell>
                  <TableCell className="text-muted-foreground">{formatCompetencia(receivable.accounting_period)}</TableCell>
                  <TableCell className="text-muted-foreground">{new Date(receivable.due_date).toLocaleDateString("pt-BR")}</TableCell>
                  <TableCell className="font-medium">{formatMoney(receivable.value)}</TableCell>
                  <TableCell className="text-emerald-600">{formatMoney(receivable.received_value)}</TableCell>
                  <TableCell className={Number(receivable.open_balance) > 0 ? "font-medium text-amber-600" : "text-muted-foreground"}>
                    {formatMoney(receivable.open_balance)}
                  </TableCell>
                  <TableCell>
                    <ReceivableStatusBadge status={receivable.status} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <Pagination
            page={receivablesQuery.data.meta.pagination.page} limit={receivablesQuery.data.meta.pagination.limit}
            total={receivablesQuery.data.meta.pagination.total} onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={Landmark} title="Nenhuma conta a receber encontrada" description="Ajuste o filtro — nada em aberto por aqui." />
      )}
      <Badge variant="outline" className="w-fit">
        A baixa (Confirmar recebimento) acontece dentro de cada Fatura — clique em &quot;Ver fatura&quot;.
      </Badge>
    </div>
  );
}

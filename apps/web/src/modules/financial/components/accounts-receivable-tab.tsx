"use client";

import * as React from "react";
import { Landmark, Plus } from "lucide-react";

import {
  Button,
  Input,
  Label,
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  toast,
} from "@gestorfrete/ui";
import type { InvoiceStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import {
  useAccountsReceivableForInvoiceQuery,
  useConfirmReceiptAccountsReceivableMutation,
  useCreateAccountsReceivableMutation,
} from "@/modules/financial/hooks/use-accounts-receivable";
import { ApiError } from "@/shared/lib/api-client";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

import { ReceivableStatusBadge } from "./receivable-status-badge";

function formatMoney(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatCompetencia(value: string): string {
  const [year, month] = value.split("-");
  return `${month}/${year}`;
}

function currentMonthCompetencia(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-01`;
}

/**
 * `POST .../commands/confirm-receipt` aceita `received_value` no contrato, mas o handler nunca o
 * lê (`confirm_receipt_accounts_receivable.py` chama `receivable.confirm_receipt(now=now)` sem
 * valor) — uma parcela é sempre baixada pelo valor cheio, nunca parcialmente. Gap registrado, não
 * contornado: nenhum campo de "valor recebido" editável aparece aqui. A baixa **parcial da
 * Fatura** é real e visível — soma das parcelas Recebidas/Conciliadas contra o total faturado.
 */
export function AccountsReceivableTab({ invoiceId, invoiceStatus }: { invoiceId: string; invoiceStatus: InvoiceStatus }) {
  const { hasPermission } = usePermissions();
  const receivablesQuery = useAccountsReceivableForInvoiceQuery(invoiceId);
  const confirmReceipt = useConfirmReceiptAccountsReceivableMutation(invoiceId);
  const createReceivable = useCreateAccountsReceivableMutation(invoiceId);

  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [value, setValue] = React.useState("");
  const [dueDate, setDueDate] = React.useState("");
  const [accountingPeriod, setAccountingPeriod] = React.useState(currentMonthCompetencia());
  const [formError, setFormError] = React.useState<string | null>(null);

  async function handleConfirmReceipt(id: string, installmentValue: string) {
    try {
      await confirmReceipt.mutateAsync({ id, body: { received_value: installmentValue } });
      toast.success("Recebimento confirmado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível confirmar o recebimento.");
    }
  }

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createReceivable.mutateAsync({ value, due_date: dueDate, accounting_period: accountingPeriod });
      toast.success("Parcela adicionada.");
      setValue(""); setDueDate(""); setAccountingPeriod(currentMonthCompetencia());
      setDrawerOpen(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível adicionar a parcela.");
    }
  }

  if (receivablesQuery.isLoading) return <LoadingState rows={3} />;
  if (receivablesQuery.error)
    return <ErrorState description="Não foi possível carregar as contas a receber." onRetry={() => receivablesQuery.refetch()} />;

  const receivables = receivablesQuery.data?.data ?? [];
  const total = receivables.reduce((sum, r) => sum + Number(r.value), 0);
  const received = receivables
    .filter((r) => r.status === "RECEBIDA" || r.status === "CONCILIADA")
    .reduce((sum, r) => sum + Number(r.value), 0);
  const balance = total - received;
  const canCreate = hasPermission("financial.receivable.create") && invoiceStatus === "EMITIDA";
  const canConfirm = hasPermission("financial.receivable.confirm_receipt");

  return (
    <div className="flex flex-col gap-4">
      {receivables.length > 0 ? (
        <div className="flex flex-wrap gap-4 rounded-md border border-border p-4">
          <div>
            <p className="text-xs text-muted-foreground">Faturado</p>
            <p className="text-lg font-semibold">{formatMoney(total)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Recebido</p>
            <p className="text-lg font-semibold text-emerald-600">{formatMoney(received)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Saldo</p>
            <p className={`text-lg font-semibold ${balance > 0 ? "text-amber-600" : ""}`}>{formatMoney(balance)}</p>
          </div>
        </div>
      ) : null}

      {canCreate ? (
        <div className="flex justify-end">
          <Button size="sm" onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Nova parcela
          </Button>
        </div>
      ) : null}

      {receivables.length === 0 ? (
        <EmptyState icon={Landmark} title="Nenhuma conta a receber ainda" />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Parcela</TableHead>
              <TableHead>Competência</TableHead>
              <TableHead>Vencimento</TableHead>
              <TableHead>Valor</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Recebido em</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {receivables.map((receivable) => (
              <TableRow key={receivable.id}>
                <TableCell className="font-medium">{receivable.installment_number}</TableCell>
                <TableCell className="text-muted-foreground">{formatCompetencia(receivable.accounting_period)}</TableCell>
                <TableCell className="text-muted-foreground">{new Date(receivable.due_date).toLocaleDateString("pt-BR")}</TableCell>
                <TableCell className="font-medium">{formatMoney(Number(receivable.value))}</TableCell>
                <TableCell>
                  <ReceivableStatusBadge status={receivable.status} />
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {receivable.received_at ? new Date(receivable.received_at).toLocaleDateString("pt-BR") : "—"}
                </TableCell>
                <TableCell>
                  {(receivable.status === "PENDENTE" || receivable.status === "VENCIDA") && canConfirm ? (
                    <Button
                      size="sm" disabled={confirmReceipt.isPending}
                      onClick={() => handleConfirmReceipt(receivable.id, receivable.value)}
                    >
                      Confirmar recebimento
                    </Button>
                  ) : null}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
        <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Nova parcela</SheetTitle>
            <SheetDescription>Caso raro — a maioria das parcelas nasce junto com a Fatura.</SheetDescription>
          </SheetHeader>
          <form onSubmit={handleCreate} className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="receivable-value">Valor</Label>
              <Input id="receivable-value" type="number" step="0.01" required value={value} onChange={(e) => setValue(e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="receivable-due-date">Vencimento</Label>
              <Input id="receivable-due-date" type="date" required value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="receivable-competencia">Competência</Label>
              <Input
                id="receivable-competencia" type="date" required value={accountingPeriod}
                onChange={(e) => setAccountingPeriod(e.target.value)}
              />
            </div>

            {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

            <div className="mt-auto flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setDrawerOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createReceivable.isPending}>
                {createReceivable.isPending ? "Adicionando…" : "Adicionar parcela"}
              </Button>
            </div>
          </form>
        </SheetContent>
      </Sheet>
    </div>
  );
}

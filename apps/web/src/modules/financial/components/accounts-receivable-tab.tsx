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
import type { AccountsReceivable, InvoiceStatus } from "@gestorfrete/types";

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
 * Baixa parcial real (Lote Financeiro, Parte 2.1) — `receive_payment` no backend valida
 * `0 < valor <= saldo_aberto` e só chega a `RECEBIDA` quando o saldo zera; antes disso,
 * `PARCIALMENTE_RECEBIDO`. O input abaixo replica a mesma validação no cliente (feedback
 * imediato), nunca como substituto da validação real do backend. Chamável de novo enquanto
 * houver saldo — cada clique em "Confirmar recebimento" é uma baixa, não uma operação única.
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

  const [payingReceivable, setPayingReceivable] = React.useState<AccountsReceivable | null>(null);
  const [paymentValue, setPaymentValue] = React.useState("");
  const [paymentError, setPaymentError] = React.useState<string | null>(null);

  function openPaymentDialog(receivable: AccountsReceivable) {
    setPayingReceivable(receivable);
    setPaymentValue(receivable.open_balance);
    setPaymentError(null);
  }

  async function handleConfirmReceipt(event: React.FormEvent) {
    event.preventDefault();
    if (!payingReceivable) return;
    const openBalance = Number(payingReceivable.open_balance);
    const amount = Number(paymentValue);
    if (!(amount > 0) || amount > openBalance) {
      setPaymentError(`O valor da baixa deve ser maior que zero e no máximo o saldo em aberto (${formatMoney(openBalance)}).`);
      return;
    }
    setPaymentError(null);
    try {
      await confirmReceipt.mutateAsync({ id: payingReceivable.id, body: { received_value: paymentValue } });
      toast.success("Recebimento confirmado.");
      setPayingReceivable(null);
    } catch (error) {
      setPaymentError(error instanceof ApiError ? error.message : "Não foi possível confirmar o recebimento.");
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
  const received = receivables.reduce((sum, r) => sum + Number(r.received_value), 0);
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
              <TableHead>Recebido</TableHead>
              <TableHead>Saldo</TableHead>
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
                <TableCell className="text-emerald-600">{formatMoney(Number(receivable.received_value))}</TableCell>
                <TableCell className={Number(receivable.open_balance) > 0 ? "font-medium text-amber-600" : "text-muted-foreground"}>
                  {formatMoney(Number(receivable.open_balance))}
                </TableCell>
                <TableCell>
                  <ReceivableStatusBadge status={receivable.status} />
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {receivable.received_at ? new Date(receivable.received_at).toLocaleDateString("pt-BR") : "—"}
                </TableCell>
                <TableCell>
                  {(receivable.status === "PENDENTE" || receivable.status === "VENCIDA" || receivable.status === "PARCIALMENTE_RECEBIDO")
                  && canConfirm ? (
                    <Button size="sm" onClick={() => openPaymentDialog(receivable)}>
                      Confirmar recebimento
                    </Button>
                  ) : null}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <Sheet open={payingReceivable !== null} onOpenChange={(open) => !open && setPayingReceivable(null)}>
        <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Confirmar recebimento — parcela {payingReceivable?.installment_number}</SheetTitle>
            <SheetDescription>
              Saldo em aberto: {payingReceivable ? formatMoney(Number(payingReceivable.open_balance)) : "—"}. Informe
              qualquer valor até esse saldo — uma baixa parcial deixa o restante em aberto para confirmar depois.
            </SheetDescription>
          </SheetHeader>
          <form onSubmit={handleConfirmReceipt} className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="receivable-payment-value">Valor recebido</Label>
              <Input
                id="receivable-payment-value" type="number" step="0.01" required value={paymentValue}
                onChange={(e) => setPaymentValue(e.target.value)}
              />
            </div>

            {paymentError ? <p className="text-sm text-destructive">{paymentError}</p> : null}

            <div className="mt-auto flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setPayingReceivable(null)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={confirmReceipt.isPending}>
                {confirmReceipt.isPending ? "Confirmando…" : "Confirmar recebimento"}
              </Button>
            </div>
          </form>
        </SheetContent>
      </Sheet>

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

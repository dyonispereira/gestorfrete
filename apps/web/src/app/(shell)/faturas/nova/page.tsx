"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Plus, Trash2 } from "lucide-react";

import {
  Badge,
  Button,
  Checkbox,
  Input,
  Label,
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
  Textarea,
  toast,
} from "@gestorfrete/ui";
import type { InvoiceInstallmentRequest } from "@gestorfrete/types";

import { useClientsQuery } from "@/modules/crm/hooks/use-clients";
import { usePaymentMethodsListQuery } from "@/modules/financial/hooks/use-payment-methods";
import { useCreateInvoiceMutation, useEligibleTripsQuery } from "@/modules/financial/hooks/use-invoices";
import { ApiError } from "@/shared/lib/api-client";
import { EmptyState } from "@/shared/components/states/empty-state";
import { LoadingState } from "@/shared/components/states/loading-state";

function formatMoney(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function currentMonthCompetencia(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-01`;
}

function emptyInstallment(): InvoiceInstallmentRequest {
  return { value: "", due_date: "", accounting_period: currentMonthCompetencia() };
}

/**
 * Lote Financeiro, Parte 3 — Faturamento Agrupado. Cliente → Período → Viagens elegíveis →
 * seleção múltipla → resumo → gerar Fatura. Faturar uma única Viagem é só selecionar uma —
 * mesmo fluxo, mesmo endpoint (D262-style, sem um segundo "faturamento individual" à parte).
 */
export default function NewInvoicePage() {
  const router = useRouter();
  const [clientId, setClientId] = React.useState("");
  const [periodFrom, setPeriodFrom] = React.useState("");
  const [periodTo, setPeriodTo] = React.useState("");
  const [selectedValues, setSelectedValues] = React.useState<Map<string, string>>(new Map());
  const [paymentMethodId, setPaymentMethodId] = React.useState("");
  const [installments, setInstallments] = React.useState<InvoiceInstallmentRequest[]>([emptyInstallment()]);
  const [adjustmentValue, setAdjustmentValue] = React.useState("");
  const [adjustmentReason, setAdjustmentReason] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const clientsQuery = useClientsQuery({ limit: 100, status: "ATIVO" });
  const eligibleTripsQuery = useEligibleTripsQuery(clientId || undefined);
  const paymentMethodsQuery = usePaymentMethodsListQuery({ limit: 100, status: "ATIVA" });
  const createInvoice = useCreateInvoiceMutation();

  const visibleTrips = (eligibleTripsQuery.data ?? []).filter((trip) => {
    if (!trip.scheduled_date) return true;
    if (periodFrom && trip.scheduled_date < periodFrom) return false;
    if (periodTo && trip.scheduled_date > periodTo) return false;
    return true;
  });

  function toggleTrip(tripId: string, suggestedValue: string | undefined, checked: boolean) {
    setSelectedValues((current) => {
      const next = new Map(current);
      if (checked) next.set(tripId, suggestedValue ?? "");
      else next.delete(tripId);
      return next;
    });
  }

  function updateTripValue(tripId: string, value: string) {
    setSelectedValues((current) => new Map(current).set(tripId, value));
  }

  const grossValue = [...selectedValues.values()].reduce((sum, v) => sum + (Number(v) || 0), 0);
  const adjustment = Number(adjustmentValue) || 0;
  const totalValue = grossValue + adjustment;
  const installmentsSum = installments.reduce((sum, i) => sum + (Number(i.value) || 0), 0);

  function updateInstallment(index: number, patch: Partial<InvoiceInstallmentRequest>) {
    setInstallments((current) => current.map((installment, i) => (i === index ? { ...installment, ...patch } : installment)));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    if (selectedValues.size === 0) {
      setFormError("Selecione ao menos uma Viagem — uma Fatura nunca pode ficar vazia.");
      return;
    }
    if (Math.abs(installmentsSum - totalValue) > 0.01) {
      setFormError(
        `A soma das parcelas (${formatMoney(installmentsSum)}) precisa bater com o Total da Fatura (${formatMoney(totalValue)}).`
      );
      return;
    }
    try {
      const invoice = await createInvoice.mutateAsync({
        trips: [...selectedValues.entries()].map(([trip_id, value]) => ({ trip_id, value })),
        client_id: clientId,
        adjustment_value: adjustmentValue || undefined,
        adjustment_reason: adjustment !== 0 ? adjustmentReason : undefined,
        payment_method_id: paymentMethodId,
        installments,
      });
      toast.success("Fatura criada.");
      router.push(`/faturas/${invoice.id}`);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar a fatura.");
    }
  }

  const canSubmit = Boolean(clientId && paymentMethodId && selectedValues.size > 0 && installments.every((i) => i.value && i.due_date));

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Nova Fatura</h1>
        <p className="text-sm text-muted-foreground">Cliente → Período → Viagens elegíveis → seleção → Fatura.</p>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        <div className="flex flex-col gap-6">
          <div className="flex flex-col gap-4 rounded-md border border-border p-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="new-invoice-client">Cliente</Label>
                <Select
                  value={clientId}
                  onValueChange={(v) => { setClientId(v); setSelectedValues(new Map()); }}
                >
                  <SelectTrigger id="new-invoice-client">
                    <SelectValue placeholder="Selecione um cliente" />
                  </SelectTrigger>
                  <SelectContent>
                    {clientsQuery.data?.data.map((client) => (
                      <SelectItem key={client.id} value={client.id}>
                        {client.razao_social}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="new-invoice-period-from">Período de</Label>
                <Input id="new-invoice-period-from" type="date" value={periodFrom} onChange={(e) => setPeriodFrom(e.target.value)} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="new-invoice-period-to">Período até</Label>
                <Input id="new-invoice-period-to" type="date" value={periodTo} onChange={(e) => setPeriodTo(e.target.value)} />
              </div>
            </div>
          </div>

          {!clientId ? (
            <EmptyState title="Selecione um cliente" description="As Viagens elegíveis desse cliente aparecem aqui." />
          ) : eligibleTripsQuery.isLoading ? (
            <LoadingState rows={4} />
          ) : visibleTrips.length === 0 ? (
            <EmptyState
              title="Nenhuma Viagem elegível"
              description="Precisa de Canhoto registrado, CT-e emitido, e não estar em outra Fatura ativa."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10" />
                  <TableHead>Viagem</TableHead>
                  <TableHead>Data</TableHead>
                  <TableHead>Valor faturável</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {visibleTrips.map((trip) => {
                  const selected = selectedValues.has(trip.trip_id);
                  return (
                    <TableRow key={trip.trip_id}>
                      <TableCell>
                        <Checkbox
                          checked={selected}
                          onCheckedChange={(checked) => toggleTrip(trip.trip_id, trip.suggested_value, checked === true)}
                        />
                      </TableCell>
                      <TableCell className="font-medium">{trip.codigo}</TableCell>
                      <TableCell className="text-muted-foreground">
                        {trip.scheduled_date ? new Date(trip.scheduled_date).toLocaleDateString("pt-BR") : "—"}
                      </TableCell>
                      <TableCell>
                        <Input
                          type="number" step="0.01" disabled={!selected}
                          value={selectedValues.get(trip.trip_id) ?? ""}
                          onChange={(e) => updateTripValue(trip.trip_id, e.target.value)}
                          className="w-32"
                        />
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}

          <div className="flex flex-col gap-4 rounded-md border border-border p-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="new-invoice-payment-method">Forma de pagamento</Label>
              <Select value={paymentMethodId} onValueChange={setPaymentMethodId}>
                <SelectTrigger id="new-invoice-payment-method">
                  <SelectValue placeholder="Selecione uma forma de pagamento ativa" />
                </SelectTrigger>
                <SelectContent>
                  {paymentMethodsQuery.data?.data.map((pm) => (
                    <SelectItem key={pm.id} value={pm.id}>
                      {pm.nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="new-invoice-adjustment-value">Ajuste (desconto/acréscimo, opcional)</Label>
                <Input
                  id="new-invoice-adjustment-value" type="number" step="0.01" value={adjustmentValue}
                  onChange={(e) => setAdjustmentValue(e.target.value)} placeholder="Negativo = desconto"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="new-invoice-adjustment-reason">Motivo do ajuste</Label>
                <Textarea
                  id="new-invoice-adjustment-reason" value={adjustmentReason} disabled={adjustment === 0}
                  onChange={(e) => setAdjustmentReason(e.target.value)}
                />
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <Label>Parcelas</Label>
                <Button
                  type="button" variant="outline" size="sm"
                  onClick={() => setInstallments((current) => [...current, emptyInstallment()])}
                >
                  <Plus className="h-4 w-4" />
                  Adicionar parcela
                </Button>
              </div>
              {installments.map((installment, index) => (
                <div key={index} className="grid grid-cols-[1fr_1fr_1fr_auto] items-end gap-2 rounded-md border border-border p-3">
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor={`new-invoice-installment-value-${index}`}>Valor</Label>
                    <Input
                      id={`new-invoice-installment-value-${index}`} type="number" step="0.01" required value={installment.value}
                      onChange={(e) => updateInstallment(index, { value: e.target.value })}
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor={`new-invoice-installment-due-${index}`}>Vencimento</Label>
                    <Input
                      id={`new-invoice-installment-due-${index}`} type="date" required value={installment.due_date}
                      onChange={(e) => updateInstallment(index, { due_date: e.target.value })}
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor={`new-invoice-installment-competencia-${index}`}>Competência</Label>
                    <Input
                      id={`new-invoice-installment-competencia-${index}`} type="date" required value={installment.accounting_period}
                      onChange={(e) => updateInstallment(index, { accounting_period: e.target.value })}
                    />
                  </div>
                  <Button
                    type="button" variant="ghost" size="sm" disabled={installments.length === 1}
                    onClick={() => setInstallments((current) => current.filter((_, i) => i !== index))}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => router.push("/faturas")}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createInvoice.isPending || !canSubmit}>
              {createInvoice.isPending ? "Gerando…" : "Gerar Fatura"}
            </Button>
          </div>
        </div>

        <aside className="flex h-fit flex-col gap-3 rounded-md border border-border p-4">
          <h2 className="font-semibold text-foreground">Resumo</h2>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Viagens selecionadas</span>
            <Badge variant="outline">{selectedValues.size}</Badge>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Valor bruto</span>
            <span className="font-medium">{formatMoney(grossValue)}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Ajuste</span>
            <span className={adjustment < 0 ? "font-medium text-destructive" : "font-medium"}>{formatMoney(adjustment)}</span>
          </div>
          <div className="flex items-center justify-between border-t border-border pt-2 text-base">
            <span className="font-semibold text-foreground">Total da Fatura</span>
            <span className="font-semibold text-foreground">{formatMoney(totalValue)}</span>
          </div>
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Soma das parcelas</span>
            <span>{formatMoney(installmentsSum)}</span>
          </div>
        </aside>
      </form>
    </div>
  );
}

"use client";

import * as React from "react";
import { Plus, Trash2 } from "lucide-react";

import {
  Button,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  toast,
} from "@gestorfrete/ui";
import type { InvoiceInstallmentRequest } from "@gestorfrete/types";

import { useClientsQuery } from "@/modules/crm/hooks/use-clients";
import { useTripsQuery } from "@/modules/freight/hooks/use-trips";
import { useCreateInvoiceMutation } from "@/modules/financial/hooks/use-invoices";
import { ApiError } from "@/shared/lib/api-client";

interface InvoiceFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function currentMonthCompetencia(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-01`;
}

function emptyInstallment(): InvoiceInstallmentRequest {
  return { value: "", due_date: "", accounting_period: currentMonthCompetencia() };
}

function sumInstallments(installments: InvoiceInstallmentRequest[]): number {
  return installments.reduce((sum, i) => sum + (Number(i.value) || 0), 0);
}

/**
 * `payment_method_id` não tem endpoint de listagem (D386 — sem router próprio, mesmo padrão de
 * `Categoria de Veículo`/D363) — campo de ID cru, com rótulo explícito, não uma invenção de
 * dropdown fake. O valor total da Fatura é sempre a soma das parcelas, calculado aqui — o backend
 * não valida essa soma sozinho (gap registrado), então o frontend nunca deixa os dois divergirem.
 */
export function InvoiceFormDrawer({ open, onOpenChange }: InvoiceFormDrawerProps) {
  const [clientId, setClientId] = React.useState("");
  const [tripId, setTripId] = React.useState("");
  const [paymentMethodId, setPaymentMethodId] = React.useState("");
  const [installments, setInstallments] = React.useState<InvoiceInstallmentRequest[]>([emptyInstallment()]);
  const [formError, setFormError] = React.useState<string | null>(null);

  const clientsQuery = useClientsQuery({ limit: 100 });
  const tripsQuery = useTripsQuery({ limit: 50 });
  const createInvoice = useCreateInvoiceMutation();

  const totalValue = sumInstallments(installments);

  function reset() {
    setClientId(""); setTripId(""); setPaymentMethodId(""); setInstallments([emptyInstallment()]); setFormError(null);
  }

  function updateInstallment(index: number, patch: Partial<InvoiceInstallmentRequest>) {
    setInstallments((current) => current.map((installment, i) => (i === index ? { ...installment, ...patch } : installment)));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createInvoice.mutateAsync({
        client_id: clientId, trip_id: tripId || undefined, payment_method_id: paymentMethodId,
        total_value: totalValue.toFixed(2), installments,
      });
      toast.success("Fatura criada.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar a fatura.");
    }
  }

  const canSubmit = Boolean(clientId && paymentMethodId && totalValue > 0 && installments.every((i) => i.value && i.due_date));

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>Nova fatura</SheetTitle>
          <SheetDescription>Exige Canhoto registrado e CT-e emitido para a viagem selecionada.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="invoice-client">Cliente</Label>
            <Select value={clientId} onValueChange={setClientId}>
              <SelectTrigger id="invoice-client">
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
            <Label htmlFor="invoice-trip">Viagem</Label>
            <Select value={tripId} onValueChange={setTripId}>
              <SelectTrigger id="invoice-trip">
                <SelectValue placeholder="Selecione a viagem elegível" />
              </SelectTrigger>
              <SelectContent>
                {tripsQuery.data?.data.map((trip) => (
                  <SelectItem key={trip.id} value={trip.id}>
                    {trip.codigo}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="invoice-payment-method">ID da forma de pagamento</Label>
            <Input
              id="invoice-payment-method" required value={paymentMethodId}
              onChange={(e) => setPaymentMethodId(e.target.value)}
              placeholder="Sem tela de cadastro ainda — cole o ID"
            />
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
                  <Label htmlFor={`installment-value-${index}`}>Valor</Label>
                  <Input
                    id={`installment-value-${index}`} type="number" step="0.01" required value={installment.value}
                    onChange={(e) => updateInstallment(index, { value: e.target.value })}
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor={`installment-due-${index}`}>Vencimento</Label>
                  <Input
                    id={`installment-due-${index}`} type="date" required value={installment.due_date}
                    onChange={(e) => updateInstallment(index, { due_date: e.target.value })}
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor={`installment-competencia-${index}`}>Competência</Label>
                  <Input
                    id={`installment-competencia-${index}`} type="date" required value={installment.accounting_period}
                    onChange={(e) => updateInstallment(index, { accounting_period: e.target.value })}
                  />
                </div>
                <Button
                  type="button" variant="ghost" size="sm"
                  disabled={installments.length === 1}
                  onClick={() => setInstallments((current) => current.filter((_, i) => i !== index))}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
            <p className="text-sm text-muted-foreground">
              Valor total: {totalValue.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}
            </p>
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createInvoice.isPending || !canSubmit}>
              {createInvoice.isPending ? "Criando…" : "Criar fatura"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

"use client";

import * as React from "react";

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
  Textarea,
  toast,
} from "@gestorfrete/ui";

import { useCreateFinancialReversalMutation } from "@/modules/financial/hooks/use-financial-reversals";
import { ApiError } from "@/shared/lib/api-client";

type TargetType = "invoice" | "accounts_payable" | "accounts_receivable";

const TARGET_LABEL: Record<TargetType, string> = {
  invoice: "Fatura",
  accounts_payable: "Conta a Pagar",
  accounts_receivable: "Conta a Receber",
};

/** Estorno nunca reverte o status do alvo (D266/D273) — é um registro paralelo e imutável. Sem
 * picker de alvo por tipo (nenhuma tela hoje lista "Contas a Receber avulsas" para escolher, ver
 * `accounts-receivable-tab.tsx`) — o ID é colado a partir da tela do lançamento original. */
export function FinancialReversalFormDrawer({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const [targetType, setTargetType] = React.useState<TargetType>("accounts_payable");
  const [targetId, setTargetId] = React.useState("");
  const [value, setValue] = React.useState("");
  const [reason, setReason] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const createReversal = useCreateFinancialReversalMutation();

  function reset() {
    setTargetType("accounts_payable"); setTargetId(""); setValue(""); setReason(""); setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createReversal.mutateAsync({
        invoice_id: targetType === "invoice" ? targetId : undefined,
        accounts_payable_id: targetType === "accounts_payable" ? targetId : undefined,
        accounts_receivable_id: targetType === "accounts_receivable" ? targetId : undefined,
        value, reason,
      });
      toast.success("Estorno registrado.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível registrar o estorno.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Novo estorno financeiro</SheetTitle>
          <SheetDescription>
            Nunca altera o status do lançamento original — fica registrado como uma trilha separada, sempre auditável.
          </SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="reversal-target-type">Tipo de lançamento</Label>
            <Select value={targetType} onValueChange={(v) => setTargetType(v as TargetType)}>
              <SelectTrigger id="reversal-target-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(TARGET_LABEL) as TargetType[]).map((value) => (
                  <SelectItem key={value} value={value}>
                    {TARGET_LABEL[value]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="reversal-target-id">ID do lançamento</Label>
            <Input id="reversal-target-id" required value={targetId} onChange={(e) => setTargetId(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="reversal-value">Valor estornado</Label>
            <Input id="reversal-value" type="number" step="0.01" required value={value} onChange={(e) => setValue(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="reversal-reason">Motivo</Label>
            <Textarea id="reversal-reason" required value={reason} onChange={(e) => setReason(e.target.value)} />
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createReversal.isPending}>
              {createReversal.isPending ? "Registrando…" : "Registrar estorno"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

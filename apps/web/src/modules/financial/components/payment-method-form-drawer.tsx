"use client";

import * as React from "react";

import { Button, Input, Label, Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, toast } from "@gestorfrete/ui";

import { useCreatePaymentMethodMutation } from "@/modules/financial/hooks/use-payment-methods";
import { ApiError } from "@/shared/lib/api-client";

interface PaymentMethodFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function PaymentMethodFormDrawer({ open, onOpenChange }: PaymentMethodFormDrawerProps) {
  const [nome, setNome] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const createPaymentMethod = useCreatePaymentMethodMutation();

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createPaymentMethod.mutateAsync({ nome });
      toast.success("Forma de pagamento criada.");
      setNome("");
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar a forma de pagamento.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Nova forma de pagamento</SheetTitle>
          <SheetDescription>Ex.: PIX, Boleto, Cartão de crédito.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="payment-method-nome">Nome</Label>
            <Input id="payment-method-nome" required value={nome} onChange={(event) => setNome(event.target.value)} />
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createPaymentMethod.isPending}>
              {createPaymentMethod.isPending ? "Criando…" : "Criar forma de pagamento"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

"use client";

import * as React from "react";

import { Button, Input, Label, Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, toast } from "@gestorfrete/ui";

import { useCreateDeliveryMutation } from "@/modules/freight/hooks/use-deliveries";
import { ApiError } from "@/shared/lib/api-client";

interface DeliveryFormDrawerProps {
  tripId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** Create-only — `order` deve ser único na viagem (409 `FREIGHT_DELIVERY_ORDER_ALREADY_EXISTS`). */
export function DeliveryFormDrawer({ tripId, open, onOpenChange }: DeliveryFormDrawerProps) {
  const [order, setOrder] = React.useState("");
  const [recipient, setRecipient] = React.useState("");
  const [logradouro, setLogradouro] = React.useState("");
  const [cidade, setCidade] = React.useState("");
  const [uf, setUf] = React.useState("");
  const [cep, setCep] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const createDelivery = useCreateDeliveryMutation(tripId);

  function reset() {
    setOrder("");
    setRecipient("");
    setLogradouro("");
    setCidade("");
    setUf("");
    setCep("");
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createDelivery.mutateAsync({
        order: Number(order),
        recipient,
        delivery_address: { logradouro, cidade, uf, cep },
      });
      toast.success("Entrega criada.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar a entrega.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Nova entrega</SheetTitle>
          <SheetDescription>A ordem precisa ser única entre as entregas desta viagem.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="delivery-order">Ordem</Label>
              <Input id="delivery-order" type="number" required value={order} onChange={(event) => setOrder(event.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="delivery-recipient">Destinatário</Label>
              <Input id="delivery-recipient" required value={recipient} onChange={(event) => setRecipient(event.target.value)} />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="delivery-logradouro">Logradouro</Label>
            <Input id="delivery-logradouro" required value={logradouro} onChange={(event) => setLogradouro(event.target.value)} />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="delivery-cidade">Cidade</Label>
              <Input id="delivery-cidade" required value={cidade} onChange={(event) => setCidade(event.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="delivery-uf">UF</Label>
              <Input id="delivery-uf" required maxLength={2} value={uf} onChange={(event) => setUf(event.target.value.toUpperCase())} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="delivery-cep">CEP</Label>
              <Input id="delivery-cep" required value={cep} onChange={(event) => setCep(event.target.value)} />
            </div>
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createDelivery.isPending}>
              {createDelivery.isPending ? "Criando…" : "Criar entrega"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

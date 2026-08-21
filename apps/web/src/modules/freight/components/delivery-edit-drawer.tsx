"use client";

import * as React from "react";

import {
  Button,
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
import type { Delivery, DeliveryStatus } from "@gestorfrete/types";

import { useUpdateDeliveryMutation } from "@/modules/freight/hooks/use-deliveries";
import { ApiError } from "@/shared/lib/api-client";

const STATUS_OPTIONS: Array<{ value: DeliveryStatus; label: string }> = [
  { value: "PENDENTE", label: "Pendente" },
  { value: "CONCLUIDA", label: "Concluída" },
  { value: "RECUSADA", label: "Recusada" },
  { value: "DEVOLVIDA", label: "Devolvida" },
  { value: "CANCELADA", label: "Cancelada" },
];

interface DeliveryEditDrawerProps {
  tripId: string;
  delivery: Delivery | null;
  onOpenChange: (open: boolean) => void;
}

/**
 * A única sub-entidade de Operação com `status` editável por PATCH direto (D233 é regra só de
 * Viagem). `RECUSADA` exige `rejection_reason` — validado no Backend (422 se ausente); replicado
 * aqui como validação de UI para feedback imediato, não como substituto da validação real.
 */
export function DeliveryEditDrawer({ tripId, delivery, onOpenChange }: DeliveryEditDrawerProps) {
  const [status, setStatus] = React.useState<DeliveryStatus>("PENDENTE");
  const [rejectionReason, setRejectionReason] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const updateDelivery = useUpdateDeliveryMutation(tripId);

  React.useEffect(() => {
    if (delivery) {
      setStatus(delivery.status);
      setRejectionReason(delivery.rejection_reason ?? "");
      setFormError(null);
    }
  }, [delivery]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!delivery) return;
    if (status === "RECUSADA" && !rejectionReason.trim()) {
      setFormError("Motivo da recusa é obrigatório quando o status é Recusada.");
      return;
    }
    setFormError(null);
    try {
      await updateDelivery.mutateAsync({
        deliveryId: delivery.id,
        body: { status, rejection_reason: status === "RECUSADA" ? rejectionReason : undefined },
      });
      toast.success("Entrega atualizada.");
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível atualizar a entrega.");
    }
  }

  return (
    <Sheet open={delivery !== null} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Entrega #{delivery?.order}</SheetTitle>
          <SheetDescription>Alterar o status da entrega.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="delivery-status">Status</Label>
            <Select value={status} onValueChange={(value) => setStatus(value as DeliveryStatus)}>
              <SelectTrigger id="delivery-status">
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
          </div>
          {status === "RECUSADA" ? (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="delivery-rejection-reason">Motivo da recusa</Label>
              <Textarea
                id="delivery-rejection-reason"
                value={rejectionReason}
                onChange={(event) => setRejectionReason(event.target.value)}
              />
            </div>
          ) : null}

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={updateDelivery.isPending}>
              {updateDelivery.isPending ? "Salvando…" : "Salvar"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

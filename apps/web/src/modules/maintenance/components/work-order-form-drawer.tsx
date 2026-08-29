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
import type { WorkOrderType } from "@gestorfrete/types";

import { useVehiclesQuery } from "@/modules/fleet/hooks/use-vehicles";
import { useCreateWorkOrderMutation } from "@/modules/maintenance/hooks/use-work-orders";
import { ApiError } from "@/shared/lib/api-client";

const TYPE_LABEL: Record<WorkOrderType, string> = {
  PREVENTIVA: "Preventiva",
  CORRETIVA: "Corretiva",
  EMERGENCIAL: "Emergencial",
  GARANTIA: "Garantia",
};

interface WorkOrderFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** Nasce ABERTA. `origin_abertura` fica MANUAL — CHECKLIST_REPROVADO só é usado pelo gatilho
 * automático da reprovação de Checklist Oficina, nunca escolhido aqui. */
export function WorkOrderFormDrawer({ open, onOpenChange }: WorkOrderFormDrawerProps) {
  const [tractorUnitId, setTractorUnitId] = React.useState("");
  const [type, setType] = React.useState<WorkOrderType>("CORRETIVA");
  const [problemDescription, setProblemDescription] = React.useState("");
  const [openingOdometerKm, setOpeningOdometerKm] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const vehiclesQuery = useVehiclesQuery({ limit: 100 });
  const createWorkOrder = useCreateWorkOrderMutation();

  function reset() {
    setTractorUnitId("");
    setType("CORRETIVA");
    setProblemDescription("");
    setOpeningOdometerKm("");
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createWorkOrder.mutateAsync({
        tractor_unit_id: tractorUnitId, type, problem_description: problemDescription,
        opening_odometer_km: openingOdometerKm || undefined,
      });
      toast.success("Ordem de serviço criada.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar a ordem de serviço.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Nova ordem de serviço</SheetTitle>
          <SheetDescription>Nasce Aberta — o diagnóstico é registrado depois, na aba de detalhe.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="work-order-tractor-unit">Veículo</Label>
            <Select value={tractorUnitId} onValueChange={setTractorUnitId}>
              <SelectTrigger id="work-order-tractor-unit">
                <SelectValue placeholder="Selecione um veículo" />
              </SelectTrigger>
              <SelectContent>
                {vehiclesQuery.data?.data.map((vehicle) => (
                  <SelectItem key={vehicle.id} value={vehicle.id}>
                    {vehicle.identity.plate}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="work-order-type">Tipo</Label>
            <Select value={type} onValueChange={(value) => setType(value as WorkOrderType)}>
              <SelectTrigger id="work-order-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(TYPE_LABEL) as WorkOrderType[]).map((value) => (
                  <SelectItem key={value} value={value}>
                    {TYPE_LABEL[value]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="work-order-problem-description">Descrição do problema</Label>
            <Textarea
              id="work-order-problem-description"
              required
              value={problemDescription}
              onChange={(event) => setProblemDescription(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="work-order-opening-odometer">Hodômetro na abertura (opcional)</Label>
            <Input
              id="work-order-opening-odometer"
              type="number"
              step="0.01"
              value={openingOdometerKm}
              onChange={(event) => setOpeningOdometerKm(event.target.value)}
            />
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createWorkOrder.isPending || !tractorUnitId}>
              {createWorkOrder.isPending ? "Criando…" : "Criar ordem de serviço"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

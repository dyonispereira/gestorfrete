"use client";

import * as React from "react";

import { Button, Input, Label, Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, toast } from "@gestorfrete/ui";

import { useCreateVehicleCategoryMutation } from "@/modules/fleet/hooks/use-vehicle-categories";
import { ApiError } from "@/shared/lib/api-client";

interface VehicleCategoryFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function VehicleCategoryFormDrawer({ open, onOpenChange }: VehicleCategoryFormDrawerProps) {
  const [nome, setNome] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const createVehicleCategory = useCreateVehicleCategoryMutation();

  function reset() {
    setNome("");
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createVehicleCategory.mutateAsync({ nome });
      toast.success("Categoria de veículo criada.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar a categoria.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Nova categoria de veículo</SheetTitle>
          <SheetDescription>Ex.: Truck, Carreta, Bitrem — nível de classificação administrativa.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="vehicle-category-nome">Nome</Label>
            <Input id="vehicle-category-nome" required value={nome} onChange={(event) => setNome(event.target.value)} />
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createVehicleCategory.isPending}>
              {createVehicleCategory.isPending ? "Criando…" : "Criar categoria"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

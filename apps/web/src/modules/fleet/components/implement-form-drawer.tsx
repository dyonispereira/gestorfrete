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
  toast,
} from "@gestorfrete/ui";
import type { BodyType } from "@gestorfrete/types";

import { useCreateImplementMutation } from "@/modules/fleet/hooks/use-implements";
import { useVehicleCategoriesQuery } from "@/modules/fleet/hooks/use-vehicle-categories";
import { ApiError } from "@/shared/lib/api-client";

const BODY_TYPE_LABEL: Record<BodyType, string> = {
  CARRETA: "Carreta",
  TANQUE: "Tanque",
  BAU: "Baú",
  GRANELEIRO: "Graneleiro",
  PRANCHA: "Prancha",
  FRIGORIFICO: "Frigorífico",
  GAIOLA: "Gaiola",
};

interface ImplementFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Create-only. `category_id` — Reconciliado (V1 Operational Hardening, Parte 5, D363): agora um
 * `Select` real sobre `GET /categorias-veiculo`, mesmo padrão de `VehicleFormDrawer`.
 */
export function ImplementFormDrawer({ open, onOpenChange }: ImplementFormDrawerProps) {
  const [plate, setPlate] = React.useState("");
  const [renavam, setRenavam] = React.useState("");
  const [bodyType, setBodyType] = React.useState<BodyType>("CARRETA");
  const [categoryId, setCategoryId] = React.useState("");
  const [loadCapacity, setLoadCapacity] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const createImplement = useCreateImplementMutation();
  const categoriesQuery = useVehicleCategoriesQuery({ status: "ATIVA", limit: 100 });

  function reset() {
    setPlate("");
    setRenavam("");
    setBodyType("CARRETA");
    setCategoryId("");
    setLoadCapacity("");
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createImplement.mutateAsync({
        plate,
        renavam,
        body_type: bodyType,
        category_id: categoryId,
        load_capacity: loadCapacity,
      });
      toast.success("Implemento criado.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar o implemento.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Novo implemento</SheetTitle>
          <SheetDescription>Placa e RENAVAM não podem ser alterados depois.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="implement-plate">Placa</Label>
              <Input id="implement-plate" required value={plate} onChange={(event) => setPlate(event.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="implement-renavam">RENAVAM</Label>
              <Input id="implement-renavam" required value={renavam} onChange={(event) => setRenavam(event.target.value)} />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Tipo de carroceria</Label>
            <Select value={bodyType} onValueChange={(value) => setBodyType(value as BodyType)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(BODY_TYPE_LABEL) as BodyType[]).map((value) => (
                  <SelectItem key={value} value={value}>
                    {BODY_TYPE_LABEL[value]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="implement-load-capacity">Capacidade de carga (kg)</Label>
            <Input id="implement-load-capacity" required value={loadCapacity} onChange={(event) => setLoadCapacity(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="implement-categoria">Categoria</Label>
            <Select value={categoryId} onValueChange={setCategoryId}>
              <SelectTrigger id="implement-categoria">
                <SelectValue placeholder="Selecione uma categoria" />
              </SelectTrigger>
              <SelectContent>
                {categoriesQuery.data?.data.map((category) => (
                  <SelectItem key={category.id} value={category.id}>
                    {category.nome}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {categoriesQuery.data?.data.length === 0 ? (
              <p className="text-xs text-muted-foreground">
                Nenhuma categoria ativa — crie uma em Frota → Categorias de Veículo antes.
              </p>
            ) : null}
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createImplement.isPending}>
              {createImplement.isPending ? "Criando…" : "Criar implemento"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

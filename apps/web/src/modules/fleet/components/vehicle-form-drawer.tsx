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

import { useCreateVehicleMutation } from "@/modules/fleet/hooks/use-vehicles";
import { useVehicleCategoriesQuery } from "@/modules/fleet/hooks/use-vehicle-categories";
import { ApiError } from "@/shared/lib/api-client";

interface VehicleFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Create-only. `branch_id` is optional and omitted here — no branch picker exists (same call made
 * for Centro de Custo em `037-cost-centers.md`). `categoria_id` — Reconciliado (V1 Operational
 * Hardening, Parte 5, D363): agora um `Select` real sobre `GET /categorias-veiculo`, não mais um
 * campo de UUID cru.
 */
export function VehicleFormDrawer({ open, onOpenChange }: VehicleFormDrawerProps) {
  const [plate, setPlate] = React.useState("");
  const [renavam, setRenavam] = React.useState("");
  const [fabricante, setFabricante] = React.useState("");
  const [modelo, setModelo] = React.useState("");
  const [anoFabricacao, setAnoFabricacao] = React.useState("");
  const [categoriaId, setCategoriaId] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const createVehicle = useCreateVehicleMutation();
  const categoriesQuery = useVehicleCategoriesQuery({ status: "ATIVA", limit: 100 });

  function reset() {
    setPlate("");
    setRenavam("");
    setFabricante("");
    setModelo("");
    setAnoFabricacao("");
    setCategoriaId("");
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createVehicle.mutateAsync({
        plate,
        renavam,
        fabricante,
        modelo,
        ano_fabricacao: Number(anoFabricacao),
        categoria_id: categoriaId,
      });
      toast.success("Veículo criado.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar o veículo.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Novo veículo</SheetTitle>
          <SheetDescription>Placa e RENAVAM não podem ser alterados depois.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="vehicle-plate">Placa</Label>
              <Input id="vehicle-plate" required value={plate} onChange={(event) => setPlate(event.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="vehicle-renavam">RENAVAM</Label>
              <Input id="vehicle-renavam" required value={renavam} onChange={(event) => setRenavam(event.target.value)} />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="vehicle-fabricante">Fabricante</Label>
            <Input id="vehicle-fabricante" required value={fabricante} onChange={(event) => setFabricante(event.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="vehicle-modelo">Modelo</Label>
              <Input id="vehicle-modelo" required value={modelo} onChange={(event) => setModelo(event.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="vehicle-ano">Ano de fabricação</Label>
              <Input
                id="vehicle-ano"
                type="number"
                required
                value={anoFabricacao}
                onChange={(event) => setAnoFabricacao(event.target.value)}
              />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="vehicle-categoria">Categoria</Label>
            <Select value={categoriaId} onValueChange={setCategoriaId}>
              <SelectTrigger id="vehicle-categoria">
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
            <Button type="submit" disabled={createVehicle.isPending}>
              {createVehicle.isPending ? "Criando…" : "Criar veículo"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

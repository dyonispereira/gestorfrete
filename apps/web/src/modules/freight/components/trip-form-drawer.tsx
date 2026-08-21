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

import { useClientsQuery } from "@/modules/crm/hooks/use-clients";
import { useCreateTripMutation } from "@/modules/freight/hooks/use-trips";
import { ApiError } from "@/shared/lib/api-client";

interface TripFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Create-only. `data_programada`/`janela_programada` são os únicos campos que também aceitam
 * PATCH depois — a Viagem nasce sempre em RASCUNHO, sem motorista/veículo (isso é a Alocação de
 * Recursos, feita depois na aba Recursos).
 */
export function TripFormDrawer({ open, onOpenChange }: TripFormDrawerProps) {
  const [clienteId, setClienteId] = React.useState("");
  const [dataProgramada, setDataProgramada] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const clientsQuery = useClientsQuery({ limit: 100, status: "ATIVO" });
  const createTrip = useCreateTripMutation();

  function reset() {
    setClienteId("");
    setDataProgramada("");
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createTrip.mutateAsync({
        cliente_id: clienteId,
        data_programada: dataProgramada || undefined,
      });
      toast.success("Viagem criada.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar a viagem.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Nova viagem</SheetTitle>
          <SheetDescription>Nasce em Rascunho. Motorista e veículo são definidos depois, na aba Recursos.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="trip-cliente">Cliente</Label>
            <Select value={clienteId} onValueChange={setClienteId}>
              <SelectTrigger id="trip-cliente">
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
            <Label htmlFor="trip-data-programada">Data programada</Label>
            <Input
              id="trip-data-programada"
              type="date"
              value={dataProgramada}
              onChange={(event) => setDataProgramada(event.target.value)}
            />
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createTrip.isPending || !clienteId}>
              {createTrip.isPending ? "Criando…" : "Criar viagem"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

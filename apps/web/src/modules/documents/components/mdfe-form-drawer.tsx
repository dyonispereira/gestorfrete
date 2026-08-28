"use client";

import * as React from "react";

import {
  Button,
  Checkbox,
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

import { useTripsQuery } from "@/modules/freight/hooks/use-trips";
import { useCtesQuery } from "@/modules/documents/hooks/use-ctes";
import { useCreateMdfeMutation } from "@/modules/documents/hooks/use-mdfes";
import { ApiError } from "@/shared/lib/api-client";

interface MdfeFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Único tipo de documento fiscal com criação real pelo usuário — "quais CT-e consolidar" é
 * decisão do Faturista, não automática. Exige todo `cte_id` AUTORIZADO e da mesma Viagem (409
 * `FISCAL_MDFE_CTE_NOT_AUTHORIZED`/`FISCAL_MDFE_NO_CTE` fora disso) — o picker já filtra por
 * `status=AUTORIZADO` e pelo `trip_id` escolhido, então o erro real só aparece se o estado
 * mudar entre a consulta e o envio.
 */
export function MdfeFormDrawer({ open, onOpenChange }: MdfeFormDrawerProps) {
  const [tripId, setTripId] = React.useState("");
  const [selectedCteIds, setSelectedCteIds] = React.useState<string[]>([]);
  const [formError, setFormError] = React.useState<string | null>(null);

  const tripsQuery = useTripsQuery({ limit: 100 });
  const ctesQuery = useCtesQuery({ trip_id: tripId || undefined, status: "AUTORIZADO", limit: 100 });
  const createMdfe = useCreateMdfeMutation();

  function toggleCte(cteId: string) {
    setSelectedCteIds((current) => (current.includes(cteId) ? current.filter((id) => id !== cteId) : [...current, cteId]));
  }

  function reset() {
    setTripId("");
    setSelectedCteIds([]);
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createMdfe.mutateAsync({ trip_id: tripId, cte_ids: selectedCteIds });
      toast.success("MDF-e criado.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar o MDF-e.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Novo MDF-e</SheetTitle>
          <SheetDescription>Consolida um ou mais CT-e Autorizados da mesma viagem.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="mdfe-trip">Viagem</Label>
            <Select
              value={tripId}
              onValueChange={(value) => {
                setTripId(value);
                setSelectedCteIds([]);
              }}
            >
              <SelectTrigger id="mdfe-trip">
                <SelectValue placeholder="Selecione a viagem" />
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
            <Label>CT-e Autorizados desta viagem</Label>
            <div className="flex max-h-56 flex-col gap-2 overflow-y-auto rounded-md border border-border p-3">
              {!tripId ? (
                <p className="text-sm text-muted-foreground">Selecione uma viagem primeiro.</p>
              ) : ctesQuery.isLoading ? (
                <p className="text-sm text-muted-foreground">Carregando CT-e…</p>
              ) : ctesQuery.data?.data.length === 0 ? (
                <p className="text-sm text-muted-foreground">Nenhum CT-e Autorizado nesta viagem ainda.</p>
              ) : (
                ctesQuery.data?.data.map((cte) => (
                  <label key={cte.id} className="flex items-center gap-2 text-sm">
                    <Checkbox checked={selectedCteIds.includes(cte.id)} onCheckedChange={() => toggleCte(cte.id)} />
                    {cte.number} — {cte.series}
                  </label>
                ))
              )}
            </div>
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createMdfe.isPending || !tripId || selectedCteIds.length === 0}>
              {createMdfe.isPending ? "Criando…" : "Criar MDF-e"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

"use client";

import * as React from "react";

import {
  Badge,
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

import { useDriversQuery } from "@/modules/drivers/hooks/use-drivers";
import { useImplementsQuery } from "@/modules/fleet/hooks/use-implements";
import { useVehiclesQuery } from "@/modules/fleet/hooks/use-vehicles";
import {
  useCreateTripAllocationMutation,
  useCurrentTripAllocationQuery,
  useReallocateTripResourcesMutation,
  useTripAllocationHistoryQuery,
} from "@/modules/freight/hooks/use-trip-allocations";
import { ApiError } from "@/shared/lib/api-client";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

interface AllocationPanelProps {
  tripId: string;
  canAllocate: boolean;
  canReassign: boolean;
}

/**
 * D188 — a Alocação é um pacote atômico (motorista+cavalo+implemento em uma única linha), nunca
 * editada in-place: o primeiro `POST /resources` só funciona uma vez (409 se já existe uma
 * VIGENTE); depois disso, a única forma de trocar é `POST .../commands/reallocate-resources`
 * (exige `reason`), que marca a linha atual como SUBSTITUIDA e insere uma nova — mesma disciplina
 * de append-only da Composição Veicular (D248) e do Hodômetro na Lote Frota.
 */
export function AllocationPanel({ tripId, canAllocate, canReassign }: AllocationPanelProps) {
  const currentQuery = useCurrentTripAllocationQuery(tripId);
  const historyQuery = useTripAllocationHistoryQuery(tripId);
  const driversQuery = useDriversQuery({ limit: 100 });
  const vehiclesQuery = useVehiclesQuery({ limit: 100 });
  const implementsQuery = useImplementsQuery({ limit: 100 });
  const createAllocation = useCreateTripAllocationMutation(tripId);
  const reallocate = useReallocateTripResourcesMutation(tripId);

  const [sheetMode, setSheetMode] = React.useState<"create" | "reallocate" | null>(null);
  const [driverId, setDriverId] = React.useState("");
  const [tractorUnitId, setTractorUnitId] = React.useState("");
  const [implementId, setImplementId] = React.useState("");
  const [reason, setReason] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);
  const [showHistory, setShowHistory] = React.useState(false);

  function reset() {
    setDriverId("");
    setTractorUnitId("");
    setImplementId("");
    setReason("");
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      if (sheetMode === "create") {
        await createAllocation.mutateAsync({
          driver_id: driverId,
          tractor_unit_id: tractorUnitId,
          implement_id: implementId || undefined,
        });
        toast.success("Recursos alocados.");
      } else {
        await reallocate.mutateAsync({
          driver_id: driverId,
          tractor_unit_id: tractorUnitId,
          implement_id: implementId || undefined,
          reason,
        });
        toast.success("Recursos realocados — a alocação anterior foi encerrada automaticamente.");
      }
      reset();
      setSheetMode(null);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível salvar a alocação.");
    }
  }

  if (currentQuery.isLoading) return <LoadingState rows={2} />;

  const current = currentQuery.error ? null : currentQuery.data;
  const hasAllocation = Boolean(current);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-foreground">Alocação atual</h3>
        <div className="flex gap-2">
          {!hasAllocation && canAllocate ? (
            <Button size="sm" onClick={() => setSheetMode("create")}>
              Alocar recursos
            </Button>
          ) : null}
          {hasAllocation && canReassign ? (
            <Button size="sm" variant="outline" onClick={() => setSheetMode("reallocate")}>
              Reatribuir
            </Button>
          ) : null}
        </div>
      </div>

      {!hasAllocation ? (
        <EmptyState title="Nenhuma alocação de recursos ainda" description="Aloque motorista e veículo para a viagem avançar." />
      ) : (
        <div className="rounded-md border border-border p-4">
          <div className="flex items-center gap-2">
            <Badge variant="success">Vigente</Badge>
          </div>
          <dl className="mt-2 grid grid-cols-1 gap-2 text-sm sm:grid-cols-3">
            <div>
              <dt className="text-muted-foreground">Motorista</dt>
              <dd className="font-medium">{current?.driver_id}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Veículo tracionador</dt>
              <dd className="font-medium">{current?.tractor_unit_id}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Implemento</dt>
              <dd className="font-medium">{current?.implement_id ?? "—"}</dd>
            </div>
          </dl>
        </div>
      )}

      <Button variant="outline" size="sm" className="self-start" onClick={() => setShowHistory((value) => !value)}>
        {showHistory ? "Ocultar histórico" : "Ver histórico de alocações"}
      </Button>

      {showHistory ? (
        historyQuery.isLoading ? (
          <LoadingState rows={2} />
        ) : historyQuery.error ? (
          <ErrorState description="Não foi possível carregar o histórico." onRetry={() => historyQuery.refetch()} />
        ) : (
          <div className="flex flex-col gap-2 border-l-2 border-border pl-4">
            {(historyQuery.data?.data ?? [])
              .filter((allocation) => allocation.status !== "VIGENTE")
              .map((allocation) => (
                <div key={allocation.id} className="rounded-md border border-border p-3 text-sm">
                  <div className="flex items-center gap-2">
                    {allocation.status === "SUBSTITUIDA" ? (
                      <Badge variant="secondary">Substituída</Badge>
                    ) : (
                      <Badge variant="outline">Encerrada</Badge>
                    )}
                    <span className="text-muted-foreground">{new Date(allocation.created_at).toLocaleString("pt-BR")}</span>
                  </div>
                  <p className="mt-1">
                    Motorista {allocation.driver_id} · Veículo {allocation.tractor_unit_id}
                  </p>
                  {allocation.replacement_reason ? (
                    <p className="mt-1 text-muted-foreground">Motivo: {allocation.replacement_reason}</p>
                  ) : null}
                </div>
              ))}
          </div>
        )
      ) : null}

      <Sheet open={sheetMode !== null} onOpenChange={(open) => !open && setSheetMode(null)}>
        <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>{sheetMode === "create" ? "Alocar recursos" : "Reatribuir recursos"}</SheetTitle>
            <SheetDescription>
              {sheetMode === "create"
                ? "Define motorista, veículo tracionador e (opcional) implemento. Dispara RASCUNHO → PLANEJADA."
                : "Encerra a alocação atual e cria uma nova — o motivo é obrigatório."}
            </SheetDescription>
          </SheetHeader>
          <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="allocation-driver">Motorista</Label>
              <Select value={driverId} onValueChange={setDriverId}>
                <SelectTrigger id="allocation-driver">
                  <SelectValue placeholder="Selecione um motorista" />
                </SelectTrigger>
                <SelectContent>
                  {driversQuery.data?.data.map((driver) => (
                    <SelectItem key={driver.id} value={driver.id}>
                      {driver.nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="allocation-tractor">Veículo tracionador</Label>
              <Select value={tractorUnitId} onValueChange={setTractorUnitId}>
                <SelectTrigger id="allocation-tractor">
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
              <Label htmlFor="allocation-implement">Implemento (opcional)</Label>
              <Select value={implementId} onValueChange={setImplementId}>
                <SelectTrigger id="allocation-implement">
                  <SelectValue placeholder="Nenhum" />
                </SelectTrigger>
                <SelectContent>
                  {implementsQuery.data?.data.map((implement) => (
                    <SelectItem key={implement.id} value={implement.id}>
                      {implement.plate}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {sheetMode === "reallocate" ? (
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="reallocate-reason">Motivo da troca</Label>
                <Textarea id="reallocate-reason" required value={reason} onChange={(event) => setReason(event.target.value)} />
              </div>
            ) : null}

            {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

            <div className="mt-auto flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setSheetMode(null)}>
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={
                  !driverId ||
                  !tractorUnitId ||
                  (sheetMode === "reallocate" && !reason.trim()) ||
                  createAllocation.isPending ||
                  reallocate.isPending
                }
              >
                {createAllocation.isPending || reallocate.isPending ? "Salvando…" : "Salvar"}
              </Button>
            </div>
          </form>
        </SheetContent>
      </Sheet>
    </div>
  );
}

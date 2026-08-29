"use client";

import * as React from "react";
import { Gauge } from "lucide-react";

import { Badge, Button, Input, Label, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, toast } from "@gestorfrete/ui";
import type { OdometerOrigin } from "@gestorfrete/types";

import { useCreateOdometerReadingMutation, useOdometerReadingsQuery } from "@/modules/fleet/hooks/use-odometer-readings";
import { ApiError } from "@/shared/lib/api-client";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const ORIGIN_LABEL: Record<OdometerOrigin, string> = {
  ABASTECIMENTO: "Abastecimento",
  CHECKLIST: "Checklist",
  MANUAL: "Manual",
  TELEMETRIA: "Telemetria",
  ORDEM_SERVICO: "Ordem de serviço",
};

interface OdometerReadingsTimelineProps {
  vehicleId: string;
  editable: boolean;
}

/**
 * Time Series pura — só registra, nunca edita/exclui uma leitura (sem esses botões, de
 * propósito). Paginação por cursor ("Carregar mais"), não por página.
 */
export function OdometerReadingsTimeline({ vehicleId, editable }: OdometerReadingsTimelineProps) {
  const readingsQuery = useOdometerReadingsQuery(vehicleId);
  const createReading = useCreateOdometerReadingMutation(vehicleId);

  const [valueKm, setValueKm] = React.useState("");
  const [origin, setOrigin] = React.useState<OdometerOrigin>("MANUAL");
  const [formError, setFormError] = React.useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createReading.mutateAsync({ value_km: valueKm, origin });
      toast.success("Leitura registrada.");
      setValueKm("");
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível registrar a leitura.");
    }
  }

  if (readingsQuery.isLoading) return <LoadingState rows={3} />;
  if (readingsQuery.error)
    return <ErrorState description="Não foi possível carregar as leituras." onRetry={() => readingsQuery.refetch()} />;

  const readings = readingsQuery.data?.pages.flatMap((page) => page.data) ?? [];

  return (
    <div className="flex flex-col gap-4">
      {editable ? (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-md border border-border p-4 sm:flex-row sm:items-end">
          <div className="flex flex-1 flex-col gap-1.5">
            <Label htmlFor="odometer-value">Quilometragem</Label>
            <Input id="odometer-value" type="number" required value={valueKm} onChange={(event) => setValueKm(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5 sm:w-48">
            <Label>Origem</Label>
            <Select value={origin} onValueChange={(value) => setOrigin(value as OdometerOrigin)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(ORIGIN_LABEL) as OdometerOrigin[]).map((value) => (
                  <SelectItem key={value} value={value}>
                    {ORIGIN_LABEL[value]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button type="submit" disabled={createReading.isPending}>
            {createReading.isPending ? "Registrando…" : "Registrar leitura"}
          </Button>
        </form>
      ) : null}

      {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

      {readings.length === 0 ? (
        <EmptyState icon={Gauge} title="Nenhuma leitura registrada" />
      ) : (
        <div className="flex flex-col gap-2">
          {readings.map((reading) => (
            <div key={reading.id} className="flex items-center justify-between rounded-md border border-border p-3">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{Number(reading.value_km).toLocaleString("pt-BR")} km</span>
                <Badge variant="outline">{ORIGIN_LABEL[reading.origin]}</Badge>
              </div>
              <span className="text-xs text-muted-foreground">{new Date(reading.captured_at).toLocaleString("pt-BR")}</span>
            </div>
          ))}
        </div>
      )}

      {readingsQuery.hasNextPage ? (
        <Button
          variant="outline"
          onClick={() => readingsQuery.fetchNextPage()}
          disabled={readingsQuery.isFetchingNextPage}
          className="self-center"
        >
          {readingsQuery.isFetchingNextPage ? "Carregando…" : "Carregar mais"}
        </Button>
      ) : null}
    </div>
  );
}

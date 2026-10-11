"use client";

import * as React from "react";

import { Button, Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle, Input, Label, toast } from "@gestorfrete/ui";
import type { Trip } from "@gestorfrete/types";

import { useUpdateTripMutation } from "@/modules/freight/hooks/use-trips";
import { ApiError } from "@/shared/lib/api-client";

/**
 * Lote 2 (`GESTORFRETE — PROMPT MESTRE`) — par PREVISTO de `itens_carga`/Romaneio (que só existe a
 * partir da Coleta real); nunca um duplicado, é a estimativa informada na programação, usada pelo
 * cálculo de Tabela de Frete. Sem roteirização automática nesta fase — distância é informada
 * manualmente, com validação (> 0) e persistência real.
 */
export function TripCargoRouteCard({ trip, canEdit }: { trip: Trip; canEdit: boolean }) {
  const [editing, setEditing] = React.useState(false);
  const [origemCidade, setOrigemCidade] = React.useState(trip.cargo_route.origin_city ?? "");
  const [origemUf, setOrigemUf] = React.useState(trip.cargo_route.origin_state ?? "");
  const [destinoCidade, setDestinoCidade] = React.useState(trip.cargo_route.destination_city ?? "");
  const [destinoUf, setDestinoUf] = React.useState(trip.cargo_route.destination_state ?? "");
  const [distancia, setDistancia] = React.useState(trip.cargo_route.predicted_distance_km ?? "");
  const [peso, setPeso] = React.useState(trip.cargo_route.cargo_weight_kg ?? "");
  const [tipoCarga, setTipoCarga] = React.useState(trip.cargo_route.cargo_type ?? "");
  const [quantidade, setQuantidade] = React.useState(trip.cargo_route.cargo_quantity?.toString() ?? "");
  const [unidadeQuantidade, setUnidadeQuantidade] = React.useState(trip.cargo_route.cargo_quantity_unit ?? "");
  const [formError, setFormError] = React.useState<string | null>(null);

  const updateTrip = useUpdateTripMutation(trip.id);

  function startEditing() {
    setOrigemCidade(trip.cargo_route.origin_city ?? "");
    setOrigemUf(trip.cargo_route.origin_state ?? "");
    setDestinoCidade(trip.cargo_route.destination_city ?? "");
    setDestinoUf(trip.cargo_route.destination_state ?? "");
    setDistancia(trip.cargo_route.predicted_distance_km ?? "");
    setPeso(trip.cargo_route.cargo_weight_kg ?? "");
    setTipoCarga(trip.cargo_route.cargo_type ?? "");
    setQuantidade(trip.cargo_route.cargo_quantity?.toString() ?? "");
    setUnidadeQuantidade(trip.cargo_route.cargo_quantity_unit ?? "");
    setFormError(null);
    setEditing(true);
  }

  async function handleSave() {
    setFormError(null);
    try {
      await updateTrip.mutateAsync({
        origem_cidade: origemCidade || undefined,
        origem_uf: origemUf || undefined,
        destino_cidade: destinoCidade || undefined,
        destino_uf: destinoUf || undefined,
        distancia_prevista_km: distancia || undefined,
        peso_carga_kg: peso || undefined,
        tipo_carga: tipoCarga || undefined,
        quantidade_carga: quantidade ? Number(quantidade) : undefined,
        unidade_quantidade_carga: unidadeQuantidade || undefined,
      });
      toast.success("Dados de carga e percurso atualizados.");
      setEditing(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível salvar.");
    }
  }

  if (!editing) {
    const cargo = trip.cargo_route;
    return (
      <Card>
        <CardHeader className="flex flex-row items-start justify-between">
          <div>
            <CardTitle>Carga e percurso</CardTitle>
            <CardDescription>Estimativas usadas no cálculo da Tabela de Frete — sem roteirização automática.</CardDescription>
          </div>
          {canEdit ? (
            <Button size="sm" variant="outline" onClick={startEditing}>
              Editar
            </Button>
          ) : null}
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
          <Row label="Origem" value={cargo.origin_city && cargo.origin_state ? `${cargo.origin_city}/${cargo.origin_state}` : undefined} />
          <Row label="Destino" value={cargo.destination_city && cargo.destination_state ? `${cargo.destination_city}/${cargo.destination_state}` : undefined} />
          <Row label="Distância prevista" value={cargo.predicted_distance_km ? `${cargo.predicted_distance_km} km` : undefined} />
          <Row label="Peso da carga" value={cargo.cargo_weight_kg ? `${cargo.cargo_weight_kg} kg (${cargo.cargo_weight_tons} t)` : undefined} />
          <Row label="Tipo de carga" value={cargo.cargo_type} />
          <Row label="Quantidade" value={cargo.cargo_quantity ? `${cargo.cargo_quantity} ${cargo.cargo_quantity_unit ?? ""}`.trim() : undefined} />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Carga e percurso</CardTitle>
        <CardDescription>Informação manual — sem mapas/roteirização nesta fase.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="cargo-origem-cidade">Cidade de origem</Label>
            <Input id="cargo-origem-cidade" value={origemCidade} onChange={(e) => setOrigemCidade(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="cargo-origem-uf">UF de origem</Label>
            <Input id="cargo-origem-uf" maxLength={2} value={origemUf} onChange={(e) => setOrigemUf(e.target.value.toUpperCase())} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="cargo-destino-cidade">Cidade de destino</Label>
            <Input id="cargo-destino-cidade" value={destinoCidade} onChange={(e) => setDestinoCidade(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="cargo-destino-uf">UF de destino</Label>
            <Input id="cargo-destino-uf" maxLength={2} value={destinoUf} onChange={(e) => setDestinoUf(e.target.value.toUpperCase())} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="cargo-distancia">Distância prevista (km)</Label>
            <Input id="cargo-distancia" type="number" step="0.01" value={distancia} onChange={(e) => setDistancia(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="cargo-peso">Peso da carga (kg)</Label>
            <Input id="cargo-peso" type="number" step="0.01" value={peso} onChange={(e) => setPeso(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="cargo-tipo">Tipo de carga</Label>
            <Input id="cargo-tipo" value={tipoCarga} onChange={(e) => setTipoCarga(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="cargo-quantidade">Quantidade</Label>
            <Input id="cargo-quantidade" type="number" value={quantidade} onChange={(e) => setQuantidade(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="cargo-unidade-quantidade">Unidade da quantidade</Label>
            <Input id="cargo-unidade-quantidade" placeholder="Ex: SACA, PALETE" value={unidadeQuantidade} onChange={(e) => setUnidadeQuantidade(e.target.value)} />
          </div>
        </div>
        {formError ? <p className="text-sm text-destructive">{formError}</p> : null}
      </CardContent>
      <CardFooter className="justify-end gap-2">
        <Button variant="outline" onClick={() => setEditing(false)}>
          Cancelar
        </Button>
        <Button onClick={handleSave} disabled={updateTrip.isPending}>
          {updateTrip.isPending ? "Salvando…" : "Salvar"}
        </Button>
      </CardFooter>
    </Card>
  );
}

function Row({ label, value }: { label: string; value: string | undefined }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value ?? "—"}</span>
    </div>
  );
}

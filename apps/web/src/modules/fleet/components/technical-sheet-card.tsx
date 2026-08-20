"use client";

import * as React from "react";

import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  toast,
} from "@gestorfrete/ui";
import type { FuelType } from "@gestorfrete/types";

import { useUpsertVehicleTechnicalSheetMutation, useVehicleTechnicalSheetQuery } from "@/modules/fleet/hooks/use-vehicle-technical-sheet";
import { ApiError } from "@/shared/lib/api-client";
import { LoadingState } from "@/shared/components/states/loading-state";

const FUEL_TYPE_LABEL: Record<FuelType, string> = {
  DIESEL_S10: "Diesel S10",
  DIESEL_S500: "Diesel S500",
  GNV: "GNV",
  ELETRICO: "Elétrico",
};

interface TechnicalSheetCardProps {
  vehicleId: string;
  editable: boolean;
}

/** `PATCH` here has upsert semantics — same form works whether a Ficha Técnica already exists or not. */
export function TechnicalSheetCard({ vehicleId, editable }: TechnicalSheetCardProps) {
  const sheetQuery = useVehicleTechnicalSheetQuery(vehicleId);
  const upsertSheet = useUpsertVehicleTechnicalSheetMutation(vehicleId);

  const [chassis, setChassis] = React.useState("");
  const [engine, setEngine] = React.useState("");
  const [axles, setAxles] = React.useState("");
  const [tareWeight, setTareWeight] = React.useState("");
  const [loadCapacity, setLoadCapacity] = React.useState("");
  const [grossVehicleWeight, setGrossVehicleWeight] = React.useState("");
  const [ownerRntrc, setOwnerRntrc] = React.useState("");
  const [fuelType, setFuelType] = React.useState<FuelType | "">("");

  React.useEffect(() => {
    const sheet = sheetQuery.data;
    if (!sheet) return;
    setChassis(sheet.chassis);
    setEngine(sheet.engine ?? "");
    setAxles(String(sheet.axles));
    setTareWeight(sheet.tare_weight);
    setLoadCapacity(sheet.load_capacity);
    setGrossVehicleWeight(sheet.gross_vehicle_weight);
    setOwnerRntrc(sheet.owner_rntrc ?? "");
    setFuelType(sheet.fuel_type);
  }, [sheetQuery.data]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    try {
      await upsertSheet.mutateAsync({
        chassis: chassis || undefined,
        engine: engine || undefined,
        axles: axles ? Number(axles) : undefined,
        tare_weight: tareWeight || undefined,
        load_capacity: loadCapacity || undefined,
        gross_vehicle_weight: grossVehicleWeight || undefined,
        owner_rntrc: ownerRntrc || undefined,
        fuel_type: fuelType || undefined,
      });
      toast.success("Ficha técnica salva.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível salvar a ficha técnica.");
    }
  }

  if (sheetQuery.isLoading) return <LoadingState rows={4} />;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ficha técnica</CardTitle>
        <CardDescription>
          {sheetQuery.data ? "Última atualização já registrada." : "Ainda não preenchida — o primeiro salvamento cria."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="ts-chassis">Chassi</Label>
              <Input id="ts-chassis" disabled={!editable} value={chassis} onChange={(event) => setChassis(event.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="ts-engine">Motor</Label>
              <Input id="ts-engine" disabled={!editable} value={engine} onChange={(event) => setEngine(event.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="ts-axles">Eixos</Label>
              <Input id="ts-axles" type="number" disabled={!editable} value={axles} onChange={(event) => setAxles(event.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Combustível</Label>
              <Select value={fuelType} onValueChange={(value) => setFuelType(value as FuelType)} disabled={!editable}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione…" />
                </SelectTrigger>
                <SelectContent>
                  {(Object.keys(FUEL_TYPE_LABEL) as FuelType[]).map((value) => (
                    <SelectItem key={value} value={value}>
                      {FUEL_TYPE_LABEL[value]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="ts-tare">Tara (kg)</Label>
              <Input id="ts-tare" disabled={!editable} value={tareWeight} onChange={(event) => setTareWeight(event.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="ts-capacity">Capacidade de carga (kg)</Label>
              <Input id="ts-capacity" disabled={!editable} value={loadCapacity} onChange={(event) => setLoadCapacity(event.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="ts-gvw">PBT (kg)</Label>
              <Input
                id="ts-gvw"
                disabled={!editable}
                value={grossVehicleWeight}
                onChange={(event) => setGrossVehicleWeight(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="ts-rntrc">RNTRC do proprietário</Label>
              <Input id="ts-rntrc" disabled={!editable} value={ownerRntrc} onChange={(event) => setOwnerRntrc(event.target.value)} />
            </div>
          </div>
          {editable ? (
            <div className="flex justify-end">
              <Button type="submit" disabled={upsertSheet.isPending}>
                {upsertSheet.isPending ? "Salvando…" : "Salvar ficha técnica"}
              </Button>
            </div>
          ) : null}
        </form>
      </CardContent>
    </Card>
  );
}

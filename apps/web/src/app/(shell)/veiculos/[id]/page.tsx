"use client";

import * as React from "react";
import { useParams } from "next/navigation";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  toast,
} from "@gestorfrete/ui";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useDeleteVehicleMutation, useUpdateVehicleMutation, useVehicleQuery } from "@/modules/fleet/hooks/use-vehicles";
import { VehicleStatusBadge } from "@/modules/fleet/components/vehicle-status-badge";
import { AvailabilityBadge } from "@/modules/fleet/components/availability-badge";
import { TechnicalSheetCard } from "@/modules/fleet/components/technical-sheet-card";
import { VehicleDocumentsTab } from "@/modules/fleet/components/vehicle-documents-tab";
import { CompositionsTimeline } from "@/modules/fleet/components/compositions-timeline";
import { OdometerReadingsTimeline } from "@/modules/fleet/components/odometer-readings-timeline";
import { ApiError } from "@/shared/lib/api-client";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

export default function VehicleDetailPage() {
  const params = useParams<{ id: string }>();
  const vehicleId = params.id;
  const { hasPermission } = usePermissions();

  const vehicleQuery = useVehicleQuery(vehicleId);
  const updateVehicle = useUpdateVehicleMutation(vehicleId);
  const deleteVehicle = useDeleteVehicleMutation();

  const vehicle = vehicleQuery.data;
  useBreadcrumbLabel(`/veiculos/${vehicleId}`, vehicle?.identity.plate);

  // fabricante/modelo/ano_fabricacao aren't in VehicleResponse (only identity/status/branch/
  // operational/audit) — these fields always start blank; PATCH accepts partial updates so
  // leaving one unchanged is safe, there's nothing to pre-fill them with.
  const [fabricante, setFabricante] = React.useState("");
  const [modelo, setModelo] = React.useState("");
  const [anoFabricacao, setAnoFabricacao] = React.useState("");

  const canEdit = hasPermission("fleet.vehicle.edit");
  const canDelete = hasPermission("fleet.vehicle.delete");
  const canViewAvailability = hasPermission("fleet.vehicle.view_availability");

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    try {
      await updateVehicle.mutateAsync({
        fabricante: fabricante || undefined,
        modelo: modelo || undefined,
        ano_fabricacao: anoFabricacao ? Number(anoFabricacao) : undefined,
      });
      toast.success("Veículo atualizado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível salvar.");
    }
  }

  async function handleDelete() {
    try {
      await deleteVehicle.mutateAsync(vehicleId);
      toast.success("Veículo desativado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível desativar.");
    }
  }

  if (vehicleQuery.isLoading) return <LoadingState rows={6} />;
  if (vehicleQuery.error || !vehicle)
    return (
      <ErrorState
        title="Não foi possível carregar o veículo"
        description={vehicleQuery.error instanceof Error ? vehicleQuery.error.message : undefined}
        onRetry={() => vehicleQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{vehicle.identity.plate}</h1>
          <div className="mt-1 flex items-center gap-2">
            <VehicleStatusBadge status={vehicle.status} />
            {canViewAvailability ? <AvailabilityBadge vehicleId={vehicleId} /> : null}
            <span className="text-sm text-muted-foreground">RENAVAM {vehicle.identity.renavam}</span>
          </div>
        </div>
        {canDelete && vehicle.status === "ATIVO" ? (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive">Desativar veículo</Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Desativar {vehicle.identity.plate}?</AlertDialogTitle>
                <AlertDialogDescription>O veículo deixa de aparecer nas listagens padrão.</AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancelar</AlertDialogCancel>
                <AlertDialogAction onClick={handleDelete}>Desativar</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        ) : null}
      </div>

      <Tabs defaultValue="dados">
        <TabsList>
          <TabsTrigger value="dados">Dados</TabsTrigger>
          <TabsTrigger value="ficha-tecnica">Ficha Técnica</TabsTrigger>
          <TabsTrigger value="documentos">Documentos</TabsTrigger>
          <TabsTrigger value="composicoes">Composições</TabsTrigger>
          <TabsTrigger value="hodometro">Hodômetro</TabsTrigger>
        </TabsList>

        <TabsContent value="dados">
          <Card>
            <CardHeader>
              <CardTitle>Dados do veículo</CardTitle>
              <CardDescription>
                {canEdit ? "Placa e RENAVAM não podem ser alterados. Preencha só o que quer mudar." : "Somente leitura."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSave} className="flex flex-col gap-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="detail-fabricante">Fabricante</Label>
                    <Input
                      id="detail-fabricante"
                      disabled={!canEdit}
                      placeholder="Deixe em branco para não alterar"
                      value={fabricante}
                      onChange={(event) => setFabricante(event.target.value)}
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="detail-modelo">Modelo</Label>
                    <Input
                      id="detail-modelo"
                      disabled={!canEdit}
                      placeholder="Deixe em branco para não alterar"
                      value={modelo}
                      onChange={(event) => setModelo(event.target.value)}
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="detail-ano">Ano de fabricação</Label>
                    <Input
                      id="detail-ano"
                      type="number"
                      disabled={!canEdit}
                      placeholder="Deixe em branco para não alterar"
                      value={anoFabricacao}
                      onChange={(event) => setAnoFabricacao(event.target.value)}
                    />
                  </div>
                </div>
                {canEdit ? (
                  <div className="flex justify-end">
                    <Button type="submit" disabled={updateVehicle.isPending}>
                      {updateVehicle.isPending ? "Salvando…" : "Salvar alterações"}
                    </Button>
                  </div>
                ) : null}
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ficha-tecnica">
          <TechnicalSheetCard vehicleId={vehicleId} editable={hasPermission("fleet.vehicle_technical_sheet.edit")} />
        </TabsContent>

        <TabsContent value="documentos">
          <VehicleDocumentsTab vehicleId={vehicleId} editable={hasPermission("fleet.vehicle_document.attach")} />
        </TabsContent>

        <TabsContent value="composicoes">
          <CompositionsTimeline vehicleId={vehicleId} editable={hasPermission("fleet.vehicle_composition.create")} />
        </TabsContent>

        <TabsContent value="hodometro">
          <OdometerReadingsTimeline vehicleId={vehicleId} editable={hasPermission("fleet.odometer_reading.create")} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

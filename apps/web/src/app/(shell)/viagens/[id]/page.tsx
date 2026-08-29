"use client";

import { useParams } from "next/navigation";

import { Card, CardDescription, CardHeader, CardTitle, Tabs, TabsContent, TabsList, TabsTrigger } from "@gestorfrete/ui";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useTripQuery } from "@/modules/freight/hooks/use-trips";
import { AllocationPanel } from "@/modules/freight/components/allocation-panel";
import { ChecklistPanel } from "@/modules/maintenance/components/checklist-panel";
import { DeliveriesTab } from "@/modules/freight/components/deliveries-tab";
import { OccurrencesTab } from "@/modules/freight/components/occurrences-tab";
import { TripAttachmentsPanel } from "@/modules/freight/components/trip-attachments-panel";
import { TripCommandsPanel } from "@/modules/freight/components/trip-commands-panel";
import { TripCommentsPanel } from "@/modules/freight/components/trip-comments-panel";
import { TripFinancialsCard } from "@/modules/freight/components/trip-financials-card";
import { TripSnapshotsCard } from "@/modules/freight/components/trip-snapshots-card";
import { TripStatusBadges } from "@/modules/freight/components/trip-status-badges";
import { TripTimeline } from "@/modules/freight/components/trip-timeline";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

export default function TripDetailPage() {
  const params = useParams<{ id: string }>();
  const tripId = params.id;
  const { hasPermission } = usePermissions();

  const tripQuery = useTripQuery(tripId);
  const trip = tripQuery.data;
  useBreadcrumbLabel(`/viagens/${tripId}`, trip?.codigo);

  if (tripQuery.isLoading) return <LoadingState rows={6} />;
  if (tripQuery.error || !trip)
    return (
      <ErrorState
        title="Não foi possível carregar a viagem"
        description={tripQuery.error instanceof Error ? tripQuery.error.message : undefined}
        onRetry={() => tripQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{trip.codigo}</h1>
          <div className="mt-2">
            <TripStatusBadges status={trip.status} />
          </div>
        </div>
      </div>

      <TripCommandsPanel trip={trip} />

      <Tabs defaultValue="visao-geral">
        <TabsList>
          <TabsTrigger value="visao-geral">Visão Geral</TabsTrigger>
          <TabsTrigger value="recursos">Recursos</TabsTrigger>
          <TabsTrigger value="checklist">Checklist</TabsTrigger>
          <TabsTrigger value="entregas">Entregas</TabsTrigger>
          <TabsTrigger value="ocorrencias">Ocorrências</TabsTrigger>
          <TabsTrigger value="financeiro">Financeiro</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="comentarios">Comentários</TabsTrigger>
          <TabsTrigger value="anexos">Anexos</TabsTrigger>
        </TabsList>

        <TabsContent value="visao-geral">
          <div className="flex flex-col gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Dados da viagem</CardTitle>
                <CardDescription>
                  Data programada: {trip.scheduled_date ? new Date(trip.scheduled_date).toLocaleDateString("pt-BR") : "—"}
                  {trip.distance_traveled_km ? ` · Distância percorrida: ${trip.distance_traveled_km} km` : ""}
                </CardDescription>
              </CardHeader>
            </Card>
            <TripSnapshotsCard trip={trip} />
          </div>
        </TabsContent>

        <TabsContent value="recursos">
          <AllocationPanel
            tripId={tripId}
            canAllocate={hasPermission("freight.trip.edit")}
            canReassign={hasPermission("freight.trip.reassign")}
          />
        </TabsContent>

        <TabsContent value="checklist">
          <ChecklistPanel
            referenceType="VIAGEM"
            referenceId={tripId}
            canFill={hasPermission("maintenance.checklist.fill")}
            canApprove={hasPermission("maintenance.checklist.approve")}
            canReject={hasPermission("maintenance.checklist.reject")}
          />
        </TabsContent>

        <TabsContent value="entregas">
          <DeliveriesTab
            tripId={tripId}
            canCreate={hasPermission("freight.delivery.create")}
            canEdit={hasPermission("freight.delivery.edit")}
            canRegisterPod={hasPermission("freight.pod.create")}
          />
        </TabsContent>

        <TabsContent value="ocorrencias">
          <OccurrencesTab
            tripId={tripId}
            canCreate={hasPermission("freight.occurrence.create")}
            canEdit={hasPermission("freight.occurrence.edit")}
          />
        </TabsContent>

        <TabsContent value="financeiro">
          <TripFinancialsCard tripId={tripId} />
        </TabsContent>

        <TabsContent value="timeline">
          <TripTimeline tripId={tripId} />
        </TabsContent>

        <TabsContent value="comentarios">
          <TripCommentsPanel tripId={tripId} />
        </TabsContent>

        <TabsContent value="anexos">
          <TripAttachmentsPanel tripId={tripId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

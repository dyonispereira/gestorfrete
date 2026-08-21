"use client";

import * as React from "react";
import { Package, Plus } from "lucide-react";

import { Button } from "@gestorfrete/ui";
import type { Delivery } from "@gestorfrete/types";

import { useDeliveriesQuery } from "@/modules/freight/hooks/use-deliveries";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

import { DeliveriesTable } from "./deliveries-table";
import { DeliveryEditDrawer } from "./delivery-edit-drawer";
import { DeliveryFormDrawer } from "./delivery-form-drawer";

interface DeliveriesTabProps {
  tripId: string;
  canCreate: boolean;
  canEdit: boolean;
  canRegisterPod: boolean;
}

export function DeliveriesTab({ tripId, canCreate, canEdit, canRegisterPod }: DeliveriesTabProps) {
  const deliveriesQuery = useDeliveriesQuery(tripId);
  const [createOpen, setCreateOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Delivery | null>(null);

  if (deliveriesQuery.isLoading) return <LoadingState rows={4} />;
  if (deliveriesQuery.error)
    return <ErrorState description="Não foi possível carregar as entregas." onRetry={() => deliveriesQuery.refetch()} />;

  const deliveries = deliveriesQuery.data?.data ?? [];

  return (
    <div className="flex flex-col gap-4">
      {canCreate ? (
        <div className="flex justify-end">
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" />
            Nova entrega
          </Button>
        </div>
      ) : null}

      {deliveries.length === 0 ? (
        <EmptyState icon={Package} title="Nenhuma entrega registrada" />
      ) : (
        <DeliveriesTable
          tripId={tripId}
          deliveries={deliveries}
          canEdit={canEdit}
          canRegisterPod={canRegisterPod}
          onEdit={setEditing}
        />
      )}

      <DeliveryFormDrawer tripId={tripId} open={createOpen} onOpenChange={setCreateOpen} />
      <DeliveryEditDrawer tripId={tripId} delivery={editing} onOpenChange={(open) => !open && setEditing(null)} />
    </div>
  );
}

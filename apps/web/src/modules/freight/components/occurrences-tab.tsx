"use client";

import * as React from "react";
import { AlertTriangle, Plus } from "lucide-react";

import { Button } from "@gestorfrete/ui";

import { useOccurrencesQuery } from "@/modules/freight/hooks/use-occurrences";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

import { OccurrenceFormDrawer } from "./occurrence-form-drawer";
import { OccurrencesTable } from "./occurrences-table";

interface OccurrencesTabProps {
  tripId: string;
  canCreate: boolean;
  canEdit: boolean;
}

export function OccurrencesTab({ tripId, canCreate, canEdit }: OccurrencesTabProps) {
  const occurrencesQuery = useOccurrencesQuery(tripId, { limit: 50 });
  const [createOpen, setCreateOpen] = React.useState(false);

  if (occurrencesQuery.isLoading) return <LoadingState rows={4} />;
  if (occurrencesQuery.error)
    return <ErrorState description="Não foi possível carregar as ocorrências." onRetry={() => occurrencesQuery.refetch()} />;

  const occurrences = occurrencesQuery.data?.data ?? [];

  return (
    <div className="flex flex-col gap-4">
      {canCreate ? (
        <div className="flex justify-end">
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" />
            Nova ocorrência
          </Button>
        </div>
      ) : null}

      {occurrences.length === 0 ? (
        <EmptyState icon={AlertTriangle} title="Nenhuma ocorrência registrada" />
      ) : (
        <OccurrencesTable tripId={tripId} occurrences={occurrences} canEdit={canEdit} />
      )}

      <OccurrenceFormDrawer tripId={tripId} open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  );
}

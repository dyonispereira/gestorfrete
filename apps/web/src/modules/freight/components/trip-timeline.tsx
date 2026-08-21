"use client";

import { History } from "lucide-react";

import { Badge, Button } from "@gestorfrete/ui";

import { useTripTimelineQuery } from "@/modules/freight/hooks/use-trip-timeline";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

/**
 * GET-only, para sempre (D187/D236) — nenhum botão de escrita existe ou vai existir aqui.
 * Paginação por cursor ("Carregar mais"), não por página, igual ao Hodômetro na Lote Frota.
 */
export function TripTimeline({ tripId }: { tripId: string }) {
  const timelineQuery = useTripTimelineQuery(tripId);

  if (timelineQuery.isLoading) return <LoadingState rows={4} />;
  if (timelineQuery.error)
    return <ErrorState description="Não foi possível carregar a timeline." onRetry={() => timelineQuery.refetch()} />;

  const entries = timelineQuery.data?.pages.flatMap((page) => page.data) ?? [];

  return (
    <div className="flex flex-col gap-4">
      {entries.length === 0 ? (
        <EmptyState icon={History} title="Nenhum evento registrado ainda" />
      ) : (
        <div className="flex flex-col gap-3 border-l-2 border-border pl-4">
          {entries.map((entry, index) => (
            <div key={`${entry.reference_id}-${index}`} className="relative rounded-md border border-border p-3">
              <span className="absolute -left-[21px] top-4 h-2.5 w-2.5 rounded-full bg-muted-foreground" />
              <div className="flex items-center gap-2">
                <Badge variant="outline">{entry.source}</Badge>
                <span className="text-xs text-muted-foreground">{new Date(entry.occurred_at).toLocaleString("pt-BR")}</span>
              </div>
              <p className="mt-1 text-sm">{entry.summary}</p>
            </div>
          ))}
        </div>
      )}

      {timelineQuery.hasNextPage ? (
        <Button
          variant="outline"
          onClick={() => timelineQuery.fetchNextPage()}
          disabled={timelineQuery.isFetchingNextPage}
          className="self-center"
        >
          {timelineQuery.isFetchingNextPage ? "Carregando…" : "Carregar mais"}
        </Button>
      ) : null}
    </div>
  );
}

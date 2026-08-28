"use client";

import { History } from "lucide-react";

import { Badge, Button } from "@gestorfrete/ui";

import { useMdfeStatusHistoryQuery } from "@/modules/documents/hooks/use-mdfe-status-history";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

export function MdfeStatusHistory({ mdfeId }: { mdfeId: string }) {
  const historyQuery = useMdfeStatusHistoryQuery(mdfeId);

  if (historyQuery.isLoading) return <LoadingState rows={3} />;
  if (historyQuery.error)
    return <ErrorState description="Não foi possível carregar o histórico." onRetry={() => historyQuery.refetch()} />;

  const entries = historyQuery.data?.pages.flatMap((page) => page.data) ?? [];

  return (
    <div className="flex flex-col gap-4">
      {entries.length === 0 ? (
        <EmptyState icon={History} title="Nenhuma transição registrada ainda" />
      ) : (
        <div className="flex flex-col gap-3 border-l-2 border-border pl-4">
          {entries.map((entry) => (
            <div key={entry.id} className="relative rounded-md border border-border p-3">
              <span className="absolute -left-[21px] top-4 h-2.5 w-2.5 rounded-full bg-muted-foreground" />
              <div className="flex items-center gap-2">
                <Badge variant="outline">{entry.status}</Badge>
                <span className="text-xs text-muted-foreground">{entry.origin}</span>
                <span className="text-xs text-muted-foreground">{new Date(entry.occurred_at).toLocaleString("pt-BR")}</span>
              </div>
              {entry.notes ? <p className="mt-1 text-sm">{entry.notes}</p> : null}
            </div>
          ))}
        </div>
      )}

      {historyQuery.hasNextPage ? (
        <Button
          variant="outline"
          onClick={() => historyQuery.fetchNextPage()}
          disabled={historyQuery.isFetchingNextPage}
          className="self-center"
        >
          {historyQuery.isFetchingNextPage ? "Carregando…" : "Carregar mais"}
        </Button>
      ) : null}
    </div>
  );
}

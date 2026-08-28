"use client";

import { Button, Table, TableBody, TableCell, TableHead, TableHeader, TableRow, Badge } from "@gestorfrete/ui";
import { Radio } from "lucide-react";

import { useFiscalEventsQuery } from "@/modules/documents/hooks/use-fiscal-events";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const RESULT_VARIANT: Record<string, "success" | "destructive" | "warning"> = {
  SUCESSO: "success",
  FALHA: "destructive",
  TIMEOUT: "warning",
};

/**
 * D277 — 100% somente leitura, sem nenhum comando de "consultar agora". Em ambientes onde o
 * simulador de resposta SEFAZ nunca foi acionado, esta lista fica genuinamente vazia — mostrada
 * como dado real de API, não escondida nem substituída por um placeholder inventado (mesmo
 * precedente da Disponibilidade na Lote Frota).
 */
export function FiscalEventsTable() {
  const eventsQuery = useFiscalEventsQuery();

  if (eventsQuery.isLoading) return <LoadingState rows={4} />;
  if (eventsQuery.error)
    return <ErrorState description="Não foi possível carregar os eventos fiscais." onRetry={() => eventsQuery.refetch()} />;

  const events = eventsQuery.data?.pages.flatMap((page) => page.data) ?? [];

  if (events.length === 0) {
    return (
      <EmptyState
        icon={Radio}
        title="Nenhum evento fiscal registrado"
        description="Log técnico de integrações com a SEFAZ/ANTT — vazio até uma resposta externa real ser recebida."
      />
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Documento</TableHead>
            <TableHead>Evento</TableHead>
            <TableHead>Protocolo externo</TableHead>
            <TableHead>Resultado</TableHead>
            <TableHead>Duração</TableHead>
            <TableHead>Início</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {events.map((event) => (
            <TableRow key={event.id}>
              <TableCell className="font-medium">{event.document_type}</TableCell>
              <TableCell>{event.event_type}</TableCell>
              <TableCell className="text-muted-foreground">{event.external_protocol ?? "—"}</TableCell>
              <TableCell>{event.result ? <Badge variant={RESULT_VARIANT[event.result]}>{event.result}</Badge> : "—"}</TableCell>
              <TableCell className="text-muted-foreground">{event.duration_ms !== undefined ? `${event.duration_ms} ms` : "—"}</TableCell>
              <TableCell className="text-muted-foreground">{new Date(event.started_at).toLocaleString("pt-BR")}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {eventsQuery.hasNextPage ? (
        <Button
          variant="outline"
          onClick={() => eventsQuery.fetchNextPage()}
          disabled={eventsQuery.isFetchingNextPage}
          className="self-center"
        >
          {eventsQuery.isFetchingNextPage ? "Carregando…" : "Carregar mais"}
        </Button>
      ) : null}
    </div>
  );
}

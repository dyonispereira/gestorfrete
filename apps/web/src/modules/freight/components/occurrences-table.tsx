"use client";

import { Button, Table, TableBody, TableCell, TableHead, TableHeader, TableRow, toast } from "@gestorfrete/ui";
import type { Occurrence, OccurrenceType } from "@gestorfrete/types";

import { useUpdateOccurrenceMutation } from "@/modules/freight/hooks/use-occurrences";
import { ApiError } from "@/shared/lib/api-client";

import { OccurrenceSeverityBadge, OccurrenceStatusBadge } from "./occurrence-status-badge";

const TYPE_LABEL: Record<OccurrenceType, string> = {
  ATRASO: "Atraso",
  AVARIA: "Avaria",
  PANE: "Pane",
  SINISTRO: "Sinistro",
  OUTRO: "Outro",
};

interface OccurrencesTableProps {
  tripId: string;
  occurrences: Occurrence[];
  canEdit: boolean;
}

/** Sem DELETE — uma Ocorrência errada é corrigida via `status: RESOLVIDA`, nunca removida. */
export function OccurrencesTable({ tripId, occurrences, canEdit }: OccurrencesTableProps) {
  const updateOccurrence = useUpdateOccurrenceMutation(tripId);

  async function handleResolve(occurrenceId: string) {
    try {
      await updateOccurrence.mutateAsync({ occurrenceId, body: { status: "RESOLVIDA" } });
      toast.success("Ocorrência marcada como resolvida.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível atualizar a ocorrência.");
    }
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Tipo</TableHead>
          <TableHead>Descrição</TableHead>
          <TableHead>Gravidade</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Ações</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {occurrences.map((occurrence) => (
          <TableRow key={occurrence.id}>
            <TableCell className="font-medium">{TYPE_LABEL[occurrence.type]}</TableCell>
            <TableCell className="max-w-xs truncate">{occurrence.description}</TableCell>
            <TableCell>{occurrence.severity ? <OccurrenceSeverityBadge severity={occurrence.severity} /> : "—"}</TableCell>
            <TableCell>
              <OccurrenceStatusBadge status={occurrence.status} />
            </TableCell>
            <TableCell className="text-right">
              {canEdit && occurrence.status === "ABERTA" ? (
                <Button size="sm" variant="outline" onClick={() => handleResolve(occurrence.id)} disabled={updateOccurrence.isPending}>
                  Marcar como resolvida
                </Button>
              ) : null}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

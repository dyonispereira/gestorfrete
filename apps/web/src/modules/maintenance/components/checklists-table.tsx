import Link from "next/link";
import { ClipboardCheck } from "lucide-react";

import { Badge, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { Checklist, ChecklistType } from "@gestorfrete/types";

import { ChecklistStatusBadge } from "./checklist-status-badge";

const TYPE_LABEL: Record<ChecklistType, string> = {
  MOTORISTA_SAIDA: "Motorista — Saída",
  MOTORISTA_RETORNO: "Motorista — Retorno",
  OFICINA: "Oficina",
  ADMINISTRATIVO: "Administrativo",
  CARREGAMENTO: "Carregamento",
  DESCARGA: "Descarga",
};

/**
 * Sem link de detalhe próprio nesta fundação — a interação real acontece embutida na referência
 * (aba Checklist da Viagem); esta lista serve só para consulta/auditoria (`maintenance.checklist.
 * view`), por isso a linha aponta para a Viagem referenciada, não para uma página de Checklist.
 */
export function ChecklistsTable({ checklists }: { checklists: Checklist[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Código</TableHead>
          <TableHead>Tipo</TableHead>
          <TableHead>Referência</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {checklists.map((checklist) => (
          <TableRow key={checklist.id}>
            <TableCell className="font-medium">
              {checklist.reference_type === "VIAGEM" ? (
                <Link href={`/viagens/${checklist.reference_id}`} className="flex items-center gap-2 hover:underline">
                  <ClipboardCheck className="h-4 w-4 text-muted-foreground" />
                  {checklist.codigo}
                </Link>
              ) : (
                <span className="flex items-center gap-2">
                  <ClipboardCheck className="h-4 w-4 text-muted-foreground" />
                  {checklist.codigo}
                </span>
              )}
            </TableCell>
            <TableCell>
              <Badge variant="outline">{TYPE_LABEL[checklist.type]}</Badge>
            </TableCell>
            <TableCell className="text-muted-foreground">{checklist.reference_type}</TableCell>
            <TableCell>
              <ChecklistStatusBadge status={checklist.status} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

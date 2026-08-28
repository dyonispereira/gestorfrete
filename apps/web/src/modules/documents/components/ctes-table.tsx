import Link from "next/link";
import { FileText } from "lucide-react";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { Cte } from "@gestorfrete/types";

import { CteStatusBadge } from "./cte-status-badge";

export function CtesTable({ ctes }: { ctes: Cte[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Número</TableHead>
          <TableHead>Série</TableHead>
          <TableHead>Valor do serviço</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {ctes.map((cte) => (
          <TableRow key={cte.id}>
            <TableCell className="font-medium">
              <Link href={`/ctes/${cte.id}`} className="flex items-center gap-2 hover:underline">
                <FileText className="h-4 w-4 text-muted-foreground" />
                {cte.number}
              </Link>
            </TableCell>
            <TableCell className="text-muted-foreground">{cte.series}</TableCell>
            <TableCell>{Number(cte.service_value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</TableCell>
            <TableCell>
              <CteStatusBadge status={cte.status} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

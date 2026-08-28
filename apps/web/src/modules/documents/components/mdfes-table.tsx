import Link from "next/link";
import { FileStack } from "lucide-react";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { Mdfe } from "@gestorfrete/types";

import { MdfeStatusBadge } from "./mdfe-status-badge";

export function MdfesTable({ mdfes }: { mdfes: Mdfe[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Número</TableHead>
          <TableHead>Série</TableHead>
          <TableHead>CT-e vinculados</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {mdfes.map((mdfe) => (
          <TableRow key={mdfe.id}>
            <TableCell className="font-medium">
              <Link href={`/mdfes/${mdfe.id}`} className="flex items-center gap-2 hover:underline">
                <FileStack className="h-4 w-4 text-muted-foreground" />
                {mdfe.number}
              </Link>
            </TableCell>
            <TableCell className="text-muted-foreground">{mdfe.series}</TableCell>
            <TableCell className="text-muted-foreground">{mdfe.cte_ids.length}</TableCell>
            <TableCell>
              <MdfeStatusBadge status={mdfe.status} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

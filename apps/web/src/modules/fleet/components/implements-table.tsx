import Link from "next/link";
import { Container } from "lucide-react";

import { Badge, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { BodyType, Implement } from "@gestorfrete/types";

import { ImplementStatusBadge } from "./implement-status-badge";

const BODY_TYPE_LABEL: Record<BodyType, string> = {
  CARRETA: "Carreta",
  TANQUE: "Tanque",
  BAU: "Baú",
  GRANELEIRO: "Graneleiro",
  PRANCHA: "Prancha",
  FRIGORIFICO: "Frigorífico",
  GAIOLA: "Gaiola",
};

export function ImplementsTable({ implements: items }: { implements: Implement[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Placa</TableHead>
          <TableHead>Carroceria</TableHead>
          <TableHead>Disponibilidade</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((implement) => (
          <TableRow key={implement.id}>
            <TableCell className="font-medium">
              <Link href={`/implementos/${implement.id}`} className="flex items-center gap-2 hover:underline">
                <Container className="h-4 w-4 text-muted-foreground" />
                {implement.plate}
              </Link>
            </TableCell>
            <TableCell>
              <Badge variant="outline">{BODY_TYPE_LABEL[implement.body_type]}</Badge>
            </TableCell>
            <TableCell>
              <ImplementStatusBadge status={implement.availability_status} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

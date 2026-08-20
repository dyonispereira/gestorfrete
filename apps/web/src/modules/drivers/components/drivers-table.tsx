import Link from "next/link";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { Driver } from "@gestorfrete/types";

import { DriverStatusBadge } from "./driver-status-badge";

const EMPLOYMENT_TYPE_LABEL = { EMPREGADO: "Empregado", AUTONOMO: "Autônomo" } as const;

export function DriversTable({ drivers }: { drivers: Driver[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Nome</TableHead>
          <TableHead>CPF</TableHead>
          <TableHead>Vínculo</TableHead>
          <TableHead>Situação</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {drivers.map((driver) => (
          <TableRow key={driver.id}>
            <TableCell className="font-medium">
              <Link href={`/motoristas/${driver.id}`} className="hover:underline">
                {driver.nome}
              </Link>
            </TableCell>
            <TableCell className="text-muted-foreground">{driver.cpf}</TableCell>
            <TableCell className="text-muted-foreground">{EMPLOYMENT_TYPE_LABEL[driver.employment_type]}</TableCell>
            <TableCell>
              <DriverStatusBadge status={driver.fitness_status} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

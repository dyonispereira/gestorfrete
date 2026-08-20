import Link from "next/link";
import { Truck } from "lucide-react";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { Vehicle } from "@gestorfrete/types";

import { VehicleStatusBadge } from "./vehicle-status-badge";

export function VehiclesTable({ vehicles }: { vehicles: Vehicle[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Placa</TableHead>
          <TableHead>Identificação</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {vehicles.map((vehicle) => (
          <TableRow key={vehicle.id}>
            <TableCell className="font-medium">
              <Link href={`/veiculos/${vehicle.id}`} className="flex items-center gap-2 hover:underline">
                <Truck className="h-4 w-4 text-muted-foreground" />
                {vehicle.identity.plate}
              </Link>
            </TableCell>
            <TableCell className="text-muted-foreground">{vehicle.identity.codigo}</TableCell>
            <TableCell>
              <VehicleStatusBadge status={vehicle.status} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

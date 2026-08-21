import Link from "next/link";
import { Route } from "lucide-react";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { Trip } from "@gestorfrete/types";

import { TripStatusBadges } from "./trip-status-badges";

export function TripsTable({ trips }: { trips: Trip[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Código</TableHead>
          <TableHead>Data programada</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {trips.map((trip) => (
          <TableRow key={trip.id}>
            <TableCell className="font-medium">
              <Link href={`/viagens/${trip.id}`} className="flex items-center gap-2 hover:underline">
                <Route className="h-4 w-4 text-muted-foreground" />
                {trip.codigo}
              </Link>
            </TableCell>
            <TableCell className="text-muted-foreground">
              {trip.scheduled_date ? new Date(trip.scheduled_date).toLocaleDateString("pt-BR") : "—"}
            </TableCell>
            <TableCell>
              <TripStatusBadges status={trip.status} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

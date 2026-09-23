import Link from "next/link";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { TripResult } from "@gestorfrete/types";

import { formatKm, formatMoney, formatMoneyPerKm, formatPercent } from "@/modules/analytics/lib/format";

export function TripResultsTable({ trips }: { trips: TripResult[] }) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Viagem</TableHead>
            <TableHead>Data</TableHead>
            <TableHead>Cliente</TableHead>
            <TableHead>Motorista</TableHead>
            <TableHead>Veículo</TableHead>
            <TableHead className="text-right">Receita</TableHead>
            <TableHead className="text-right">Custo</TableHead>
            <TableHead className="text-right">Margem</TableHead>
            <TableHead className="text-right">Margem %</TableHead>
            <TableHead className="text-right">KM realizado</TableHead>
            <TableHead className="text-right">Receita/km</TableHead>
            <TableHead className="text-right">Custo/km</TableHead>
            <TableHead className="text-right">Resultado/km</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {trips.map((trip) => (
            <TableRow key={trip.trip_id}>
              <TableCell className="font-medium">
                <Link href={`/viagens/${trip.trip_id}`} className="text-primary hover:underline">
                  {trip.codigo}
                </Link>
              </TableCell>
              <TableCell className="text-muted-foreground">
                {trip.scheduled_date ? new Date(trip.scheduled_date).toLocaleDateString("pt-BR") : "—"}
              </TableCell>
              <TableCell className="text-muted-foreground">{trip.client_name ?? "—"}</TableCell>
              <TableCell className="text-muted-foreground">{trip.driver_name ?? "—"}</TableCell>
              <TableCell className="text-muted-foreground">{trip.vehicle_plate ?? "—"}</TableCell>
              <TableCell className="text-right">{formatMoney(trip.totals.realized_revenue)}</TableCell>
              <TableCell className="text-right">{formatMoney(trip.totals.realized_cost)}</TableCell>
              <TableCell
                className={`text-right font-medium ${Number(trip.totals.realized_margin) < 0 ? "text-destructive" : ""}`}
              >
                {formatMoney(trip.totals.realized_margin)}
              </TableCell>
              <TableCell className="text-right">{formatPercent(trip.totals.realized_margin_pct)}</TableCell>
              <TableCell className="text-right text-muted-foreground">{formatKm(trip.totals.km)}</TableCell>
              <TableCell className="text-right text-muted-foreground">{formatMoneyPerKm(trip.totals.revenue_per_km)}</TableCell>
              <TableCell className="text-right text-muted-foreground">{formatMoneyPerKm(trip.totals.cost_per_km)}</TableCell>
              <TableCell className="text-right text-muted-foreground">{formatMoneyPerKm(trip.totals.margin_per_km)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

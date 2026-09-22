import Link from "next/link";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { DriverResult } from "@gestorfrete/types";

import { formatMoney, formatPercent } from "@/modules/analytics/lib/format";

/** "Custo Vinculado" é só o que foi explicitamente lançado contra o Motorista (nunca herdado do
 * Veículo — regra explícita do usuário) — mostrado em coluna própria para deixar isso visível sem
 * precisar entrar no drill-down. */
export function DriverResultsTable({ drivers }: { drivers: DriverResult[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Motorista</TableHead>
          <TableHead className="text-right">Viagens</TableHead>
          <TableHead className="text-right">Receita</TableHead>
          <TableHead className="text-right">Custo Viagens</TableHead>
          <TableHead className="text-right">Custo Vinculado</TableHead>
          <TableHead className="text-right">Margem</TableHead>
          <TableHead className="text-right">Margem %</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {drivers.map((driver) => (
          <TableRow key={driver.driver_id}>
            <TableCell className="font-medium">
              <Link href={`/resultados/motoristas/${driver.driver_id}`} className="text-primary hover:underline">
                {driver.name}
              </Link>
            </TableCell>
            <TableCell className="text-right">{driver.totals.trips}</TableCell>
            <TableCell className="text-right">{formatMoney(driver.totals.realized_revenue)}</TableCell>
            <TableCell className="text-right">{formatMoney(driver.trip_cost_realized)}</TableCell>
            <TableCell className="text-right text-muted-foreground">{formatMoney(driver.linked_cost_realized)}</TableCell>
            <TableCell
              className={`text-right font-medium ${Number(driver.totals.realized_margin) < 0 ? "text-destructive" : ""}`}
            >
              {formatMoney(driver.totals.realized_margin)}
            </TableCell>
            <TableCell className="text-right">{formatPercent(driver.totals.realized_margin_pct)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

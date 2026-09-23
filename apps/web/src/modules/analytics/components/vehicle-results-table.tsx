import Link from "next/link";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { VehicleResult } from "@gestorfrete/types";

import { formatKm, formatMoney, formatMoneyPerKm, formatPercent } from "@/modules/analytics/lib/format";

/** Placa | Viagens | Receita | Custo Viagens | Manutenção | Outros Custos | Custo Total | Resultado
 * | Margem % | KM realizado | Receita/km | Custo operacional/km | Custo total/km | Resultado/km —
 * exatamente a tabela pedida pelo usuário. `Resultado`/`Margem %`/`Custo total/km`/`Resultado/km`
 * são o Resultado TOTAL do Veículo (inclui Manutenção + Outros Custos); `Custo operacional/km` é só
 * Viagens — a mesma distinção Operacional×Total levada ao KM (V1 Operational Hardening, Parte 3).
 * Qualquer célula de KM mostra "Indisponível" quando a Viagem/o grupo não tiver KM conhecido —
 * nunca uma aproximação. */
export function VehicleResultsTable({ vehicles }: { vehicles: VehicleResult[] }) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Placa</TableHead>
            <TableHead className="text-right">Viagens</TableHead>
            <TableHead className="text-right">Receita</TableHead>
            <TableHead className="text-right">Custo Viagens</TableHead>
            <TableHead className="text-right">Manutenção</TableHead>
            <TableHead className="text-right">Outros Custos</TableHead>
            <TableHead className="text-right">Custo Total</TableHead>
            <TableHead className="text-right">Resultado</TableHead>
            <TableHead className="text-right">Margem %</TableHead>
            <TableHead className="text-right">KM realizado</TableHead>
            <TableHead className="text-right">Receita/km</TableHead>
            <TableHead className="text-right">Custo operacional/km</TableHead>
            <TableHead className="text-right">Custo total/km</TableHead>
            <TableHead className="text-right">Resultado/km</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {vehicles.map((vehicle) => (
            <TableRow key={vehicle.vehicle_id}>
              <TableCell className="font-medium">
                <Link href={`/resultados/veiculos/${vehicle.vehicle_id}`} className="text-primary hover:underline">
                  {vehicle.plate}
                </Link>
              </TableCell>
              <TableCell className="text-right">{vehicle.totals.trips}</TableCell>
              <TableCell className="text-right">{formatMoney(vehicle.totals.realized_revenue)}</TableCell>
              <TableCell className="text-right">{formatMoney(vehicle.trip_cost_realized)}</TableCell>
              <TableCell className="text-right">{formatMoney(vehicle.maintenance_cost_realized)}</TableCell>
              <TableCell className="text-right">{formatMoney(vehicle.other_costs_realized)}</TableCell>
              <TableCell className="text-right">{formatMoney(vehicle.totals.realized_cost)}</TableCell>
              <TableCell
                className={`text-right font-medium ${Number(vehicle.totals.realized_margin) < 0 ? "text-destructive" : ""}`}
              >
                {formatMoney(vehicle.totals.realized_margin)}
              </TableCell>
              <TableCell className="text-right">{formatPercent(vehicle.totals.realized_margin_pct)}</TableCell>
              <TableCell className="text-right text-muted-foreground">{formatKm(vehicle.totals.km)}</TableCell>
              <TableCell className="text-right text-muted-foreground">{formatMoneyPerKm(vehicle.totals.revenue_per_km)}</TableCell>
              <TableCell className="text-right text-muted-foreground">{formatMoneyPerKm(vehicle.operational_cost_per_km)}</TableCell>
              <TableCell className="text-right text-muted-foreground">{formatMoneyPerKm(vehicle.totals.cost_per_km)}</TableCell>
              <TableCell className="text-right text-muted-foreground">{formatMoneyPerKm(vehicle.totals.margin_per_km)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

import Link from "next/link";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { ClientResult } from "@gestorfrete/types";

import { formatKm, formatMoney, formatMoneyPerKm, formatPercent } from "@/modules/analytics/lib/format";

/** KM transportado/Receita/Custo/Margem por km "quando matematicamente válido" (pedido explícito do
 * usuário, V1 Operational Hardening, Parte 3) — aqui `Custo` já é só o operacional de Viagem do
 * Cliente (nunca Manutenção/frota, ver docs/domain/012-resultado-gerencial.md), então `Custo/km`
 * não precisa de uma variante "operacional" separada como em Veículo. "Indisponível" quando o
 * Cliente não tiver KM conhecido em todas as Viagens do período — nunca uma aproximação. */
export function ClientResultsTable({ clients }: { clients: ClientResult[] }) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Cliente</TableHead>
            <TableHead className="text-right">Viagens</TableHead>
            <TableHead className="text-right">Receita Prevista</TableHead>
            <TableHead className="text-right">Receita Realizada</TableHead>
            <TableHead className="text-right">Custo</TableHead>
            <TableHead className="text-right">Margem</TableHead>
            <TableHead className="text-right">Margem %</TableHead>
            <TableHead className="text-right">KM transportado</TableHead>
            <TableHead className="text-right">Receita/km</TableHead>
            <TableHead className="text-right">Custo/km</TableHead>
            <TableHead className="text-right">Margem/km</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {clients.map((client) => (
            <TableRow key={client.client_id}>
              <TableCell className="font-medium">
                <Link href={`/resultados/clientes/${client.client_id}`} className="text-primary hover:underline">
                  {client.name}
                </Link>
              </TableCell>
              <TableCell className="text-right">{client.totals.trips}</TableCell>
              <TableCell className="text-right text-muted-foreground">{formatMoney(client.totals.predicted_revenue)}</TableCell>
              <TableCell className="text-right">{formatMoney(client.totals.realized_revenue)}</TableCell>
              <TableCell className="text-right">{formatMoney(client.totals.realized_cost)}</TableCell>
              <TableCell
                className={`text-right font-medium ${Number(client.totals.realized_margin) < 0 ? "text-destructive" : ""}`}
              >
                {formatMoney(client.totals.realized_margin)}
              </TableCell>
              <TableCell className="text-right">{formatPercent(client.totals.realized_margin_pct)}</TableCell>
              <TableCell className="text-right text-muted-foreground">{formatKm(client.totals.km)}</TableCell>
              <TableCell className="text-right text-muted-foreground">{formatMoneyPerKm(client.totals.revenue_per_km)}</TableCell>
              <TableCell className="text-right text-muted-foreground">{formatMoneyPerKm(client.totals.cost_per_km)}</TableCell>
              <TableCell className="text-right text-muted-foreground">{formatMoneyPerKm(client.totals.margin_per_km)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

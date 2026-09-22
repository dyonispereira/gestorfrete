import Link from "next/link";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { ClientResult } from "@gestorfrete/types";

import { formatMoney, formatPercent } from "@/modules/analytics/lib/format";

export function ClientResultsTable({ clients }: { clients: ClientResult[] }) {
  return (
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
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

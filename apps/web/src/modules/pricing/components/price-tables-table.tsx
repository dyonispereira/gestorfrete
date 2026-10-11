import Link from "next/link";

import { Badge, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { PriceTable } from "@gestorfrete/types";

import { PriceTableStatusBadge } from "@/modules/pricing/components/price-table-status-badge";

export function PriceTablesTable({ priceTables }: { priceTables: PriceTable[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Nome</TableHead>
          <TableHead>Direção</TableHead>
          <TableHead>Vigência</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {priceTables.map((table) => (
          <TableRow key={table.id}>
            <TableCell className="font-medium">
              <Link href={`/tabelas-frete/${table.id}`} className="hover:underline">
                {table.nome}
              </Link>
            </TableCell>
            <TableCell>
              <Badge variant={table.direcao === "VENDA" ? "default" : "outline"}>
                {table.direcao === "VENDA" ? "Venda" : "Compra"}
              </Badge>
            </TableCell>
            <TableCell className="text-muted-foreground">
              {new Date(table.vigencia_inicio).toLocaleDateString("pt-BR")}
              {table.vigencia_fim ? ` – ${new Date(table.vigencia_fim).toLocaleDateString("pt-BR")}` : " – sem fim"}
            </TableCell>
            <TableCell>
              <PriceTableStatusBadge status={table.status} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

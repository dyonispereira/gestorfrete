import Link from "next/link";
import { FileText } from "lucide-react";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { Invoice } from "@gestorfrete/types";

import { InvoiceStatusBadge } from "./invoice-status-badge";

function formatMoney(value: string): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function InvoicesTable({ invoices, clientNames }: { invoices: Invoice[]; clientNames: Map<string, string> }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Número</TableHead>
          <TableHead>Cliente</TableHead>
          <TableHead>Origem</TableHead>
          <TableHead>Emissão</TableHead>
          <TableHead>Valor total</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {invoices.map((invoice) => (
          <TableRow key={invoice.id}>
            <TableCell className="font-medium">
              <Link href={`/faturas/${invoice.id}`} className="flex items-center gap-2 hover:underline">
                <FileText className="h-4 w-4 text-muted-foreground" />
                {invoice.invoice_number}
              </Link>
            </TableCell>
            <TableCell className="text-muted-foreground">{clientNames.get(invoice.client_id) ?? "—"}</TableCell>
            <TableCell className="text-muted-foreground">
              {invoice.trips.length > 0
                ? `${invoice.trips.length} ${invoice.trips.length === 1 ? "Viagem" : "Viagens"}`
                : "Entrega"}
            </TableCell>
            <TableCell className="text-muted-foreground">{new Date(invoice.issue_date).toLocaleDateString("pt-BR")}</TableCell>
            <TableCell className="font-medium">{formatMoney(invoice.total_value)}</TableCell>
            <TableCell>
              <InvoiceStatusBadge status={invoice.status} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

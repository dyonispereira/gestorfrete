import Link from "next/link";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { Client } from "@gestorfrete/types";

import { ClientStatusBadge } from "./client-status-badge";

export function ClientsTable({ clients }: { clients: Client[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Razão Social</TableHead>
          <TableHead>Documento</TableHead>
          <TableHead>Contato</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {clients.map((client) => (
          <TableRow key={client.id}>
            <TableCell className="font-medium">
              <Link href={`/clientes/${client.id}`} className="hover:underline">
                {client.razao_social}
              </Link>
              {client.nome_fantasia ? (
                <p className="text-xs text-muted-foreground">{client.nome_fantasia}</p>
              ) : null}
            </TableCell>
            <TableCell className="text-muted-foreground">{client.document}</TableCell>
            <TableCell className="text-muted-foreground">{client.email ?? client.telefone ?? "—"}</TableCell>
            <TableCell>
              <ClientStatusBadge status={client.status} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

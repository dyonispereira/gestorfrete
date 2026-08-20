import Link from "next/link";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { Role } from "@gestorfrete/types";

export function RolesTable({ roles }: { roles: Role[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Nome</TableHead>
          <TableHead>Descrição</TableHead>
          <TableHead>Permissões</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {roles.map((role) => (
          <TableRow key={role.id}>
            <TableCell className="font-medium">
              <Link href={`/papeis/${role.id}`} className="hover:underline">
                {role.nome}
              </Link>
            </TableCell>
            <TableCell className="text-muted-foreground">{role.descricao ?? "—"}</TableCell>
            <TableCell className="text-muted-foreground">
              {role.permissions.length === 0 ? "Nenhuma" : `${role.permissions.length} permissões`}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

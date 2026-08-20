import Link from "next/link";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { User } from "@gestorfrete/types";

import { UserStatusBadge } from "./user-status-badge";

export function UsersTable({ users }: { users: User[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Nome</TableHead>
          <TableHead>E-mail</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Papéis</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {users.map((user) => (
          <TableRow key={user.id} className="cursor-pointer">
            <TableCell className="font-medium">
              <Link href={`/usuarios/${user.id}`} className="hover:underline">
                {user.nome}
              </Link>
            </TableCell>
            <TableCell className="text-muted-foreground">{user.email}</TableCell>
            <TableCell>
              <UserStatusBadge status={user.status} />
            </TableCell>
            <TableCell className="text-muted-foreground">
              {user.roles.length === 0
                ? "Nenhum"
                : user.roles.length === 1
                  ? "1 papel"
                  : `${user.roles.length} papéis`}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

import Link from "next/link";
import { Landmark } from "lucide-react";

import { Badge, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { BankAccount, BankAccountType } from "@gestorfrete/types";

const TYPE_LABEL: Record<BankAccountType, string> = { CORRENTE: "Corrente", POUPANCA: "Poupança" };

export function BankAccountsTable({ accounts }: { accounts: BankAccount[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Banco</TableHead>
          <TableHead>Agência</TableHead>
          <TableHead>Conta</TableHead>
          <TableHead>Tipo</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {accounts.map((account) => (
          <TableRow key={account.id}>
            <TableCell className="font-medium">
              <Link href={`/contas-bancarias/${account.id}`} className="flex items-center gap-2 hover:underline">
                <Landmark className="h-4 w-4 text-muted-foreground" />
                {account.bank}
              </Link>
            </TableCell>
            <TableCell className="text-muted-foreground">{account.branch}</TableCell>
            <TableCell className="text-muted-foreground">{account.account_number}</TableCell>
            <TableCell>
              <Badge variant="outline">{TYPE_LABEL[account.type]}</Badge>
            </TableCell>
            <TableCell>
              <Badge variant={account.status === "ATIVA" ? "success" : "secondary"}>
                {account.status === "ATIVA" ? "Ativa" : "Inativa"}
              </Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

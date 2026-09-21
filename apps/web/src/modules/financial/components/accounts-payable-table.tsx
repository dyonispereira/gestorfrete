import Link from "next/link";
import { Receipt } from "lucide-react";

import { Badge, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { AccountsPayable, PayableOrigin } from "@gestorfrete/types";

import { AccountsPayableStatusBadge } from "./accounts-payable-status-badge";

const ORIGIN_LABEL: Record<PayableOrigin, string> = {
  VIAGEM: "Viagem",
  ORDEM_SERVICO: "Ordem de Serviço",
  ABASTECIMENTO: "Abastecimento",
  COMPRA: "Compra",
  AJUSTE_MANUAL: "Ajuste manual",
};

function formatMoney(value: string): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatCompetencia(value: string): string {
  const [year, month] = value.split("-");
  return `${month}/${year}`;
}

interface AccountsPayableTableProps {
  payables: AccountsPayable[];
  supplierNames: Map<string, string>;
  costCenterNames: Map<string, string>;
  vehiclePlates: Map<string, string>;
}

/** Saldo não existe como campo no contrato — Conta a Pagar não tem baixa parcial (`pay()` é
 * tudo-ou-nada, `APROVADA→PAGA`); "saldo" é sempre `0` quando `PAGA`/`CONCILIADA`, senão o próprio
 * `value` — derivado aqui, nunca fabricado como campo novo. */
export function AccountsPayableTable({ payables, supplierNames, costCenterNames, vehiclePlates }: AccountsPayableTableProps) {
  const isSettled = (status: AccountsPayable["status"]) => status === "PAGA" || status === "CONCILIADA";

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Fornecedor</TableHead>
          <TableHead>Origem</TableHead>
          <TableHead>Centro de custo</TableHead>
          <TableHead>Veículo</TableHead>
          <TableHead>Competência</TableHead>
          <TableHead>Vencimento</TableHead>
          <TableHead>Valor</TableHead>
          <TableHead>Saldo</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {payables.map((payable) => (
          <TableRow key={payable.id}>
            <TableCell className="font-medium">
              <Link href={`/contas-pagar/${payable.id}`} className="flex items-center gap-2 hover:underline">
                <Receipt className="h-4 w-4 text-muted-foreground" />
                {supplierNames.get(payable.supplier_id) ?? "—"}
              </Link>
            </TableCell>
            <TableCell>
              <Badge variant="outline">{ORIGIN_LABEL[payable.origin]}</Badge>
            </TableCell>
            <TableCell className="text-muted-foreground">{costCenterNames.get(payable.cost_center_id) ?? "—"}</TableCell>
            <TableCell className="text-muted-foreground">
              {payable.vehicle_id ? (vehiclePlates.get(payable.vehicle_id) ?? "—") : "—"}
            </TableCell>
            <TableCell className="text-muted-foreground">{formatCompetencia(payable.accounting_period)}</TableCell>
            <TableCell className="text-muted-foreground">{new Date(payable.due_date).toLocaleDateString("pt-BR")}</TableCell>
            <TableCell className="font-medium">{formatMoney(payable.value)}</TableCell>
            <TableCell className={isSettled(payable.status) ? "text-muted-foreground" : "font-medium"}>
              {formatMoney(isSettled(payable.status) ? "0" : payable.value)}
            </TableCell>
            <TableCell>
              <AccountsPayableStatusBadge status={payable.status} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

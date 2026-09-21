import Link from "next/link";
import { Undo2, User } from "lucide-react";

import { Badge } from "@gestorfrete/ui";
import type { FinancialReversal } from "@gestorfrete/types";

function formatMoney(value: string): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

interface FinancialReversalsListProps {
  reversals: FinancialReversal[];
  userNames: Map<string, string>;
  canViewUsers: boolean;
}

/**
 * Cada estorno é um registro paralelo e imutável (D266) — nunca some, nunca "some" o lançamento
 * original junto. `usuário` — Reconciliado (Lote Financeiro, Parte 2.1): `created_by` vem
 * resolvido via `logs_auditoria` (a trilha transversal já capturava isso; não é um campo do
 * agregado `FinancialReversal`, que segue sem `AuditMetadata` própria por decisão, D266). Sem
 * `identity_access.user.view`, mostra o ID em vez de um nome — nunca inventa um nome sem poder
 * confirmá-lo.
 */
export function FinancialReversalsList({ reversals, userNames, canViewUsers }: FinancialReversalsListProps) {
  return (
    <div className="flex flex-col gap-3">
      {reversals.map((reversal) => (
        <div key={reversal.id} className="flex flex-col gap-2 rounded-md border border-border p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Undo2 className="h-4 w-4 text-muted-foreground" />
              <span className="text-lg font-semibold text-destructive">−{formatMoney(reversal.value)}</span>
            </div>
            <span className="text-xs text-muted-foreground">{new Date(reversal.reversed_at).toLocaleString("pt-BR")}</span>
          </div>
          <p className="text-sm">{reversal.reason}</p>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <User className="h-3.5 w-3.5" />
            {reversal.created_by
              ? (canViewUsers ? (userNames.get(reversal.created_by) ?? reversal.created_by) : reversal.created_by)
              : "Usuário não identificado"}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {reversal.invoice_id ? (
              <Link href={`/faturas/${reversal.invoice_id}`}>
                <Badge variant="outline">Fatura vinculada</Badge>
              </Link>
            ) : null}
            {reversal.accounts_payable_id ? (
              <Link href={`/contas-pagar/${reversal.accounts_payable_id}`}>
                <Badge variant="outline">Conta a Pagar vinculada</Badge>
              </Link>
            ) : null}
            {reversal.accounts_receivable_id ? <Badge variant="outline">Conta a Receber vinculada</Badge> : null}
          </div>
        </div>
      ))}
    </div>
  );
}

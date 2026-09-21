import Link from "next/link";
import { Undo2 } from "lucide-react";

import { Badge } from "@gestorfrete/ui";
import type { FinancialReversal } from "@gestorfrete/types";

function formatMoney(value: string): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

/** Cada estorno é um registro paralelo e imutável (D266) — nunca some, nunca "some" o lançamento
 * original junto. `usuário` não aparece: `FinancialReversalResponse` não expõe quem registrou o
 * estorno (gap de contrato registrado, não preenchido com um valor inventado). */
export function FinancialReversalsList({ reversals }: { reversals: FinancialReversal[] }) {
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

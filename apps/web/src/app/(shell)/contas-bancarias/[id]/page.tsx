"use client";

import { useParams } from "next/navigation";
import { AlertTriangle } from "lucide-react";

import { Badge, Card, CardContent, CardHeader, CardTitle } from "@gestorfrete/ui";
import type { BankAccountType } from "@gestorfrete/types";

import { useBankAccountBalanceQuery, useBankAccountQuery } from "@/modules/financial/hooks/use-bank-accounts";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

const TYPE_LABEL: Record<BankAccountType, string> = { CORRENTE: "Corrente", POUPANCA: "Poupança" };

function formatMoney(value: string): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export default function BankAccountDetailPage() {
  const params = useParams<{ id: string }>();
  const bankAccountId = params.id;

  const accountQuery = useBankAccountQuery(bankAccountId);
  const account = accountQuery.data;
  useBreadcrumbLabel(`/contas-bancarias/${bankAccountId}`, account?.bank);

  const balanceQuery = useBankAccountBalanceQuery(bankAccountId);

  if (accountQuery.isLoading) return <LoadingState rows={4} />;
  if (accountQuery.error || !account)
    return (
      <ErrorState
        title="Não foi possível carregar a conta bancária"
        description={accountQuery.error instanceof Error ? accountQuery.error.message : undefined}
        onRetry={() => accountQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">{account.bank}</h1>
        <div className="mt-2">
          <Badge variant={account.status === "ATIVA" ? "success" : "secondary"}>
            {account.status === "ATIVA" ? "Ativa" : "Inativa"}
          </Badge>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Dados da conta</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 text-sm">
          <div className="flex items-center justify-between gap-2">
            <span className="text-muted-foreground">Agência</span>
            <span className="font-medium">{account.branch}</span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="text-muted-foreground">Número da conta</span>
            <span className="font-medium">{account.account_number}</span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="text-muted-foreground">Tipo</span>
            <span className="font-medium">{TYPE_LABEL[account.type]}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Saldo</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 text-sm">
          <p className="text-2xl font-semibold">
            {balanceQuery.data ? formatMoney(balanceQuery.data.balance) : "—"}
          </p>
          <div className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 p-3 text-amber-900 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <p>
              Este é o saldo consolidado do tenant inteiro (Recebido − Pago), não o saldo real desta conta
              específica — nenhuma movimentação hoje é vinculada a uma conta bancária individual, e não há
              integração/conciliação bancária ainda. O mesmo valor aparece para qualquer conta consultada.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

"use client";

import * as React from "react";
import { Landmark, Plus } from "lucide-react";

import { Button } from "@gestorfrete/ui";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useBankAccountsListQuery } from "@/modules/financial/hooks/use-bank-accounts";
import { BankAccountFormDrawer } from "@/modules/financial/components/bank-account-form-drawer";
import { BankAccountsTable } from "@/modules/financial/components/bank-accounts-table";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

export default function BankAccountsPage() {
  const { hasPermission } = usePermissions();
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const accountsQuery = useBankAccountsListQuery({ limit: 50 });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Contas Bancárias</h1>
          <p className="text-sm text-muted-foreground">Cadastro de contas usadas para pagamento — sem conciliação bancária ainda.</p>
        </div>
        {hasPermission("financial.bank_account.create") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Nova conta bancária
          </Button>
        ) : null}
      </div>

      {accountsQuery.isLoading ? (
        <LoadingState rows={4} />
      ) : accountsQuery.error ? (
        <ErrorState
          title="Não foi possível carregar as contas bancárias"
          description={accountsQuery.error instanceof Error ? accountsQuery.error.message : undefined}
          onRetry={() => accountsQuery.refetch()}
        />
      ) : accountsQuery.data && accountsQuery.data.data.length > 0 ? (
        <BankAccountsTable accounts={accountsQuery.data.data} />
      ) : (
        <EmptyState icon={Landmark} title="Nenhuma conta bancária cadastrada" />
      )}

      <BankAccountFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}

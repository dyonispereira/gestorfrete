"use client";

import * as React from "react";
import { ListTree, Plus } from "lucide-react";

import { Button } from "@gestorfrete/ui";
import type { ChartOfAccounts } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useChartOfAccountsListQuery } from "@/modules/financial/hooks/use-chart-of-accounts";
import { ChartOfAccountsFormDrawer } from "@/modules/financial/components/chart-of-accounts-form-drawer";
import { ChartOfAccountsTree } from "@/modules/financial/components/chart-of-accounts-tree";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

export default function ChartOfAccountsPage() {
  const { hasPermission } = usePermissions();
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [selected, setSelected] = React.useState<ChartOfAccounts | null>(null);

  const accountsQuery = useChartOfAccountsListQuery({ limit: 100 });

  function openCreate() {
    setSelected(null);
    setDrawerOpen(true);
  }

  function openEdit(account: ChartOfAccounts) {
    if (!hasPermission("financial.chart_of_accounts.edit")) return;
    setSelected(account);
    setDrawerOpen(true);
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Plano de Contas</h1>
          <p className="text-sm text-muted-foreground">Estrutura hierárquica de categorias contábeis (Receita/Despesa).</p>
        </div>
        {hasPermission("financial.chart_of_accounts.create") ? (
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Nova conta
          </Button>
        ) : null}
      </div>

      {accountsQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : accountsQuery.error ? (
        <ErrorState
          title="Não foi possível carregar o plano de contas"
          description={accountsQuery.error instanceof Error ? accountsQuery.error.message : undefined}
          onRetry={() => accountsQuery.refetch()}
        />
      ) : accountsQuery.data && accountsQuery.data.data.length > 0 ? (
        <ChartOfAccountsTree accounts={accountsQuery.data.data} onSelect={openEdit} />
      ) : (
        <EmptyState icon={ListTree} title="Nenhuma conta contábil cadastrada" />
      )}

      <ChartOfAccountsFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} account={selected} />
    </div>
  );
}

"use client";

import * as React from "react";
import { Plus, Undo2 } from "lucide-react";

import { Button, Pagination } from "@gestorfrete/ui";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useFinancialReversalsListQuery } from "@/modules/financial/hooks/use-financial-reversals";
import { useUsersQuery } from "@/modules/identity/hooks/use-users";
import { FinancialReversalFormDrawer } from "@/modules/financial/components/financial-reversal-form-drawer";
import { FinancialReversalsList } from "@/modules/financial/components/financial-reversals-list";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

export default function FinancialReversalsPage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const reversalsQuery = useFinancialReversalsListQuery({ page, limit: 20 });
  // `created_by` é um UUID cru (resolvido via `logs_auditoria` no backend, não um campo do
  // Estorno) — resolver o nome exige `identity_access.user.view`, permissão de outro módulo que
  // nem todo perfil financeiro tem. Sem ela, a lista mostra o ID em vez de inventar um nome.
  const canViewUsers = hasPermission("identity_access.user.view");
  const usersQuery = useUsersQuery({ limit: 100 });
  const userNames = new Map((canViewUsers ? usersQuery.data?.data ?? [] : []).map((u) => [u.id, u.nome]));

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Estornos Financeiros</h1>
          <p className="text-sm text-muted-foreground">Correção pós-fato de Fatura/Conta a Pagar/Conta a Receber — nunca altera o lançamento original.</p>
        </div>
        {hasPermission("financial.reversal.create") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Novo estorno
          </Button>
        ) : null}
      </div>

      {reversalsQuery.isLoading ? (
        <LoadingState rows={4} />
      ) : reversalsQuery.error ? (
        <ErrorState
          title="Não foi possível carregar os estornos"
          description={reversalsQuery.error instanceof Error ? reversalsQuery.error.message : undefined}
          onRetry={() => reversalsQuery.refetch()}
        />
      ) : reversalsQuery.data && reversalsQuery.data.data.length > 0 ? (
        <>
          <FinancialReversalsList reversals={reversalsQuery.data.data} userNames={userNames} canViewUsers={canViewUsers} />
          <Pagination
            page={reversalsQuery.data.meta.pagination.page} limit={reversalsQuery.data.meta.pagination.limit}
            total={reversalsQuery.data.meta.pagination.total} onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={Undo2} title="Nenhum estorno registrado" />
      )}

      <FinancialReversalFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}

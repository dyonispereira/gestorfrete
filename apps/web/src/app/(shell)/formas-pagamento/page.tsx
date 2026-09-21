"use client";

import * as React from "react";
import { Plus, Wallet } from "lucide-react";

import { Button, Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { PaymentMethodStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { usePaymentMethodsListQuery } from "@/modules/financial/hooks/use-payment-methods";
import { PaymentMethodFormDrawer } from "@/modules/financial/components/payment-method-form-drawer";
import { PaymentMethodsTable } from "@/modules/financial/components/payment-methods-table";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const STATUS_OPTIONS: Array<{ value: "all" | PaymentMethodStatus; label: string }> = [
  { value: "all", label: "Todos os status" },
  { value: "ATIVA", label: "Ativa" },
  { value: "INATIVA", label: "Inativa" },
];

/** D386, fechado (Lote Financeiro, Parte 2.1) — antes só existia como ID cru colado em outro formulário. */
export default function PaymentMethodsPage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [status, setStatus] = React.useState<"all" | PaymentMethodStatus>("all");
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const paymentMethodsQuery = usePaymentMethodsListQuery({ page, limit: 20, status: status === "all" ? undefined : status });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Formas de Pagamento</h1>
          <p className="text-sm text-muted-foreground">Usadas em Faturas — PIX, Boleto, Cartão, etc.</p>
        </div>
        {hasPermission("financial.payment_method.create") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Nova forma de pagamento
          </Button>
        ) : null}
      </div>

      <Select value={status} onValueChange={(v) => { setStatus(v as "all" | PaymentMethodStatus); setPage(1); }}>
        <SelectTrigger className="sm:w-56">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {STATUS_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {paymentMethodsQuery.isLoading ? (
        <LoadingState rows={4} />
      ) : paymentMethodsQuery.error ? (
        <ErrorState
          title="Não foi possível carregar as formas de pagamento"
          description={paymentMethodsQuery.error instanceof Error ? paymentMethodsQuery.error.message : undefined}
          onRetry={() => paymentMethodsQuery.refetch()}
        />
      ) : paymentMethodsQuery.data && paymentMethodsQuery.data.data.length > 0 ? (
        <>
          <PaymentMethodsTable paymentMethods={paymentMethodsQuery.data.data} />
          <Pagination
            page={paymentMethodsQuery.data.meta.pagination.page} limit={paymentMethodsQuery.data.meta.pagination.limit}
            total={paymentMethodsQuery.data.meta.pagination.total} onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={Wallet} title="Nenhuma forma de pagamento cadastrada" description="Crie a primeira para poder faturar." />
      )}

      <PaymentMethodFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}

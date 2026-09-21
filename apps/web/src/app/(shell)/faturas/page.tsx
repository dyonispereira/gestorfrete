"use client";

import * as React from "react";
import Link from "next/link";
import { FileText, Plus } from "lucide-react";

import { Button, Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { InvoiceStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useInvoicesListQuery } from "@/modules/financial/hooks/use-invoices";
import { useClientsQuery } from "@/modules/crm/hooks/use-clients";
import { InvoicesTable } from "@/modules/financial/components/invoices-table";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const STATUS_OPTIONS: Array<{ value: "all" | InvoiceStatus; label: string }> = [
  { value: "all", label: "Todos os status" },
  { value: "EMITIDA", label: "Emitida" },
  { value: "CANCELADA", label: "Cancelada" },
];

export default function InvoicesPage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [status, setStatus] = React.useState<"all" | InvoiceStatus>("all");

  const invoicesQuery = useInvoicesListQuery({ page, limit: 20, status: status === "all" ? undefined : status });
  const clientsQuery = useClientsQuery({ limit: 100 });
  const clientNames = new Map((clientsQuery.data?.data ?? []).map((c) => [c.id, c.razao_social]));

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Faturas</h1>
          <p className="text-sm text-muted-foreground">Faturamento por viagem/entrega, com Contas a Receber geradas.</p>
        </div>
        {hasPermission("financial.invoice.create") ? (
          <Button asChild>
            <Link href="/faturas/nova">
              <Plus className="h-4 w-4" />
              Nova fatura
            </Link>
          </Button>
        ) : null}
      </div>

      <Select value={status} onValueChange={(v) => { setStatus(v as "all" | InvoiceStatus); setPage(1); }}>
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

      {invoicesQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : invoicesQuery.error ? (
        <ErrorState
          title="Não foi possível carregar as faturas"
          description={invoicesQuery.error instanceof Error ? invoicesQuery.error.message : undefined}
          onRetry={() => invoicesQuery.refetch()}
        />
      ) : invoicesQuery.data && invoicesQuery.data.data.length > 0 ? (
        <>
          <InvoicesTable invoices={invoicesQuery.data.data} clientNames={clientNames} />
          <Pagination
            page={invoicesQuery.data.meta.pagination.page} limit={invoicesQuery.data.meta.pagination.limit}
            total={invoicesQuery.data.meta.pagination.total} onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={FileText} title="Nenhuma fatura encontrada" description="Ajuste o filtro ou crie a primeira fatura." />
      )}
    </div>
  );
}

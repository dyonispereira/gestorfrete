"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { Button, Card, CardContent, CardHeader, CardTitle, toast } from "@gestorfrete/ui";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useCancelInvoiceMutation, useInvoiceQuery } from "@/modules/financial/hooks/use-invoices";
import { useClientQuery } from "@/modules/crm/hooks/use-clients";
import { InvoiceStatusBadge } from "@/modules/financial/components/invoice-status-badge";
import { AccountsReceivableTab } from "@/modules/financial/components/accounts-receivable-tab";
import { ApiError } from "@/shared/lib/api-client";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

function formatMoney(value: string): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export default function InvoiceDetailPage() {
  const params = useParams<{ id: string }>();
  const invoiceId = params.id;
  const { hasPermission } = usePermissions();

  const invoiceQuery = useInvoiceQuery(invoiceId);
  const invoice = invoiceQuery.data;
  useBreadcrumbLabel(`/faturas/${invoiceId}`, invoice?.invoice_number);

  const clientQuery = useClientQuery(invoice?.client_id);
  const cancelInvoice = useCancelInvoiceMutation();

  async function handleCancel() {
    try {
      await cancelInvoice.mutateAsync(invoiceId);
      toast.success("Fatura cancelada.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível cancelar a fatura.");
    }
  }

  if (invoiceQuery.isLoading) return <LoadingState rows={6} />;
  if (invoiceQuery.error || !invoice)
    return (
      <ErrorState
        title="Não foi possível carregar a fatura"
        description={invoiceQuery.error instanceof Error ? invoiceQuery.error.message : undefined}
        onRetry={() => invoiceQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{invoice.invoice_number}</h1>
          <div className="mt-2">
            <InvoiceStatusBadge status={invoice.status} />
          </div>
        </div>
        {invoice.status === "EMITIDA" && hasPermission("financial.invoice.cancel") ? (
          <Button variant="destructive" onClick={handleCancel} disabled={cancelInvoice.isPending}>
            Cancelar fatura
          </Button>
        ) : null}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Dados da fatura</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 text-sm">
          <div className="flex items-center justify-between gap-2">
            <span className="text-muted-foreground">Cliente</span>
            <span className="font-medium">{clientQuery.data?.razao_social ?? "—"}</span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="text-muted-foreground">Origem</span>
            {invoice.trip_id ? (
              <Link href={`/viagens/${invoice.trip_id}`} className="font-medium text-primary hover:underline">
                Ver viagem (CT-e e canhoto na própria Viagem, D008)
              </Link>
            ) : (
              <span className="font-medium">Entrega {invoice.delivery_id}</span>
            )}
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="text-muted-foreground">Emissão</span>
            <span className="font-medium">{new Date(invoice.issue_date).toLocaleDateString("pt-BR")}</span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="text-muted-foreground">Valor total</span>
            <span className="font-medium">{formatMoney(invoice.total_value)}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Contas a Receber</CardTitle>
        </CardHeader>
        <CardContent>
          <AccountsReceivableTab invoiceId={invoiceId} invoiceStatus={invoice.status} />
        </CardContent>
      </Card>
    </div>
  );
}

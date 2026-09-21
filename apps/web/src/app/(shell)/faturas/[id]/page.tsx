"use client";

import { useParams } from "next/navigation";

import { Button, Card, CardContent, CardHeader, CardTitle, Tabs, TabsContent, TabsList, TabsTrigger, toast } from "@gestorfrete/ui";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useCancelInvoiceMutation, useInvoiceQuery } from "@/modules/financial/hooks/use-invoices";
import { useClientQuery } from "@/modules/crm/hooks/use-clients";
import { usePaymentMethodQuery } from "@/modules/financial/hooks/use-payment-methods";
import { InvoiceStatusBadge } from "@/modules/financial/components/invoice-status-badge";
import { InvoiceTripsTab } from "@/modules/financial/components/invoice-trips-tab";
import { AccountsReceivableTab } from "@/modules/financial/components/accounts-receivable-tab";
import { ApiError } from "@/shared/lib/api-client";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

function formatMoney(value: string): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

/**
 * Cabeçalho / Itens / Financeiro (pedido explícito do usuário) — "o usuário consegue sair da
 * Fatura e rastrear a operação que gerou cada real". Lote Financeiro, Parte 3 — Faturamento
 * Agrupado: uma Fatura cobre N Viagens (`invoice.trips`), não mais uma só.
 */
export default function InvoiceDetailPage() {
  const params = useParams<{ id: string }>();
  const invoiceId = params.id;
  const { hasPermission } = usePermissions();

  const invoiceQuery = useInvoiceQuery(invoiceId);
  const invoice = invoiceQuery.data;
  useBreadcrumbLabel(`/faturas/${invoiceId}`, invoice?.invoice_number);

  const clientQuery = useClientQuery(invoice?.client_id);
  const paymentMethodQuery = usePaymentMethodQuery(invoice?.payment_method_id);
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

      <Tabs defaultValue="cabecalho">
        <TabsList>
          <TabsTrigger value="cabecalho">Cabeçalho</TabsTrigger>
          <TabsTrigger value="itens">Itens Faturados</TabsTrigger>
          <TabsTrigger value="financeiro">Financeiro</TabsTrigger>
        </TabsList>

        <TabsContent value="cabecalho">
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
                {invoice.trips.length > 0 ? (
                  <span className="font-medium">
                    {invoice.trips.length} {invoice.trips.length === 1 ? "Viagem" : "Viagens"} (ver aba Itens Faturados)
                  </span>
                ) : (
                  // Modo "por entrega" não tem tela própria de Entrega avulsa nesta base (fluxo
                  // alternativo, fora do escopo da Parte 3) — mostra o ID, sem inventar um link quebrado.
                  <span className="font-medium">Entrega {invoice.delivery_id}</span>
                )}
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Emissão</span>
                <span className="font-medium">{new Date(invoice.issue_date).toLocaleDateString("pt-BR")}</span>
              </div>
              {/* Vencimento/Competência não são campos da Fatura em si — cada parcela (Conta a
                  Receber) tem os seus, podendo divergir entre parcelas. Mostrar um único valor
                  aqui seria inventar um dado que o domínio não tem — a aba Financeiro mostra o
                  vencimento/competência reais de cada parcela. */}
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Forma de pagamento</span>
                <span className="font-medium">{paymentMethodQuery.data?.nome ?? "—"}</span>
              </div>
              <div className="mt-2 flex flex-col gap-1 border-t border-border pt-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-muted-foreground">Valor bruto</span>
                  <span className="font-medium">{formatMoney(invoice.gross_value)}</span>
                </div>
                {Number(invoice.adjustment_value) !== 0 ? (
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-muted-foreground">
                      Ajuste{invoice.adjustment_reason ? ` — ${invoice.adjustment_reason}` : ""}
                    </span>
                    <span className={Number(invoice.adjustment_value) < 0 ? "font-medium text-destructive" : "font-medium"}>
                      {formatMoney(invoice.adjustment_value)}
                    </span>
                  </div>
                ) : null}
                <div className="flex items-center justify-between gap-2 text-base">
                  <span className="font-semibold text-foreground">Valor total</span>
                  <span className="font-semibold text-foreground">{formatMoney(invoice.total_value)}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="itens">
          <InvoiceTripsTab trips={invoice.trips} />
        </TabsContent>

        <TabsContent value="financeiro">
          <Card>
            <CardHeader>
              <CardTitle>Contas a Receber</CardTitle>
            </CardHeader>
            <CardContent>
              <AccountsReceivableTab invoiceId={invoiceId} invoiceStatus={invoice.status} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

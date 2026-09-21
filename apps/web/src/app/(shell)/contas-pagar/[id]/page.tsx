"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { Card, CardContent, CardHeader, CardTitle, Tabs, TabsContent, TabsList, TabsTrigger } from "@gestorfrete/ui";
import type { PayableOrigin } from "@gestorfrete/types";

import { useAccountsPayableQuery } from "@/modules/financial/hooks/use-accounts-payable";
import { AccountsPayableCommandsPanel } from "@/modules/financial/components/accounts-payable-commands-panel";
import { AccountsPayableStatusBadge } from "@/modules/financial/components/accounts-payable-status-badge";
import { ExpenseApprovalsTab } from "@/modules/financial/components/expense-approvals-tab";
import { ExpenseAllocationsTab } from "@/modules/financial/components/expense-allocations-tab";
import { useSupplierQuery } from "@/modules/maintenance/hooks/use-suppliers";
import { useCostCenterQuery } from "@/modules/financial/hooks/use-cost-centers";
import { useChartOfAccountsQuery } from "@/modules/financial/hooks/use-chart-of-accounts";
import { useVehicleQuery } from "@/modules/fleet/hooks/use-vehicles";
import { useDriverQuery } from "@/modules/drivers/hooks/use-drivers";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

const ORIGIN_LABEL: Record<PayableOrigin, string> = {
  VIAGEM: "Viagem",
  ORDEM_SERVICO: "Ordem de Serviço",
  ABASTECIMENTO: "Abastecimento",
  COMPRA: "Compra",
  AJUSTE_MANUAL: "Ajuste manual",
};

function formatMoney(value: string): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatCompetencia(value: string): string {
  const [year, month] = value.split("-");
  return `${month}/${year}`;
}

export default function AccountsPayableDetailPage() {
  const params = useParams<{ id: string }>();
  const payableId = params.id;

  const payableQuery = useAccountsPayableQuery(payableId);
  const payable = payableQuery.data;
  useBreadcrumbLabel(`/contas-pagar/${payableId}`, payable ? formatMoney(payable.value) : undefined);

  const supplierQuery = useSupplierQuery(payable?.supplier_id);
  const costCenterQuery = useCostCenterQuery(payable?.cost_center_id);
  const chartQuery = useChartOfAccountsQuery(payable?.chart_of_accounts_id);
  const vehicleQuery = useVehicleQuery(payable?.vehicle_id);
  const driverQuery = useDriverQuery(payable?.driver_id);

  if (payableQuery.isLoading) return <LoadingState rows={6} />;
  if (payableQuery.error || !payable)
    return (
      <ErrorState
        title="Não foi possível carregar a conta a pagar"
        description={payableQuery.error instanceof Error ? payableQuery.error.message : undefined}
        onRetry={() => payableQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">{formatMoney(payable.value)}</h1>
        <div className="mt-2">
          <AccountsPayableStatusBadge status={payable.status} />
        </div>
      </div>

      <AccountsPayableCommandsPanel payable={payable} />

      <Tabs defaultValue="visao-geral">
        <TabsList>
          <TabsTrigger value="visao-geral">Visão Geral</TabsTrigger>
          <TabsTrigger value="aprovacoes">Aprovações</TabsTrigger>
          <TabsTrigger value="rateios">Rateios</TabsTrigger>
        </TabsList>

        <TabsContent value="visao-geral">
          <div className="flex flex-col gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Dados do lançamento</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-2 text-sm">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-muted-foreground">Fornecedor</span>
                  <span className="font-medium">{supplierQuery.data?.razao_social ?? "—"}</span>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-muted-foreground">Centro de custo</span>
                  <span className="font-medium">{costCenterQuery.data?.nome ?? "—"}</span>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-muted-foreground">Plano de contas</span>
                  <span className="font-medium">
                    {chartQuery.data ? `${chartQuery.data.account_code} — ${chartQuery.data.name}` : "—"}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-muted-foreground">Competência</span>
                  <span className="font-medium">{formatCompetencia(payable.accounting_period)}</span>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-muted-foreground">Vencimento</span>
                  <span className="font-medium">{new Date(payable.due_date).toLocaleDateString("pt-BR")}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Origem e rastreabilidade</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-2 text-sm">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-muted-foreground">Origem</span>
                  <span className="font-medium">{ORIGIN_LABEL[payable.origin]}</span>
                </div>
                {payable.maintenance_order_id ? (
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-muted-foreground">Ordem de Serviço</span>
                    <Link href={`/ordens-servico/${payable.maintenance_order_id}`} className="font-medium text-primary hover:underline">
                      Ver ordem de serviço
                    </Link>
                  </div>
                ) : null}
                {payable.trip_id ? (
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-muted-foreground">Viagem</span>
                    <Link href={`/viagens/${payable.trip_id}`} className="font-medium text-primary hover:underline">
                      Ver viagem
                    </Link>
                  </div>
                ) : null}
                <div className="flex items-center justify-between gap-2">
                  <span className="text-muted-foreground">Veículo</span>
                  <span className="font-medium">{vehicleQuery.data?.identity.plate ?? "—"}</span>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-muted-foreground">Motorista</span>
                  <span className="font-medium">{driverQuery.data?.nome ?? "—"}</span>
                </div>
                {payable.origin === "ORDEM_SERVICO" ? (
                  <p className="mt-1 text-xs text-muted-foreground">
                    Nasceu automaticamente no fechamento da Ordem de Serviço acima — sem lançamento manual.
                  </p>
                ) : null}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="aprovacoes">
          <ExpenseApprovalsTab accountsPayableId={payableId} />
        </TabsContent>

        <TabsContent value="rateios">
          <ExpenseAllocationsTab accountsPayableId={payableId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

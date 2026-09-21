"use client";

import * as React from "react";
import { Plus, Receipt } from "lucide-react";

import { Button, Input, Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { PayableStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useAccountsPayableListQuery } from "@/modules/financial/hooks/use-accounts-payable";
import { useSuppliersQuery } from "@/modules/maintenance/hooks/use-suppliers";
import { useCostCentersQuery } from "@/modules/financial/hooks/use-cost-centers";
import { useChartOfAccountsListQuery } from "@/modules/financial/hooks/use-chart-of-accounts";
import { useVehiclesQuery } from "@/modules/fleet/hooks/use-vehicles";
import { AccountsPayableFormDrawer } from "@/modules/financial/components/accounts-payable-form-drawer";
import { AccountsPayableTable } from "@/modules/financial/components/accounts-payable-table";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const STATUS_OPTIONS: Array<{ value: "all" | PayableStatus; label: string }> = [
  { value: "all", label: "Todos os status" },
  { value: "LANCADA", label: "Lançada" },
  { value: "AGUARDANDO_APROVACAO", label: "Aguardando aprovação" },
  { value: "APROVADA", label: "Aprovada" },
  { value: "PAGA", label: "Paga" },
  { value: "CONCILIADA", label: "Conciliada" },
  { value: "REJEITADA", label: "Rejeitada" },
];

export default function AccountsPayablePage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [status, setStatus] = React.useState<"all" | PayableStatus>("all");
  const [supplierId, setSupplierId] = React.useState("all");
  const [costCenterId, setCostCenterId] = React.useState("all");
  const [vehicleId, setVehicleId] = React.useState("all");
  const [chartOfAccountsId, setChartOfAccountsId] = React.useState("all");
  // Input `type="month"` devolve "YYYY-MM" — convertido para o primeiro dia do mês, mesma
  // convenção usada na criação da Conta a Pagar (`competencia` sempre `day=1`).
  const [accountingPeriodMonth, setAccountingPeriodMonth] = React.useState("");
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const payablesQuery = useAccountsPayableListQuery({
    page, limit: 20, status: status === "all" ? undefined : status,
    supplier_id: supplierId === "all" ? undefined : supplierId,
    cost_center_id: costCenterId === "all" ? undefined : costCenterId,
    vehicle_id: vehicleId === "all" ? undefined : vehicleId,
    chart_of_accounts_id: chartOfAccountsId === "all" ? undefined : chartOfAccountsId,
    accounting_period: accountingPeriodMonth ? `${accountingPeriodMonth}-01` : undefined,
  });
  const suppliersQuery = useSuppliersQuery({ limit: 100 });
  const costCentersQuery = useCostCentersQuery({ limit: 100 });
  const chartOfAccountsQuery = useChartOfAccountsListQuery({ limit: 100, type: "DESPESA" });
  const vehiclesQuery = useVehiclesQuery({ limit: 100 });

  const supplierNames = new Map((suppliersQuery.data?.data ?? []).map((s) => [s.id, s.razao_social]));
  const costCenterNames = new Map((costCentersQuery.data?.data ?? []).map((c) => [c.id, c.nome]));
  const vehiclePlates = new Map((vehiclesQuery.data?.data ?? []).map((v) => [v.id, v.identity.plate]));

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Contas a Pagar</h1>
          <p className="text-sm text-muted-foreground">Despesas de viagem, manutenção, abastecimento e lançamentos administrativos.</p>
        </div>
        {hasPermission("financial.payable.create") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Nova conta a pagar
          </Button>
        ) : null}
      </div>

      <div className="flex flex-wrap gap-3">
        <Select value={status} onValueChange={(v) => { setStatus(v as "all" | PayableStatus); setPage(1); }}>
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
        <Select value={supplierId} onValueChange={(v) => { setSupplierId(v); setPage(1); }}>
          <SelectTrigger className="sm:w-56">
            <SelectValue placeholder="Todos os fornecedores" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os fornecedores</SelectItem>
            {suppliersQuery.data?.data.map((supplier) => (
              <SelectItem key={supplier.id} value={supplier.id}>
                {supplier.razao_social}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={costCenterId} onValueChange={(v) => { setCostCenterId(v); setPage(1); }}>
          <SelectTrigger className="sm:w-56">
            <SelectValue placeholder="Todos os centros de custo" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os centros de custo</SelectItem>
            {costCentersQuery.data?.data.map((costCenter) => (
              <SelectItem key={costCenter.id} value={costCenter.id}>
                {costCenter.nome}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={vehicleId} onValueChange={(v) => { setVehicleId(v); setPage(1); }}>
          <SelectTrigger className="sm:w-56">
            <SelectValue placeholder="Todos os veículos" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os veículos</SelectItem>
            {vehiclesQuery.data?.data.map((vehicle) => (
              <SelectItem key={vehicle.id} value={vehicle.id}>
                {vehicle.identity.plate}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={chartOfAccountsId} onValueChange={(v) => { setChartOfAccountsId(v); setPage(1); }}>
          <SelectTrigger className="sm:w-56">
            <SelectValue placeholder="Todos os planos de contas" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os planos de contas</SelectItem>
            {chartOfAccountsQuery.data?.data.map((account) => (
              <SelectItem key={account.id} value={account.id}>
                {account.account_code} — {account.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Input
          type="month" className="sm:w-40" aria-label="Competência" value={accountingPeriodMonth}
          onChange={(event) => { setAccountingPeriodMonth(event.target.value); setPage(1); }}
        />
      </div>

      {payablesQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : payablesQuery.error ? (
        <ErrorState
          title="Não foi possível carregar as contas a pagar"
          description={payablesQuery.error instanceof Error ? payablesQuery.error.message : undefined}
          onRetry={() => payablesQuery.refetch()}
        />
      ) : payablesQuery.data && payablesQuery.data.data.length > 0 ? (
        <>
          <AccountsPayableTable
            payables={payablesQuery.data.data} supplierNames={supplierNames}
            costCenterNames={costCenterNames} vehiclePlates={vehiclePlates}
          />
          <Pagination
            page={payablesQuery.data.meta.pagination.page} limit={payablesQuery.data.meta.pagination.limit}
            total={payablesQuery.data.meta.pagination.total} onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={Receipt} title="Nenhuma conta a pagar encontrada" description="Ajuste o filtro ou crie um novo lançamento." />
      )}

      <AccountsPayableFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}

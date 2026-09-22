"use client";

import * as React from "react";
import { BarChart3 } from "lucide-react";

import { Pagination, Tabs, TabsContent, TabsList, TabsTrigger } from "@gestorfrete/ui";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { PeriodFilter, type Period } from "@/modules/analytics/components/period-filter";
import { ResultSummaryCards } from "@/modules/analytics/components/result-summary-cards";
import { TripResultsTable } from "@/modules/analytics/components/trip-results-table";
import { VehicleResultsTable } from "@/modules/analytics/components/vehicle-results-table";
import { ClientResultsTable } from "@/modules/analytics/components/client-results-table";
import { DriverResultsTable } from "@/modules/analytics/components/driver-results-table";
import {
  useClientResultsQuery,
  useDriverResultsQuery,
  useOverviewQuery,
  useTripResultsQuery,
  useVehicleResultsQuery,
} from "@/modules/analytics/hooks/use-management-results";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

/** Operação → Fiscal → Financeiro → Resultado — a última etapa da cadeia. Nenhum dado aqui é
 * digitado: tudo deriva dos fatos já registrados nos módulos operacionais (D090/D149). */
export default function ManagementResultsPage() {
  const { hasPermission } = usePermissions();
  const [period, setPeriod] = React.useState<Period>({ dateFrom: "", dateTo: "" });
  const periodParams = { date_from: period.dateFrom || undefined, date_to: period.dateTo || undefined };

  const canViewOverview = hasPermission("analytics.executive_dashboard.view");
  const canViewTrips = hasPermission("analytics.freight_report.view");
  const canViewVehicles = hasPermission("analytics.maintenance_report.view");
  const canViewClients = hasPermission("analytics.financial_report.view");
  const canViewDrivers = hasPermission("analytics.driver_report.view");

  const defaultTab = canViewOverview
    ? "visao-geral"
    : canViewTrips
      ? "viagens"
      : canViewVehicles
        ? "veiculos"
        : canViewClients
          ? "clientes"
          : "motoristas";

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Resultado Gerencial</h1>
          <p className="text-sm text-muted-foreground">Quem fatura, quem custa e quem dá margem — derivado, nunca digitado.</p>
        </div>
        <PeriodFilter period={period} onChange={setPeriod} />
      </div>

      <Tabs defaultValue={defaultTab}>
        <TabsList>
          {canViewOverview ? <TabsTrigger value="visao-geral">Visão Geral</TabsTrigger> : null}
          {canViewTrips ? <TabsTrigger value="viagens">Viagens</TabsTrigger> : null}
          {canViewVehicles ? <TabsTrigger value="veiculos">Veículos</TabsTrigger> : null}
          {canViewClients ? <TabsTrigger value="clientes">Clientes</TabsTrigger> : null}
          {canViewDrivers ? <TabsTrigger value="motoristas">Motoristas</TabsTrigger> : null}
        </TabsList>

        {canViewOverview ? (
          <TabsContent value="visao-geral">
            <OverviewTab period={periodParams} />
          </TabsContent>
        ) : null}
        {canViewTrips ? (
          <TabsContent value="viagens">
            <TripsTab period={periodParams} />
          </TabsContent>
        ) : null}
        {canViewVehicles ? (
          <TabsContent value="veiculos">
            <VehiclesTab period={periodParams} />
          </TabsContent>
        ) : null}
        {canViewClients ? (
          <TabsContent value="clientes">
            <ClientsTab period={periodParams} />
          </TabsContent>
        ) : null}
        {canViewDrivers ? (
          <TabsContent value="motoristas">
            <DriversTab period={periodParams} />
          </TabsContent>
        ) : null}
      </Tabs>
    </div>
  );
}

function OverviewTab({ period }: { period: { date_from?: string; date_to?: string } }) {
  const query = useOverviewQuery(period);
  if (query.isLoading) return <LoadingState rows={2} />;
  if (query.error || !query.data)
    return <ErrorState title="Não foi possível carregar a Visão Geral" onRetry={() => query.refetch()} />;
  return <ResultSummaryCards totals={query.data.totals} />;
}

function TripsTab({ period }: { period: { date_from?: string; date_to?: string } }) {
  const [page, setPage] = React.useState(1);
  const query = useTripResultsQuery({ ...period, page, limit: 20 });
  if (query.isLoading) return <LoadingState rows={6} />;
  if (query.error || !query.data)
    return <ErrorState title="Não foi possível carregar as Viagens" onRetry={() => query.refetch()} />;
  if (query.data.data.length === 0)
    return <EmptyState icon={BarChart3} title="Nenhuma Viagem no período" description="Ajuste o período ou aguarde novas Viagens finalizadas." />;
  return (
    <div className="flex flex-col gap-4">
      <TripResultsTable trips={query.data.data} />
      <Pagination
        page={query.data.meta.pagination.page}
        limit={query.data.meta.pagination.limit}
        total={query.data.meta.pagination.total}
        onPageChange={setPage}
      />
    </div>
  );
}

function VehiclesTab({ period }: { period: { date_from?: string; date_to?: string } }) {
  const query = useVehicleResultsQuery(period);
  if (query.isLoading) return <LoadingState rows={6} />;
  if (query.error || !query.data)
    return <ErrorState title="Não foi possível carregar os Veículos" onRetry={() => query.refetch()} />;
  if (query.data.length === 0)
    return <EmptyState icon={BarChart3} title="Nenhum Veículo com atividade no período" />;
  return <VehicleResultsTable vehicles={query.data} />;
}

function ClientsTab({ period }: { period: { date_from?: string; date_to?: string } }) {
  const query = useClientResultsQuery(period);
  if (query.isLoading) return <LoadingState rows={6} />;
  if (query.error || !query.data)
    return <ErrorState title="Não foi possível carregar os Clientes" onRetry={() => query.refetch()} />;
  if (query.data.length === 0)
    return <EmptyState icon={BarChart3} title="Nenhum Cliente com atividade no período" />;
  return <ClientResultsTable clients={query.data} />;
}

function DriversTab({ period }: { period: { date_from?: string; date_to?: string } }) {
  const query = useDriverResultsQuery(period);
  if (query.isLoading) return <LoadingState rows={6} />;
  if (query.error || !query.data)
    return <ErrorState title="Não foi possível carregar os Motoristas" onRetry={() => query.refetch()} />;
  if (query.data.length === 0)
    return <EmptyState icon={BarChart3} title="Nenhum Motorista com atividade no período" />;
  return <DriverResultsTable drivers={query.data} />;
}

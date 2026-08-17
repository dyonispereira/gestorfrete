"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@gestorfrete/ui";
import { LineChart } from "lucide-react";

import { useSession } from "@/core/tenant/session-provider";
import { LoadingState } from "@/shared/components/states/loading-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { EmptyState } from "@/shared/components/states/empty-state";

export default function DashboardPage() {
  const { user, tenant, isLoading, error } = useSession();

  if (isLoading) return <LoadingState rows={5} />;
  if (error) return <ErrorState description={error.message} onRetry={() => window.location.reload()} />;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Olá, {user?.nome.split(" ")[0]}</h1>
        <p className="text-sm text-muted-foreground">
          {tenant?.razao_social} — sessão autenticada via {"/auth/me"}.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Indicadores operacionais</CardTitle>
          <CardDescription>
            Os dashboards reais (BI, Sprint 12 Lote posterior) consomem {"reporting.dashboard"}; este lote
            entrega a fundação visual, não os dados de negócio.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={LineChart}
            title="Sem indicadores ainda"
            description="Os KPIs operacionais chegam junto com o Lote de Operação/Viagens e o Lote de BI."
          />
        </CardContent>
      </Card>
    </div>
  );
}

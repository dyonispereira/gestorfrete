"use client";

import { useParams } from "next/navigation";

import { Button, Card, CardContent, CardHeader, CardTitle, Tabs, TabsContent, TabsList, TabsTrigger, toast } from "@gestorfrete/ui";

import { usePermissions } from "@/core/rbac/permissions-provider";
import {
  useActivatePriceTableMutation,
  useExpirePriceTableMutation,
  usePriceTableQuery,
} from "@/modules/pricing/hooks/use-price-tables";
import { useClientQuery } from "@/modules/crm/hooks/use-clients";
import { PriceTableStatusBadge } from "@/modules/pricing/components/price-table-status-badge";
import { PriceTableItemsTab } from "@/modules/pricing/components/price-table-items-tab";
import { ApiError } from "@/shared/lib/api-client";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

export default function PriceTableDetailPage() {
  const params = useParams<{ id: string }>();
  const priceTableId = params.id;
  const { hasPermission } = usePermissions();

  const priceTableQuery = usePriceTableQuery(priceTableId);
  const table = priceTableQuery.data;
  useBreadcrumbLabel(`/tabelas-frete/${priceTableId}`, table?.nome);

  const activate = useActivatePriceTableMutation();
  const expire = useExpirePriceTableMutation();
  const canEdit = hasPermission("pricing.price_table.edit");

  async function handleActivate() {
    try {
      await activate.mutateAsync(priceTableId);
      toast.success("Tabela ativada — vigente a partir de agora.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível ativar a tabela.");
    }
  }

  async function handleExpire() {
    try {
      await expire.mutateAsync(priceTableId);
      toast.success("Tabela expirada.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível expirar a tabela.");
    }
  }

  const clientQuery = useClientQuery(table?.cliente_id);

  if (priceTableQuery.isLoading) return <LoadingState rows={6} />;
  if (priceTableQuery.error || !table)
    return (
      <ErrorState
        title="Não foi possível carregar a tabela de frete"
        description={priceTableQuery.error instanceof Error ? priceTableQuery.error.message : undefined}
        onRetry={() => priceTableQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{table.nome}</h1>
          <div className="mt-2 flex items-center gap-2">
            <PriceTableStatusBadge status={table.status} />
            <span className="text-sm text-muted-foreground">v{table.versao}</span>
          </div>
        </div>
        {canEdit && table.status === "RASCUNHO" ? (
          <Button onClick={handleActivate} disabled={activate.isPending}>
            {activate.isPending ? "Ativando…" : "Ativar tabela"}
          </Button>
        ) : null}
        {canEdit && table.status === "VIGENTE" ? (
          <Button variant="destructive" onClick={handleExpire} disabled={expire.isPending}>
            {expire.isPending ? "Expirando…" : "Expirar tabela"}
          </Button>
        ) : null}
      </div>

      <Tabs defaultValue="cabecalho">
        <TabsList>
          <TabsTrigger value="cabecalho">Cabeçalho</TabsTrigger>
          <TabsTrigger value="itens">Itens</TabsTrigger>
        </TabsList>

        <TabsContent value="cabecalho">
          <Card>
            <CardHeader>
              <CardTitle>Dados da tabela</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2 text-sm">
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Direção</span>
                <span className="font-medium">{table.direcao === "VENDA" ? "Venda" : "Compra"}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Cliente</span>
                <span className="font-medium">{clientQuery.data?.razao_social ?? "Todos os clientes"}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Vigência</span>
                <span className="font-medium">
                  {new Date(table.vigencia_inicio).toLocaleDateString("pt-BR")}
                  {table.vigencia_fim ? ` – ${new Date(table.vigencia_fim).toLocaleDateString("pt-BR")}` : " – sem fim definido"}
                </span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="itens">
          <PriceTableItemsTab priceTableId={priceTableId} tableStatus={table.status} canEdit={canEdit} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

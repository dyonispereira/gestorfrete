"use client";

import { useParams } from "next/navigation";
import Link from "next/link";

import { Badge, Card, CardContent, CardDescription, CardHeader, CardTitle, Tabs, TabsContent, TabsList, TabsTrigger } from "@gestorfrete/ui";

import { useMdfeQuery } from "@/modules/documents/hooks/use-mdfes";
import { MdfeCommandsPanel } from "@/modules/documents/components/mdfe-commands-panel";
import { MdfeStatusBadge } from "@/modules/documents/components/mdfe-status-badge";
import { MdfeStatusHistory } from "@/modules/documents/components/mdfe-status-history";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

export default function MdfeDetailPage() {
  const params = useParams<{ id: string }>();
  const mdfeId = params.id;

  const mdfeQuery = useMdfeQuery(mdfeId);
  const mdfe = mdfeQuery.data;
  useBreadcrumbLabel(`/mdfes/${mdfeId}`, mdfe ? `${mdfe.number}/${mdfe.series}` : undefined);

  if (mdfeQuery.isLoading) return <LoadingState rows={6} />;
  if (mdfeQuery.error || !mdfe)
    return (
      <ErrorState
        title="Não foi possível carregar o MDF-e"
        description={mdfeQuery.error instanceof Error ? mdfeQuery.error.message : undefined}
        onRetry={() => mdfeQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          MDF-e {mdfe.number}/{mdfe.series}
        </h1>
        <div className="mt-2">
          <MdfeStatusBadge status={mdfe.status} />
        </div>
      </div>

      <MdfeCommandsPanel mdfe={mdfe} />

      <Tabs defaultValue="visao-geral">
        <TabsList>
          <TabsTrigger value="visao-geral">Visão Geral</TabsTrigger>
          <TabsTrigger value="historico">Histórico</TabsTrigger>
        </TabsList>

        <TabsContent value="visao-geral">
          <Card>
            <CardHeader>
              <CardTitle>Dados do MDF-e</CardTitle>
              <CardDescription>Consolida um ou mais CT-e Autorizados da mesma viagem.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3 text-sm">
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Viagem</span>
                <span className="font-medium">{mdfe.trip_id}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Chave de acesso</span>
                <span className="font-medium">{mdfe.access_key ?? "—"}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Protocolo SEFAZ</span>
                <span className="font-medium">{mdfe.sefaz_protocol ?? "—"}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Encerrado em</span>
                <span className="font-medium">{mdfe.closed_at ? new Date(mdfe.closed_at).toLocaleString("pt-BR") : "—"}</span>
              </div>
              <div>
                <span className="text-muted-foreground">CT-e vinculados</span>
                <div className="mt-1 flex flex-wrap gap-2">
                  {mdfe.cte_ids.map((cteId) => (
                    <Link key={cteId} href={`/ctes/${cteId}`}>
                      <Badge variant="outline">{cteId.slice(0, 8)}</Badge>
                    </Link>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="historico">
          <MdfeStatusHistory mdfeId={mdfeId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

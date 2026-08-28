"use client";

import { useParams } from "next/navigation";

import { Card, CardContent, CardDescription, CardHeader, CardTitle, Tabs, TabsContent, TabsList, TabsTrigger } from "@gestorfrete/ui";

import { useCteQuery } from "@/modules/documents/hooks/use-ctes";
import { CteCommandsPanel } from "@/modules/documents/components/cte-commands-panel";
import { CteStatusBadge } from "@/modules/documents/components/cte-status-badge";
import { CteStatusHistory } from "@/modules/documents/components/cte-status-history";
import { CorrectionLettersTab } from "@/modules/documents/components/correction-letters-tab";
import { ReferencedNfesTab } from "@/modules/documents/components/referenced-nfes-tab";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

export default function CteDetailPage() {
  const params = useParams<{ id: string }>();
  const cteId = params.id;

  const cteQuery = useCteQuery(cteId);
  const cte = cteQuery.data;
  useBreadcrumbLabel(`/ctes/${cteId}`, cte ? `${cte.number}/${cte.series}` : undefined);

  if (cteQuery.isLoading) return <LoadingState rows={6} />;
  if (cteQuery.error || !cte)
    return (
      <ErrorState
        title="Não foi possível carregar o CT-e"
        description={cteQuery.error instanceof Error ? cteQuery.error.message : undefined}
        onRetry={() => cteQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          CT-e {cte.number}/{cte.series}
        </h1>
        <div className="mt-2">
          <CteStatusBadge status={cte.status} />
        </div>
      </div>

      <CteCommandsPanel cte={cte} />

      <Tabs defaultValue="visao-geral">
        <TabsList>
          <TabsTrigger value="visao-geral">Visão Geral</TabsTrigger>
          <TabsTrigger value="historico">Histórico</TabsTrigger>
          <TabsTrigger value="correcoes">Correções</TabsTrigger>
          <TabsTrigger value="nfe-referenciada">NF-e Referenciada</TabsTrigger>
        </TabsList>

        <TabsContent value="visao-geral">
          <Card>
            <CardHeader>
              <CardTitle>Dados do CT-e</CardTitle>
              <CardDescription>Valores capturados no momento da emissão — nunca ressincronizados.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-2 text-sm">
              <Row label="Viagem" value={cte.trip_id} />
              <Row label="Valor do serviço" value={Number(cte.service_value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })} />
              <Row label="Chave de acesso" value={cte.access_key} />
              <Row label="Protocolo SEFAZ" value={cte.sefaz_protocol} />
              <Row label="Autorizado em" value={cte.authorized_at ? new Date(cte.authorized_at).toLocaleString("pt-BR") : undefined} />
              <Row label="XML" value={cte.xml_file_id ? "Disponível (referência em Storage)" : "Não disponível ainda"} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="historico">
          <CteStatusHistory cteId={cteId} />
        </TabsContent>

        <TabsContent value="correcoes">
          <CorrectionLettersTab cteId={cteId} cteStatus={cte.status} />
        </TabsContent>

        <TabsContent value="nfe-referenciada">
          <ReferencedNfesTab cteId={cteId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string | undefined }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value ?? "—"}</span>
    </div>
  );
}

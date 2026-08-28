"use client";

import * as React from "react";
import { FileText } from "lucide-react";

import { Input, Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { CteStatus } from "@gestorfrete/types";

import { useCtesQuery } from "@/modules/documents/hooks/use-ctes";
import { CtesTable } from "@/modules/documents/components/ctes-table";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const STATUS_OPTIONS: Array<{ value: "all" | CteStatus; label: string }> = [
  { value: "all", label: "Todos os status" },
  { value: "RASCUNHO", label: "Rascunho" },
  { value: "VALIDADO", label: "Validado" },
  { value: "ASSINADO", label: "Assinado" },
  { value: "TRANSMITIDO", label: "Transmitido" },
  { value: "AUTORIZADO", label: "Autorizado" },
  { value: "CANCELADO", label: "Cancelado" },
  { value: "DENEGADO", label: "Denegado" },
  { value: "INUTILIZADO", label: "Inutilizado" },
];

export default function CtesPage() {
  const [page, setPage] = React.useState(1);
  const [accessKey, setAccessKey] = React.useState("");
  const [status, setStatus] = React.useState<"all" | CteStatus>("all");

  const ctesQuery = useCtesQuery({
    page,
    limit: 20,
    access_key: accessKey || undefined,
    status: status === "all" ? undefined : status,
  });

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">CT-e</h1>
        <p className="text-sm text-muted-foreground">
          Conhecimentos de Transporte Eletrônico. Criados automaticamente ao despachar uma viagem — sem criação manual.
        </p>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          placeholder="Buscar por chave de acesso…"
          value={accessKey}
          onChange={(event) => {
            setAccessKey(event.target.value);
            setPage(1);
          }}
          className="sm:max-w-xs"
        />
        <Select
          value={status}
          onValueChange={(value) => {
            setStatus(value as "all" | CteStatus);
            setPage(1);
          }}
        >
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
      </div>

      {ctesQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : ctesQuery.error ? (
        <ErrorState
          title="Não foi possível carregar os CT-e"
          description={ctesQuery.error instanceof Error ? ctesQuery.error.message : undefined}
          onRetry={() => ctesQuery.refetch()}
        />
      ) : ctesQuery.data && ctesQuery.data.data.length > 0 ? (
        <>
          <CtesTable ctes={ctesQuery.data.data} />
          <Pagination
            page={ctesQuery.data.meta.pagination.page}
            limit={ctesQuery.data.meta.pagination.limit}
            total={ctesQuery.data.meta.pagination.total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={FileText} title="Nenhum CT-e encontrado" description="Ajuste a busca/filtro, ou despache uma viagem." />
      )}
    </div>
  );
}

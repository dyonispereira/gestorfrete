"use client";

import * as React from "react";
import { ClipboardCheck } from "lucide-react";

import { Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { ChecklistStatus } from "@gestorfrete/types";

import { useChecklistsQuery } from "@/modules/maintenance/hooks/use-checklists";
import { ChecklistsTable } from "@/modules/maintenance/components/checklists-table";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const STATUS_OPTIONS: Array<{ value: "all" | ChecklistStatus; label: string }> = [
  { value: "all", label: "Todos os status" },
  { value: "PENDENTE", label: "Pendente" },
  { value: "EM_PREENCHIMENTO", label: "Em preenchimento" },
  { value: "CONCLUIDO", label: "Concluído" },
  { value: "APROVADO", label: "Aprovado" },
  { value: "REPROVADO", label: "Reprovado" },
];

/** Consulta/auditoria — a interação real acontece embutida na Viagem (aba Checklist). */
export default function ChecklistsPage() {
  const [page, setPage] = React.useState(1);
  const [status, setStatus] = React.useState<"all" | ChecklistStatus>("all");

  const checklistsQuery = useChecklistsQuery({ page, limit: 20, status: status === "all" ? undefined : status });

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Checklists</h1>
        <p className="text-sm text-muted-foreground">Verificações de saída/retorno de motorista, oficina e outras.</p>
      </div>

      <Select
        value={status}
        onValueChange={(value) => {
          setStatus(value as "all" | ChecklistStatus);
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

      {checklistsQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : checklistsQuery.error ? (
        <ErrorState
          title="Não foi possível carregar os checklists"
          description={checklistsQuery.error instanceof Error ? checklistsQuery.error.message : undefined}
          onRetry={() => checklistsQuery.refetch()}
        />
      ) : checklistsQuery.data && checklistsQuery.data.data.length > 0 ? (
        <>
          <ChecklistsTable checklists={checklistsQuery.data.data} />
          <Pagination
            page={checklistsQuery.data.meta.pagination.page}
            limit={checklistsQuery.data.meta.pagination.limit}
            total={checklistsQuery.data.meta.pagination.total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={ClipboardCheck} title="Nenhum checklist encontrado" description="Ajuste o filtro, ou crie um checklist a partir de uma viagem." />
      )}
    </div>
  );
}

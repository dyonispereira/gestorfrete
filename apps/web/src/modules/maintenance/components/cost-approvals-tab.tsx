"use client";

import { Gavel } from "lucide-react";

import { Badge } from "@gestorfrete/ui";
import type { CostApprovalDecision } from "@gestorfrete/types";

import { useCostApprovalsQuery } from "@/modules/maintenance/hooks/use-cost-approvals";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const DECISION_VARIANT: Record<CostApprovalDecision, "success" | "destructive"> = {
  APROVADO: "success",
  REJEITADO: "destructive",
};
const DECISION_LABEL: Record<CostApprovalDecision, string> = { APROVADO: "Aprovado", REJEITADO: "Rejeitado" };

/** Registro pontual, nunca alterado depois de criado — só consulta aqui, sem nenhuma ação. */
export function CostApprovalsTab({ workOrderId }: { workOrderId: string }) {
  const approvalsQuery = useCostApprovalsQuery(workOrderId);

  if (approvalsQuery.isLoading) return <LoadingState rows={2} />;
  if (approvalsQuery.error)
    return <ErrorState description="Não foi possível carregar as aprovações de custo." onRetry={() => approvalsQuery.refetch()} />;

  const approvals = approvalsQuery.data?.data ?? [];

  if (approvals.length === 0) return <EmptyState icon={Gavel} title="Nenhuma aprovação de custo registrada" />;

  return (
    <div className="flex flex-col gap-2">
      {approvals.map((approval) => (
        <div key={approval.id} className="rounded-md border border-border p-3">
          <div className="flex items-center gap-2">
            <Badge variant={DECISION_VARIANT[approval.decision]}>{DECISION_LABEL[approval.decision]}</Badge>
            <span className="text-xs text-muted-foreground">Nível {approval.level}</span>
            <span className="text-xs text-muted-foreground">{new Date(approval.occurred_at).toLocaleString("pt-BR")}</span>
          </div>
          {approval.justification ? <p className="mt-1 text-sm">{approval.justification}</p> : null}
        </div>
      ))}
    </div>
  );
}

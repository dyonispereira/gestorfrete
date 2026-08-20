"use client";

import * as React from "react";
import { useParams } from "next/navigation";

import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  toast,
} from "@gestorfrete/ui";
import type { CostCenterStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useCostCenterQuery, useUpdateCostCenterMutation } from "@/modules/financial/hooks/use-cost-centers";
import { ApiError } from "@/shared/lib/api-client";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

const VARIANT_BY_STATUS: Record<CostCenterStatus, "success" | "secondary"> = { ATIVO: "success", INATIVO: "secondary" };
const LABEL_BY_STATUS: Record<CostCenterStatus, string> = { ATIVO: "Ativo", INATIVO: "Inativo" };

/**
 * No delete button — `cost_center_router.py` has no DELETE endpoint (D-note in code: RBAC_MATRIX
 * has no `financial.cost_center.delete`). Deactivation is `status: INATIVO` through the same form.
 */
export default function CostCenterDetailPage() {
  const params = useParams<{ id: string }>();
  const costCenterId = params.id;
  const { hasPermission } = usePermissions();

  const costCenterQuery = useCostCenterQuery(costCenterId);
  const updateCostCenter = useUpdateCostCenterMutation(costCenterId);

  const costCenter = costCenterQuery.data;
  useBreadcrumbLabel(`/centros-custo/${costCenterId}`, costCenter?.nome);

  const [nome, setNome] = React.useState("");
  const [status, setStatus] = React.useState<CostCenterStatus>("ATIVO");

  React.useEffect(() => {
    if (!costCenter) return;
    setNome(costCenter.nome);
    setStatus(costCenter.status);
  }, [costCenter]);

  const canEdit = hasPermission("financial.cost_center.edit");

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    try {
      await updateCostCenter.mutateAsync({ nome, status });
      toast.success("Centro de custo atualizado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível salvar.");
    }
  }

  if (costCenterQuery.isLoading) return <LoadingState rows={6} />;
  if (costCenterQuery.error || !costCenter)
    return (
      <ErrorState
        title="Não foi possível carregar o centro de custo"
        description={costCenterQuery.error instanceof Error ? costCenterQuery.error.message : undefined}
        onRetry={() => costCenterQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">{costCenter.nome}</h1>
        <div className="mt-1 flex items-center gap-2">
          <Badge variant={VARIANT_BY_STATUS[costCenter.status]}>{LABEL_BY_STATUS[costCenter.status]}</Badge>
          <span className="text-sm text-muted-foreground">{costCenter.accounting_code}</span>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Dados do centro de custo</CardTitle>
          <CardDescription>
            {canEdit ? "Código contábil não pode ser alterado." : "Somente leitura."} Sem excluir — desative mudando o status.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="flex flex-col gap-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="detail-nome">Nome</Label>
                <Input id="detail-nome" disabled={!canEdit} value={nome} onChange={(event) => setNome(event.target.value)} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label>Status</Label>
                <Select value={status} onValueChange={(value) => setStatus(value as CostCenterStatus)} disabled={!canEdit}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ATIVO">Ativo</SelectItem>
                    <SelectItem value="INATIVO">Inativo</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            {canEdit ? (
              <div className="flex justify-end">
                <Button type="submit" disabled={updateCostCenter.isPending}>
                  {updateCostCenter.isPending ? "Salvando…" : "Salvar alterações"}
                </Button>
              </div>
            ) : null}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

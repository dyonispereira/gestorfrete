"use client";

import * as React from "react";

import {
  Button,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  Textarea,
  toast,
} from "@gestorfrete/ui";
import type { WorkOrderType } from "@gestorfrete/types";

import { useVehiclesQuery } from "@/modules/fleet/hooks/use-vehicles";
import { useSuppliersQuery } from "@/modules/maintenance/hooks/use-suppliers";
import { useCreateWorkOrderMutation } from "@/modules/maintenance/hooks/use-work-orders";
import { useCostCentersQuery } from "@/modules/financial/hooks/use-cost-centers";
import { useChartOfAccountsListQuery } from "@/modules/financial/hooks/use-chart-of-accounts";
import { ApiError } from "@/shared/lib/api-client";

const TYPE_LABEL: Record<WorkOrderType, string> = {
  PREVENTIVA: "Preventiva",
  CORRETIVA: "Corretiva",
  EMERGENCIAL: "Emergencial",
  GARANTIA: "Garantia",
};

interface WorkOrderFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** Nasce ABERTA. `origin_abertura` fica MANUAL — CHECKLIST_REPROVADO só é usado pelo gatilho
 * automático da reprovação de Checklist Oficina, nunca escolhido aqui. */
export function WorkOrderFormDrawer({ open, onOpenChange }: WorkOrderFormDrawerProps) {
  const [tractorUnitId, setTractorUnitId] = React.useState("");
  const [type, setType] = React.useState<WorkOrderType>("CORRETIVA");
  const [problemDescription, setProblemDescription] = React.useState("");
  const [openingOdometerKm, setOpeningOdometerKm] = React.useState("");
  const [supplierId, setSupplierId] = React.useState("");
  const [costCenterId, setCostCenterId] = React.useState("");
  const [chartOfAccountsId, setChartOfAccountsId] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const vehiclesQuery = useVehiclesQuery({ limit: 100 });
  const suppliersQuery = useSuppliersQuery({ limit: 100 });
  const costCentersQuery = useCostCentersQuery({ limit: 100 });
  const chartQuery = useChartOfAccountsListQuery({ limit: 100, type: "DESPESA" });
  const createWorkOrder = useCreateWorkOrderMutation();

  function reset() {
    setTractorUnitId("");
    setType("CORRETIVA");
    setProblemDescription("");
    setOpeningOdometerKm("");
    setSupplierId("");
    setCostCenterId("");
    setChartOfAccountsId("");
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createWorkOrder.mutateAsync({
        tractor_unit_id: tractorUnitId, type, problem_description: problemDescription,
        opening_odometer_km: openingOdometerKm || undefined, supplier_id: supplierId || undefined,
        cost_center_id: costCenterId || undefined, chart_of_accounts_id: chartOfAccountsId || undefined,
      });
      toast.success("Ordem de serviço criada.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar a ordem de serviço.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Nova ordem de serviço</SheetTitle>
          <SheetDescription>Nasce Aberta — o diagnóstico é registrado depois, na aba de detalhe.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="work-order-tractor-unit">Veículo</Label>
            <Select value={tractorUnitId} onValueChange={setTractorUnitId}>
              <SelectTrigger id="work-order-tractor-unit">
                <SelectValue placeholder="Selecione um veículo" />
              </SelectTrigger>
              <SelectContent>
                {vehiclesQuery.data?.data.map((vehicle) => (
                  <SelectItem key={vehicle.id} value={vehicle.id}>
                    {vehicle.identity.plate}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="work-order-type">Tipo</Label>
            <Select value={type} onValueChange={(value) => setType(value as WorkOrderType)}>
              <SelectTrigger id="work-order-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(TYPE_LABEL) as WorkOrderType[]).map((value) => (
                  <SelectItem key={value} value={value}>
                    {TYPE_LABEL[value]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="work-order-problem-description">Descrição do problema</Label>
            <Textarea
              id="work-order-problem-description"
              required
              value={problemDescription}
              onChange={(event) => setProblemDescription(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="work-order-opening-odometer">Hodômetro na abertura (opcional)</Label>
            <Input
              id="work-order-opening-odometer"
              type="number"
              step="0.01"
              value={openingOdometerKm}
              onChange={(event) => setOpeningOdometerKm(event.target.value)}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="work-order-supplier">Fornecedor executor (opcional)</Label>
            <Select value={supplierId} onValueChange={setSupplierId}>
              <SelectTrigger id="work-order-supplier">
                <SelectValue placeholder="Mão de obra interna, sem fornecedor" />
              </SelectTrigger>
              <SelectContent>
                {suppliersQuery.data?.data.map((supplier) => (
                  <SelectItem key={supplier.id} value={supplier.id}>
                    {supplier.razao_social}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="work-order-cost-center">Centro de custo (opcional)</Label>
            <Select value={costCenterId} onValueChange={setCostCenterId}>
              <SelectTrigger id="work-order-cost-center">
                <SelectValue placeholder="Sem centro de custo" />
              </SelectTrigger>
              <SelectContent>
                {costCentersQuery.data?.data.map((costCenter) => (
                  <SelectItem key={costCenter.id} value={costCenter.id}>
                    {costCenter.nome}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="work-order-chart">Plano de contas (opcional)</Label>
            <Select value={chartOfAccountsId} onValueChange={setChartOfAccountsId}>
              <SelectTrigger id="work-order-chart">
                <SelectValue placeholder="Sem conta contábil" />
              </SelectTrigger>
              <SelectContent>
                {chartQuery.data?.data.map((account) => (
                  <SelectItem key={account.id} value={account.id}>
                    {account.account_code} — {account.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <p className="text-xs text-muted-foreground">
            Fornecedor + Centro de custo + Plano de contas, todos preenchidos, habilitam a Conta a Pagar
            automática quando a OS for fechada.
          </p>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createWorkOrder.isPending || !tractorUnitId}>
              {createWorkOrder.isPending ? "Criando…" : "Criar ordem de serviço"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

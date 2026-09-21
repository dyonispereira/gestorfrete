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
  toast,
} from "@gestorfrete/ui";
import type { PayableOrigin } from "@gestorfrete/types";

import { useSuppliersQuery } from "@/modules/maintenance/hooks/use-suppliers";
import { useCostCentersQuery } from "@/modules/financial/hooks/use-cost-centers";
import { useChartOfAccountsListQuery } from "@/modules/financial/hooks/use-chart-of-accounts";
import { useCreateAccountsPayableMutation } from "@/modules/financial/hooks/use-accounts-payable";
import { useVehiclesQuery } from "@/modules/fleet/hooks/use-vehicles";
import { useDriversQuery } from "@/modules/drivers/hooks/use-drivers";
import { useTripsQuery } from "@/modules/freight/hooks/use-trips";
import { useWorkOrdersQuery } from "@/modules/maintenance/hooks/use-work-orders";
import { ApiError } from "@/shared/lib/api-client";

const ORIGIN_LABEL: Record<PayableOrigin, string> = {
  VIAGEM: "Viagem",
  ORDEM_SERVICO: "Ordem de Serviço",
  ABASTECIMENTO: "Abastecimento",
  COMPRA: "Compra",
  AJUSTE_MANUAL: "Ajuste manual",
};

interface AccountsPayableFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function currentMonthCompetencia(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-01`;
}

/** A maioria das Contas a Pagar de Ordem de Serviço nasce sozinha no fechamento da OS (ver aba
 * "Origem" da tela de detalhe) — este formulário cobre o lançamento manual: Abastecimento, Compra,
 * Ajuste Manual, ou um custo adicional de Viagem/OS que o automático não cobriu. */
export function AccountsPayableFormDrawer({ open, onOpenChange }: AccountsPayableFormDrawerProps) {
  const [supplierId, setSupplierId] = React.useState("");
  const [costCenterId, setCostCenterId] = React.useState("");
  const [chartOfAccountsId, setChartOfAccountsId] = React.useState("");
  const [origin, setOrigin] = React.useState<PayableOrigin>("AJUSTE_MANUAL");
  const [tripId, setTripId] = React.useState("");
  const [maintenanceOrderId, setMaintenanceOrderId] = React.useState("");
  const [vehicleId, setVehicleId] = React.useState("");
  const [driverId, setDriverId] = React.useState("");
  const [value, setValue] = React.useState("");
  const [dueDate, setDueDate] = React.useState("");
  const [accountingPeriod, setAccountingPeriod] = React.useState(currentMonthCompetencia());
  const [formError, setFormError] = React.useState<string | null>(null);

  const suppliersQuery = useSuppliersQuery({ limit: 100 });
  const costCentersQuery = useCostCentersQuery({ limit: 100 });
  const chartQuery = useChartOfAccountsListQuery({ limit: 100, type: "DESPESA" });
  const vehiclesQuery = useVehiclesQuery({ limit: 100 });
  const driversQuery = useDriversQuery({ limit: 100 });
  const tripsQuery = useTripsQuery({ limit: 50 });
  const workOrdersQuery = useWorkOrdersQuery({ limit: 50 });
  const createPayable = useCreateAccountsPayableMutation();

  function reset() {
    setSupplierId(""); setCostCenterId(""); setChartOfAccountsId(""); setOrigin("AJUSTE_MANUAL");
    setTripId(""); setMaintenanceOrderId(""); setVehicleId(""); setDriverId("");
    setValue(""); setDueDate(""); setAccountingPeriod(currentMonthCompetencia()); setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createPayable.mutateAsync({
        supplier_id: supplierId, cost_center_id: costCenterId, origin, value, due_date: dueDate,
        accounting_period: accountingPeriod, chart_of_accounts_id: chartOfAccountsId,
        trip_id: origin === "VIAGEM" ? tripId || undefined : undefined,
        maintenance_order_id: origin === "ORDEM_SERVICO" ? maintenanceOrderId || undefined : undefined,
        vehicle_id: vehicleId || undefined, driver_id: driverId || undefined,
      });
      toast.success("Conta a pagar criada.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar a conta a pagar.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Nova conta a pagar</SheetTitle>
          <SheetDescription>Lançamento manual — custos de Ordem de Serviço fechada nascem automaticamente.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="payable-supplier">Fornecedor</Label>
            <Select value={supplierId} onValueChange={setSupplierId}>
              <SelectTrigger id="payable-supplier">
                <SelectValue placeholder="Selecione um fornecedor" />
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
            <Label htmlFor="payable-cost-center">Centro de custo</Label>
            <Select value={costCenterId} onValueChange={setCostCenterId}>
              <SelectTrigger id="payable-cost-center">
                <SelectValue placeholder="Selecione um centro de custo" />
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
            <Label htmlFor="payable-chart">Plano de contas</Label>
            <Select value={chartOfAccountsId} onValueChange={setChartOfAccountsId}>
              <SelectTrigger id="payable-chart">
                <SelectValue placeholder="Selecione uma conta contábil" />
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

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="payable-origin">Origem</Label>
            <Select value={origin} onValueChange={(v) => setOrigin(v as PayableOrigin)}>
              <SelectTrigger id="payable-origin">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(ORIGIN_LABEL) as PayableOrigin[]).map((value) => (
                  <SelectItem key={value} value={value}>
                    {ORIGIN_LABEL[value]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {origin === "VIAGEM" ? (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="payable-trip">Viagem</Label>
              <Select value={tripId} onValueChange={setTripId}>
                <SelectTrigger id="payable-trip">
                  <SelectValue placeholder="Selecione a viagem" />
                </SelectTrigger>
                <SelectContent>
                  {tripsQuery.data?.data.map((trip) => (
                    <SelectItem key={trip.id} value={trip.id}>
                      {trip.codigo}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ) : null}

          {origin === "ORDEM_SERVICO" ? (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="payable-work-order">Ordem de Serviço</Label>
              <Select value={maintenanceOrderId} onValueChange={setMaintenanceOrderId}>
                <SelectTrigger id="payable-work-order">
                  <SelectValue placeholder="Selecione a ordem de serviço" />
                </SelectTrigger>
                <SelectContent>
                  {workOrdersQuery.data?.data.map((workOrder) => (
                    <SelectItem key={workOrder.id} value={workOrder.id}>
                      {workOrder.codigo}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ) : null}

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="payable-vehicle">Veículo (opcional)</Label>
            <Select value={vehicleId} onValueChange={setVehicleId}>
              <SelectTrigger id="payable-vehicle">
                <SelectValue placeholder="Sem vínculo com veículo" />
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
            <Label htmlFor="payable-driver">Motorista (opcional — só quando o custo é do motorista)</Label>
            <Select value={driverId} onValueChange={setDriverId}>
              <SelectTrigger id="payable-driver">
                <SelectValue placeholder="Sem vínculo com motorista" />
              </SelectTrigger>
              <SelectContent>
                {driversQuery.data?.data.map((driver) => (
                  <SelectItem key={driver.id} value={driver.id}>
                    {driver.nome}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="payable-value">Valor</Label>
              <Input id="payable-value" type="number" step="0.01" required value={value} onChange={(e) => setValue(e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="payable-due-date">Vencimento</Label>
              <Input id="payable-due-date" type="date" required value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="payable-competencia">Competência</Label>
            <Input
              id="payable-competencia" type="date" required value={accountingPeriod}
              onChange={(e) => setAccountingPeriod(e.target.value)}
            />
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createPayable.isPending || !supplierId || !costCenterId || !chartOfAccountsId}>
              {createPayable.isPending ? "Criando…" : "Criar conta a pagar"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

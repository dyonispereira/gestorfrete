"use client";

import * as React from "react";

import {
  Button,
  Checkbox,
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
import type { WorkOrder, WorkOrderCause } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import {
  useAprovarCustoWorkOrderMutation,
  useCancelarWorkOrderMutation,
  useConcluirWorkOrderMutation,
  useDiagnosticarWorkOrderMutation,
  useFecharWorkOrderMutation,
  useIniciarExecucaoWorkOrderMutation,
  useReprovarCustoWorkOrderMutation,
  useSubmeterAprovacaoWorkOrderMutation,
} from "@/modules/maintenance/hooks/use-work-orders";
import { ApiError } from "@/shared/lib/api-client";

const CAUSA_LABEL: Record<WorkOrderCause, string> = {
  DESGASTE: "Desgaste",
  QUEBRA: "Quebra",
  ACIDENTE: "Acidente",
  MAU_USO: "Mau uso",
  INSPECAO: "Inspeção",
  RECALL: "Recall",
};

type TextDialogKey = "reprovar-custo" | "cancelar";

/**
 * Só renderiza o(s) comando(s) válido(s) para o `status` atual — mesmo princípio do
 * `TripCommandsPanel`/`CteCommandsPanel`. `AGUARDANDO_PECA` nunca aparece (fora de escopo nesta
 * Lote — sem subsistema de peças real por trás). `FECHADA`/`CANCELADA` são terminais, sem botão
 * algum, nunca reabertas.
 */
export function WorkOrderCommandsPanel({ workOrder }: { workOrder: WorkOrder }) {
  const { hasPermission } = usePermissions();
  const status = workOrder.status;

  const [diagnoseOpen, setDiagnoseOpen] = React.useState(false);
  const [technicalDiagnosis, setTechnicalDiagnosis] = React.useState("");
  const [cause, setCause] = React.useState<WorkOrderCause | "">("");
  const [rootCause, setRootCause] = React.useState("");
  const [needsApproval, setNeedsApproval] = React.useState(false);
  const [diagnoseError, setDiagnoseError] = React.useState<string | null>(null);

  const [textDialog, setTextDialog] = React.useState<TextDialogKey | null>(null);
  const [text, setText] = React.useState("");

  const diagnosticar = useDiagnosticarWorkOrderMutation();
  const submeterAprovacao = useSubmeterAprovacaoWorkOrderMutation();
  const aprovarCusto = useAprovarCustoWorkOrderMutation();
  const reprovarCusto = useReprovarCustoWorkOrderMutation();
  const iniciarExecucao = useIniciarExecucaoWorkOrderMutation();
  const concluir = useConcluirWorkOrderMutation();
  const fechar = useFecharWorkOrderMutation();
  const cancelar = useCancelarWorkOrderMutation();

  async function handleDiagnose(event: React.FormEvent) {
    event.preventDefault();
    setDiagnoseError(null);
    try {
      await diagnosticar.mutateAsync({
        workOrderId: workOrder.id,
        body: {
          technical_diagnosis: technicalDiagnosis || undefined, cause: cause || undefined,
          root_cause: rootCause || undefined, needs_approval: needsApproval,
        },
      });
      toast.success("Diagnóstico registrado.");
      setDiagnoseOpen(false);
    } catch (error) {
      setDiagnoseError(error instanceof ApiError ? error.message : "Não foi possível registrar o diagnóstico.");
    }
  }

  async function runSimple(action: () => Promise<unknown>, successMessage: string) {
    try {
      await action();
      toast.success(successMessage);
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível executar a ação.");
    }
  }

  async function handleTextDialogConfirm() {
    try {
      if (textDialog === "reprovar-custo") {
        await reprovarCusto.mutateAsync({ workOrderId: workOrder.id, body: { justification: text } });
        toast.success("Custo reprovado — de volta ao diagnóstico.");
      }
      if (textDialog === "cancelar") {
        await cancelar.mutateAsync({ workOrderId: workOrder.id, body: { justification: text } });
        toast.success("Ordem de serviço cancelada.");
      }
      setTextDialog(null);
      setText("");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível executar a ação.");
    }
  }

  const canEdit = hasPermission("maintenance.work_order.edit");
  const canApproveCost = hasPermission("maintenance.work_order.approve_cost");
  const canRejectCost = hasPermission("maintenance.work_order.reject_cost");
  const canClose = hasPermission("maintenance.work_order.close");
  const canCancel = hasPermission("maintenance.work_order.cancel");

  const buttons: React.ReactNode[] = [];

  if (status === "ABERTA" && canEdit) {
    buttons.push(
      <Button key="diagnosticar" onClick={() => setDiagnoseOpen(true)}>
        Diagnosticar
      </Button>
    );
  }
  if (status === "EM_DIAGNOSTICO" && canEdit) {
    buttons.push(
      <Button
        key="submeter-aprovacao"
        variant="outline"
        onClick={() => runSimple(() => submeterAprovacao.mutateAsync(workOrder.id), "Submetido para aprovação.")}
      >
        Submeter para aprovação
      </Button>,
      <Button key="iniciar-execucao" onClick={() => runSimple(() => iniciarExecucao.mutateAsync(workOrder.id), "Execução iniciada.")}>
        Iniciar execução
      </Button>
    );
  }
  if (status === "AGUARDANDO_APROVACAO") {
    if (canApproveCost) {
      buttons.push(
        <Button
          key="aprovar-custo"
          onClick={() => runSimple(() => aprovarCusto.mutateAsync({ workOrderId: workOrder.id }), "Custo aprovado.")}
        >
          Aprovar custo
        </Button>
      );
    }
    if (canRejectCost) {
      buttons.push(
        <Button key="reprovar-custo" variant="outline" onClick={() => setTextDialog("reprovar-custo")}>
          Reprovar custo
        </Button>
      );
    }
  }
  if (status === "EM_EXECUCAO" && canEdit) {
    buttons.push(
      <Button key="concluir" onClick={() => runSimple(() => concluir.mutateAsync(workOrder.id), "Ordem de serviço concluída.")}>
        Concluir
      </Button>
    );
  }
  if (status === "CONCLUIDA" && canClose) {
    buttons.push(
      <Button key="fechar" onClick={() => runSimple(() => fechar.mutateAsync(workOrder.id), "Ordem de serviço fechada.")}>
        Fechar
      </Button>
    );
  }
  if (["ABERTA", "EM_DIAGNOSTICO", "AGUARDANDO_APROVACAO"].includes(status) && canCancel) {
    buttons.push(
      <Button key="cancelar" variant="destructive" onClick={() => setTextDialog("cancelar")}>
        Cancelar
      </Button>
    );
  }

  const textDialogCopy: Record<TextDialogKey, { title: string; description: string; confirm: string }> = {
    "reprovar-custo": {
      title: "Reprovar custo",
      description: "Volta a ordem de serviço para Em Diagnóstico. Justificativa obrigatória.",
      confirm: "Reprovar custo",
    },
    cancelar: {
      title: "Cancelar ordem de serviço",
      description: "Só possível antes de Em Execução. Justificativa obrigatória.",
      confirm: "Cancelar ordem de serviço",
    },
  };

  return (
    <div className="flex flex-col gap-3">
      {buttons.length > 0 ? <div className="flex flex-wrap gap-2">{buttons}</div> : null}

      <Sheet open={diagnoseOpen} onOpenChange={setDiagnoseOpen}>
        <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Diagnosticar</SheetTitle>
            <SheetDescription>Registra o diagnóstico técnico e se esta OS precisa de aprovação de custo.</SheetDescription>
          </SheetHeader>
          <form onSubmit={handleDiagnose} className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="work-order-technical-diagnosis">Diagnóstico técnico</Label>
              <Textarea
                id="work-order-technical-diagnosis"
                value={technicalDiagnosis}
                onChange={(event) => setTechnicalDiagnosis(event.target.value)}
              />
            </div>
            {workOrder.type === "CORRETIVA" ? (
              <>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="work-order-cause">Causa</Label>
                  <Select value={cause} onValueChange={(value) => setCause(value as WorkOrderCause)}>
                    <SelectTrigger id="work-order-cause">
                      <SelectValue placeholder="Não informada" />
                    </SelectTrigger>
                    <SelectContent>
                      {(Object.keys(CAUSA_LABEL) as WorkOrderCause[]).map((value) => (
                        <SelectItem key={value} value={value}>
                          {CAUSA_LABEL[value]}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="work-order-root-cause">Causa raiz</Label>
                  <Textarea id="work-order-root-cause" value={rootCause} onChange={(event) => setRootCause(event.target.value)} />
                </div>
              </>
            ) : null}
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <Checkbox checked={needsApproval} onCheckedChange={(checked) => setNeedsApproval(checked === true)} />
              Precisa de aprovação de custo
            </label>

            {diagnoseError ? <p className="text-sm text-destructive">{diagnoseError}</p> : null}

            <div className="mt-auto flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setDiagnoseOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={diagnosticar.isPending}>
                {diagnosticar.isPending ? "Salvando…" : "Salvar diagnóstico"}
              </Button>
            </div>
          </form>
        </SheetContent>
      </Sheet>

      <Sheet open={textDialog !== null} onOpenChange={(open) => !open && setTextDialog(null)}>
        <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
          {textDialog ? (
            <>
              <SheetHeader>
                <SheetTitle>{textDialogCopy[textDialog].title}</SheetTitle>
                <SheetDescription>{textDialogCopy[textDialog].description}</SheetDescription>
              </SheetHeader>
              <div className="flex flex-1 flex-col gap-4">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="work-order-text-dialog">Justificativa</Label>
                  <Textarea id="work-order-text-dialog" required value={text} onChange={(event) => setText(event.target.value)} />
                </div>
                <div className="mt-auto flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setTextDialog(null)}>
                    Voltar
                  </Button>
                  <Button
                    variant={textDialog === "cancelar" ? "destructive" : "default"}
                    disabled={!text.trim() || reprovarCusto.isPending || cancelar.isPending}
                    onClick={handleTextDialogConfirm}
                  >
                    {textDialogCopy[textDialog].confirm}
                  </Button>
                </div>
              </div>
            </>
          ) : null}
        </SheetContent>
      </Sheet>
    </div>
  );
}

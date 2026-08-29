"use client";

import * as React from "react";
import { ClipboardCheck } from "lucide-react";

import {
  Badge,
  Button,
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
import type { Checklist, ChecklistItem, ChecklistReferenceType, ChecklistType } from "@gestorfrete/types";

import {
  useApproveChecklistMutation,
  useChecklistsQuery,
  useCreateChecklistMutation,
  useRejectChecklistMutation,
  useStartChecklistMutation,
  useSubmitChecklistMutation,
} from "@/modules/maintenance/hooks/use-checklists";
import { ApiError } from "@/shared/lib/api-client";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

import { ChecklistItemForm } from "./checklist-item-form";
import { ChecklistStatusBadge } from "./checklist-status-badge";

const TYPE_LABEL: Record<ChecklistType, string> = {
  MOTORISTA_SAIDA: "Motorista — Saída",
  MOTORISTA_RETORNO: "Motorista — Retorno",
  OFICINA: "Oficina",
  ADMINISTRATIVO: "Administrativo",
  CARREGAMENTO: "Carregamento",
  DESCARGA: "Descarga",
};

interface ChecklistPanelProps {
  referenceType: ChecklistReferenceType;
  referenceId: string;
  canFill: boolean;
  canApprove: boolean;
  canReject: boolean;
}

/**
 * Checklist "Motorista — Saída" de uma Viagem é o que desbloqueia `PLANEJADA→AGUARDANDO_CHECKLIST→
 * LIBERADA` de verdade (Lote Frota e Manutenção, Parte 1 — fecha o gap identificado nas Lotes
 * Operação/Documentos Fiscais). Criar já dispara o primeiro passo; aprovar dispara o segundo — sem
 * nenhum SQL seed. Checklist "Oficina" de uma Ordem de Serviço reprovado abre automaticamente uma
 * OS corretiva (Parte 2, mesmo bounded context) — sem chamada a `freight`. Um Checklist Reprovado
 * nunca é reaberto — a lista mostra o histórico completo, mais recente primeiro, e o novo Pendente
 * criado pela reprovação aparece como um registro à parte.
 */
export function ChecklistPanel({ referenceType, referenceId, canFill, canApprove, canReject }: ChecklistPanelProps) {
  const checklistsQuery = useChecklistsQuery({ reference_type: referenceType, reference_id: referenceId, limit: 50 });
  const createChecklist = useCreateChecklistMutation();
  const startChecklist = useStartChecklistMutation();
  const submitChecklist = useSubmitChecklistMutation();
  const approveChecklist = useApproveChecklistMutation();
  const rejectChecklist = useRejectChecklistMutation();

  const [createOpen, setCreateOpen] = React.useState(false);
  const [type, setType] = React.useState<ChecklistType>(referenceType === "VIAGEM" ? "MOTORISTA_SAIDA" : "OFICINA");
  const [items, setItems] = React.useState<Record<string, ChecklistItem[]>>({});
  const [rejectTarget, setRejectTarget] = React.useState<Checklist | null>(null);
  const [rejectObservacao, setRejectObservacao] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createChecklist.mutateAsync({ type, reference_type: referenceType, reference_id: referenceId });
      toast.success("Checklist criado.");
      setCreateOpen(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar o checklist.");
    }
  }

  async function handleStart(checklistId: string) {
    try {
      await startChecklist.mutateAsync(checklistId);
      toast.success("Preenchimento iniciado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível iniciar o preenchimento.");
    }
  }

  async function handleSubmit(checklistId: string) {
    const checklistItems = items[checklistId] ?? [];
    try {
      await submitChecklist.mutateAsync({ checklistId, body: { itens: checklistItems } });
      toast.success("Checklist concluído.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível concluir o checklist.");
    }
  }

  async function handleApprove(checklistId: string) {
    try {
      await approveChecklist.mutateAsync(checklistId);
      toast.success("Checklist aprovado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível aprovar o checklist.");
    }
  }

  async function handleReject() {
    if (!rejectTarget) return;
    try {
      await rejectChecklist.mutateAsync({ checklistId: rejectTarget.id, body: { observacao: rejectObservacao } });
      toast.success("Checklist reprovado — um novo checklist Pendente foi criado.");
      setRejectTarget(null);
      setRejectObservacao("");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível reprovar o checklist.");
    }
  }

  if (checklistsQuery.isLoading) return <LoadingState rows={3} />;
  if (checklistsQuery.error)
    return <ErrorState description="Não foi possível carregar os checklists." onRetry={() => checklistsQuery.refetch()} />;

  const checklists = checklistsQuery.data?.data ?? [];

  return (
    <div className="flex flex-col gap-4">
      {canFill ? (
        <div className="flex justify-end">
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            Novo checklist
          </Button>
        </div>
      ) : null}

      {checklists.length === 0 ? (
        <EmptyState icon={ClipboardCheck} title="Nenhum checklist criado ainda" />
      ) : (
        <div className="flex flex-col gap-3">
          {checklists.map((checklist) => (
            <div key={checklist.id} className="rounded-md border border-border p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline">{TYPE_LABEL[checklist.type]}</Badge>
                <ChecklistStatusBadge status={checklist.status} />
                <span className="text-xs text-muted-foreground">{checklist.codigo}</span>
              </div>

              {checklist.status === "PENDENTE" && canFill ? (
                <div className="mt-3">
                  <Button size="sm" variant="outline" onClick={() => handleStart(checklist.id)} disabled={startChecklist.isPending}>
                    Iniciar preenchimento
                  </Button>
                </div>
              ) : null}

              {checklist.status === "EM_PREENCHIMENTO" && canFill ? (
                <div className="mt-3 flex flex-col gap-3">
                  <ChecklistItemForm
                    items={items[checklist.id] ?? []}
                    onChange={(next) => setItems((current) => ({ ...current, [checklist.id]: next }))}
                  />
                  <Button
                    size="sm"
                    className="self-start"
                    disabled={
                      submitChecklist.isPending ||
                      (items[checklist.id] ?? []).length === 0 ||
                      (items[checklist.id] ?? []).some((item) => !item.descricao.trim() || item.resposta === undefined)
                    }
                    onClick={() => handleSubmit(checklist.id)}
                  >
                    Concluir checklist
                  </Button>
                </div>
              ) : null}

              {checklist.status === "CONCLUIDO" ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {canApprove ? (
                    <Button size="sm" onClick={() => handleApprove(checklist.id)} disabled={approveChecklist.isPending}>
                      Aprovar
                    </Button>
                  ) : null}
                  {canReject ? (
                    <Button size="sm" variant="destructive" onClick={() => setRejectTarget(checklist)}>
                      Reprovar
                    </Button>
                  ) : null}
                </div>
              ) : null}

              {checklist.items.length > 0 ? (
                <ul className="mt-3 flex flex-col gap-1 text-sm">
                  {checklist.items.map((item, index) => (
                    <li key={index} className="flex items-center justify-between gap-2">
                      <span>
                        {item.descricao}
                        {item.critico ? <span className="ml-1 text-xs text-destructive">(crítico)</span> : null}
                      </span>
                      <Badge variant={item.resposta ? "success" : "destructive"}>
                        {item.resposta ? "Conforme" : "Não conforme"}
                      </Badge>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ))}
        </div>
      )}

      <Sheet open={createOpen} onOpenChange={setCreateOpen}>
        <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Novo checklist</SheetTitle>
            <SheetDescription>
              {referenceType === "VIAGEM"
                ? "“Motorista — Saída” é o que libera o despacho da viagem quando aprovado."
                : "“Oficina” reprovado abre automaticamente uma nova Ordem de Serviço corretiva."}
            </SheetDescription>
          </SheetHeader>
          <form onSubmit={handleCreate} className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="checklist-type">Tipo</Label>
              <Select value={type} onValueChange={(value) => setType(value as ChecklistType)}>
                <SelectTrigger id="checklist-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(Object.keys(TYPE_LABEL) as ChecklistType[]).map((value) => (
                    <SelectItem key={value} value={value}>
                      {TYPE_LABEL[value]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

            <div className="mt-auto flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createChecklist.isPending}>
                {createChecklist.isPending ? "Criando…" : "Criar checklist"}
              </Button>
            </div>
          </form>
        </SheetContent>
      </Sheet>

      <Sheet open={rejectTarget !== null} onOpenChange={(open) => !open && setRejectTarget(null)}>
        <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Reprovar checklist</SheetTitle>
            <SheetDescription>
              Cria automaticamente um novo checklist Pendente — este nunca é reaberto. Observação obrigatória.
            </SheetDescription>
          </SheetHeader>
          <div className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="checklist-reject-observacao">Observação</Label>
              <Textarea
                id="checklist-reject-observacao"
                required
                value={rejectObservacao}
                onChange={(event) => setRejectObservacao(event.target.value)}
              />
            </div>
            <div className="mt-auto flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setRejectTarget(null)}>
                Voltar
              </Button>
              <Button variant="destructive" disabled={!rejectObservacao.trim() || rejectChecklist.isPending} onClick={handleReject}>
                Reprovar checklist
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}

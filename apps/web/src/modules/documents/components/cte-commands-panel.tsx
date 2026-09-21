"use client";

import * as React from "react";

import { Button, Label, Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, Textarea, toast } from "@gestorfrete/ui";
import type { Cte } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import {
  useCancelCteMutation,
  useInutilizeCteMutation,
  useReceiveSefazResponseMutation,
  useSignCteMutation,
  useTransmitCteMutation,
  useValidateCteMutation,
} from "@/modules/documents/hooks/use-ctes";
import { ApiError } from "@/shared/lib/api-client";

/**
 * Só renderiza o(s) comando(s) válido(s) para o `status` atual — nunca um botão para uma
 * transição inválida (`docs/flows/009-FISCAL.md`). Status nunca muda por PATCH: cada botão é um
 * `POST .../commands/<verbo>` (D274). Sem botão de excluir em nenhuma hipótese (D109).
 *
 * `TRANSMITIDO→AUTORIZADO/DENEGADO` — Reconciliado (Lote Fiscal, Parte 2.2, D397 fechado): ganhou
 * rota HTTP real (`commands/receive-sefaz-response`). Nenhuma integração de verdade com a SEFAZ
 * existe — o resultado vem de um `SandboxSefazGateway` no backend, sempre autoriza. O rótulo do
 * botão deixa isso explícito, nunca fingindo ser uma resposta real da SEFAZ.
 */
export function CteCommandsPanel({ cte }: { cte: Cte }) {
  const { hasPermission } = usePermissions();
  const [cancelOpen, setCancelOpen] = React.useState(false);
  const [notes, setNotes] = React.useState("");

  const validate = useValidateCteMutation();
  const sign = useSignCteMutation();
  const transmit = useTransmitCteMutation();
  const receiveSefazResponse = useReceiveSefazResponseMutation();
  const inutilize = useInutilizeCteMutation();
  const cancel = useCancelCteMutation();

  async function runSimple(mutation: ReturnType<typeof useValidateCteMutation>, successMessage: string) {
    try {
      await mutation.mutateAsync(cte.id);
      toast.success(successMessage);
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível executar a ação.");
    }
  }

  async function handleCancel() {
    try {
      await cancel.mutateAsync({ cteId: cte.id, body: { notes } });
      toast.success("CT-e cancelado.");
      setCancelOpen(false);
      setNotes("");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível cancelar o CT-e.");
    }
  }

  const canIssue = hasPermission("documents.cte.issue");
  const canReceiveSefazResponse = hasPermission("documents.cte.receive_sefaz_response");
  const canCancel = hasPermission("documents.cte.cancel");

  const buttons: React.ReactNode[] = [];

  if ((cte.status === "RASCUNHO" || cte.status === "VALIDADO") && canIssue) {
    if (cte.status === "RASCUNHO") {
      buttons.push(
        <Button key="validate" onClick={() => runSimple(validate, "CT-e validado.")}>
          Validar
        </Button>
      );
    }
    if (cte.status === "VALIDADO") {
      buttons.push(
        <Button key="sign" onClick={() => runSimple(sign, "CT-e assinado.")}>
          Assinar
        </Button>
      );
    }
    buttons.push(
      <Button key="inutilize" variant="outline" onClick={() => runSimple(inutilize, "CT-e inutilizado.")}>
        Inutilizar
      </Button>
    );
  }
  if (cte.status === "ASSINADO" && canIssue) {
    buttons.push(
      <Button key="transmit" onClick={() => runSimple(transmit, "CT-e transmitido à SEFAZ.")}>
        Transmitir
      </Button>
    );
  }
  if (cte.status === "TRANSMITIDO" && canReceiveSefazResponse) {
    buttons.push(
      <Button
        key="receive-sefaz-response" variant="outline"
        onClick={() => runSimple(receiveSefazResponse, "Resposta da SEFAZ recebida (simulada).")}
      >
        Simular resposta SEFAZ
      </Button>
    );
  }
  if (cte.status === "AUTORIZADO" && canCancel) {
    buttons.push(
      <Button key="cancel" variant="destructive" onClick={() => setCancelOpen(true)}>
        Cancelar
      </Button>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {buttons.length > 0 ? <div className="flex flex-wrap gap-2">{buttons}</div> : null}

      <Sheet open={cancelOpen} onOpenChange={setCancelOpen}>
        <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Cancelar CT-e</SheetTitle>
            <SheetDescription>Dentro do prazo legal de cancelamento. Motivo obrigatório.</SheetDescription>
          </SheetHeader>
          <div className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="cte-cancel-notes">Observação</Label>
              <Textarea id="cte-cancel-notes" required value={notes} onChange={(event) => setNotes(event.target.value)} />
            </div>
            <div className="mt-auto flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setCancelOpen(false)}>
                Voltar
              </Button>
              <Button variant="destructive" disabled={!notes.trim() || cancel.isPending} onClick={handleCancel}>
                Cancelar CT-e
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}

"use client";

import * as React from "react";

import { Button, Label, Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, Textarea, toast } from "@gestorfrete/ui";
import type { Mdfe } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useCancelMdfeMutation, useCloseMdfeMutation } from "@/modules/documents/hooks/use-mdfes";
import { ApiError } from "@/shared/lib/api-client";

/**
 * `PENDENTE→AUTORIZADO` só existe via o simulador de resposta SEFAZ, sem rota HTTP (D397) —
 * "Encerrar" só fica clicável a partir de `AUTORIZADO`, que hoje só é alcançável com dado
 * semeado diretamente (mesmo gap do CT-e). Cancelar é bloqueado uma vez `ENCERRADO` — nunca
 * reversível (`docs/flows/009-FISCAL.md`).
 */
export function MdfeCommandsPanel({ mdfe }: { mdfe: Mdfe }) {
  const { hasPermission } = usePermissions();
  const [cancelOpen, setCancelOpen] = React.useState(false);
  const [notes, setNotes] = React.useState("");

  const close = useCloseMdfeMutation();
  const cancel = useCancelMdfeMutation();

  async function handleClose() {
    try {
      await close.mutateAsync(mdfe.id);
      toast.success("MDF-e encerrado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível encerrar o MDF-e.");
    }
  }

  async function handleCancel() {
    try {
      await cancel.mutateAsync({ mdfeId: mdfe.id, body: { notes } });
      toast.success("MDF-e cancelado.");
      setCancelOpen(false);
      setNotes("");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível cancelar o MDF-e.");
    }
  }

  const buttons: React.ReactNode[] = [];

  if (mdfe.status === "AUTORIZADO" && hasPermission("documents.mdfe.close")) {
    buttons.push(
      <Button key="close" onClick={handleClose} disabled={close.isPending}>
        Encerrar
      </Button>
    );
  }
  if ((mdfe.status === "PENDENTE" || mdfe.status === "AUTORIZADO") && hasPermission("documents.mdfe.cancel")) {
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
            <SheetTitle>Cancelar MDF-e</SheetTitle>
            <SheetDescription>Motivo obrigatório. Bloqueado depois de Encerrado.</SheetDescription>
          </SheetHeader>
          <div className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="mdfe-cancel-notes">Observação</Label>
              <Textarea id="mdfe-cancel-notes" required value={notes} onChange={(event) => setNotes(event.target.value)} />
            </div>
            <div className="mt-auto flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setCancelOpen(false)}>
                Voltar
              </Button>
              <Button variant="destructive" disabled={!notes.trim() || cancel.isPending} onClick={handleCancel}>
                Cancelar MDF-e
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}

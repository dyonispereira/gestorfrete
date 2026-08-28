"use client";

import * as React from "react";
import { FileEdit, Plus } from "lucide-react";

import { Button, Label, Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, Textarea, toast } from "@gestorfrete/ui";
import type { CteStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useCorrectionLettersQuery, useCreateCorrectionLetterMutation } from "@/modules/documents/hooks/use-correction-letters";
import { ApiError } from "@/shared/lib/api-client";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

interface CorrectionLettersTabProps {
  cteId: string;
  cteStatus: CteStatus;
}

/**
 * Append-only — Carta de Correção nunca é editada/excluída, cada uma é a própria história (D282).
 * Só aceita quando o CT-e pai está AUTORIZADO — o botão "Nova carta" reflete esse gate mesmo antes
 * do Backend recusar, para não abrir um formulário fadado a falhar.
 */
export function CorrectionLettersTab({ cteId, cteStatus }: CorrectionLettersTabProps) {
  const { hasPermission } = usePermissions();
  const lettersQuery = useCorrectionLettersQuery(cteId);
  const createLetter = useCreateCorrectionLetterMutation(cteId);

  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [correctionText, setCorrectionText] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const canCreate = hasPermission("documents.cte.correct") && cteStatus === "AUTORIZADO";

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createLetter.mutateAsync({ correction_text: correctionText });
      toast.success("Carta de correção emitida.");
      setCorrectionText("");
      setDrawerOpen(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível emitir a carta de correção.");
    }
  }

  if (lettersQuery.isLoading) return <LoadingState rows={2} />;
  if (lettersQuery.error)
    return <ErrorState description="Não foi possível carregar as cartas de correção." onRetry={() => lettersQuery.refetch()} />;

  const letters = lettersQuery.data?.data ?? [];

  return (
    <div className="flex flex-col gap-4">
      {canCreate ? (
        <div className="flex justify-end">
          <Button size="sm" onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Nova carta de correção
          </Button>
        </div>
      ) : null}

      {letters.length === 0 ? (
        <EmptyState icon={FileEdit} title="Nenhuma carta de correção emitida" />
      ) : (
        <div className="flex flex-col gap-2">
          {letters.map((letter) => (
            <div key={letter.id} className="rounded-md border border-border p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Carta #{letter.sequence_number}</span>
                <span className="text-xs text-muted-foreground">{new Date(letter.sent_at).toLocaleString("pt-BR")}</span>
              </div>
              <p className="mt-1 text-sm">{letter.correction_text}</p>
            </div>
          ))}
        </div>
      )}

      <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
        <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Nova carta de correção</SheetTitle>
            <SheetDescription>Só corrige erros formais — nunca valores fiscais ou partes do CT-e.</SheetDescription>
          </SheetHeader>
          <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="correction-text">Texto da correção</Label>
              <Textarea id="correction-text" required value={correctionText} onChange={(event) => setCorrectionText(event.target.value)} />
            </div>

            {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

            <div className="mt-auto flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setDrawerOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createLetter.isPending}>
                {createLetter.isPending ? "Emitindo…" : "Emitir carta"}
              </Button>
            </div>
          </form>
        </SheetContent>
      </Sheet>
    </div>
  );
}

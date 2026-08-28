"use client";

import * as React from "react";
import { Plus, Receipt } from "lucide-react";

import { Button, Input, Label, Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, toast } from "@gestorfrete/ui";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useCreateReferencedNfeMutation, useReferencedNfesQuery } from "@/modules/documents/hooks/use-referenced-nfes";
import { ApiError } from "@/shared/lib/api-client";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

/**
 * O GestorFrete não emite NF-e — só referencia uma já emitida por terceiros (chave de 44
 * dígitos). Append-only, sem gate de status do CT-e pai, sem edição/exclusão.
 */
export function ReferencedNfesTab({ cteId }: { cteId: string }) {
  const { hasPermission } = usePermissions();
  const nfesQuery = useReferencedNfesQuery(cteId);
  const createNfe = useCreateReferencedNfeMutation(cteId);

  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [accessKey, setAccessKey] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const canCreate = hasPermission("documents.cte.issue");

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createNfe.mutateAsync({ access_key: accessKey });
      toast.success("NF-e referenciada adicionada.");
      setAccessKey("");
      setDrawerOpen(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível adicionar a NF-e referenciada.");
    }
  }

  if (nfesQuery.isLoading) return <LoadingState rows={2} />;
  if (nfesQuery.error)
    return <ErrorState description="Não foi possível carregar as NF-e referenciadas." onRetry={() => nfesQuery.refetch()} />;

  const nfes = nfesQuery.data?.data ?? [];

  return (
    <div className="flex flex-col gap-4">
      {canCreate ? (
        <div className="flex justify-end">
          <Button size="sm" onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Referenciar NF-e
          </Button>
        </div>
      ) : null}

      {nfes.length === 0 ? (
        <EmptyState icon={Receipt} title="Nenhuma NF-e referenciada" />
      ) : (
        <div className="flex flex-col gap-2">
          {nfes.map((nfe) => (
            <div key={nfe.id} className="rounded-md border border-border p-3 font-mono text-sm">
              {nfe.access_key}
            </div>
          ))}
        </div>
      )}

      <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
        <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Referenciar NF-e</SheetTitle>
            <SheetDescription>Chave de acesso de 44 dígitos, emitida por terceiros.</SheetDescription>
          </SheetHeader>
          <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="nfe-access-key">Chave de acesso</Label>
              <Input
                id="nfe-access-key"
                required
                pattern="[0-9]{44}"
                maxLength={44}
                value={accessKey}
                onChange={(event) => setAccessKey(event.target.value)}
              />
            </div>

            {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

            <div className="mt-auto flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setDrawerOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createNfe.isPending}>
                {createNfe.isPending ? "Adicionando…" : "Adicionar"}
              </Button>
            </div>
          </form>
        </SheetContent>
      </Sheet>
    </div>
  );
}

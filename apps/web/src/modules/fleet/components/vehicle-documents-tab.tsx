"use client";

import * as React from "react";
import { FileText, Plus } from "lucide-react";

import { Badge, Button, Input, Label, Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, toast } from "@gestorfrete/ui";
import type { CreateVehicleDocumentRequest, VehicleDocument } from "@gestorfrete/types";

import {
  useCreateVehicleDocumentMutation,
  useUpdateVehicleDocumentMutation,
  useVehicleDocumentsQuery,
} from "@/modules/fleet/hooks/use-vehicle-documents";
import { ApiError } from "@/shared/lib/api-client";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

/** Suggestions only — the Backend accepts any string for `type`, there's no server-side vocabulary (Lote Frota audit). */
const TYPE_SUGGESTIONS = ["CRLV", "Apólice de Seguro", "Licenciamento", "Certificado de Tacógrafo"];

const EMPTY_FORM = { type: "", number: "", expires_at: "" };

interface VehicleDocumentsTabProps {
  vehicleId: string;
  editable: boolean;
}

/** No delete — no DELETE endpoint exists for vehicle documents. */
export function VehicleDocumentsTab({ vehicleId, editable }: VehicleDocumentsTabProps) {
  const documentsQuery = useVehicleDocumentsQuery(vehicleId);
  const createDocument = useCreateVehicleDocumentMutation(vehicleId);
  const updateDocument = useUpdateVehicleDocumentMutation(vehicleId);

  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<VehicleDocument | null>(null);
  const [form, setForm] = React.useState(EMPTY_FORM);
  const [formError, setFormError] = React.useState<string | null>(null);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setDrawerOpen(true);
  }

  function openEdit(document: VehicleDocument) {
    setEditing(document);
    setForm({ type: document.type, number: document.number, expires_at: document.expires_at });
    setFormError(null);
    setDrawerOpen(true);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      if (editing) {
        await updateDocument.mutateAsync({ documentId: editing.id, body: { number: form.number, expires_at: form.expires_at } });
        toast.success("Documento atualizado.");
      } else {
        const body: CreateVehicleDocumentRequest = { type: form.type, number: form.number, expires_at: form.expires_at };
        await createDocument.mutateAsync(body);
        toast.success("Documento adicionado.");
      }
      setDrawerOpen(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível salvar o documento.");
    }
  }

  if (documentsQuery.isLoading) return <LoadingState rows={3} />;
  if (documentsQuery.error)
    return <ErrorState description="Não foi possível carregar os documentos." onRetry={() => documentsQuery.refetch()} />;

  const documents = documentsQuery.data?.data ?? [];

  return (
    <div className="flex flex-col gap-4">
      {editable ? (
        <div className="flex justify-end">
          <Button size="sm" onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Novo documento
          </Button>
        </div>
      ) : null}

      {documents.length === 0 ? (
        <EmptyState icon={FileText} title="Nenhum documento cadastrado" />
      ) : (
        <div className="flex flex-col gap-3">
          {documents.map((document) => (
            <div key={document.id} className="flex items-start justify-between gap-4 rounded-md border border-border p-4">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{document.type}</Badge>
                  <Badge variant={document.status === "VALIDO" ? "success" : "destructive"}>
                    {document.status === "VALIDO" ? "Válido" : "Vencido"}
                  </Badge>
                </div>
                <p className="text-sm text-foreground">{document.number}</p>
                <p className="text-sm text-muted-foreground">Vence em {document.expires_at}</p>
              </div>
              {editable ? (
                <Button size="sm" variant="outline" onClick={() => openEdit(document)}>
                  Editar
                </Button>
              ) : null}
            </div>
          ))}
        </div>
      )}

      <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
        <SheetContent className="flex flex-col gap-6 sm:max-w-md">
          <SheetHeader>
            <SheetTitle>{editing ? "Editar documento" : "Novo documento"}</SheetTitle>
            <SheetDescription>Sem upload de arquivo — a API não tem esse campo.</SheetDescription>
          </SheetHeader>
          <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="vdoc-type">Tipo</Label>
              <Input
                id="vdoc-type"
                required
                list="vehicle-document-types"
                disabled={Boolean(editing)}
                value={form.type}
                onChange={(event) => setForm((f) => ({ ...f, type: event.target.value }))}
              />
              <datalist id="vehicle-document-types">
                {TYPE_SUGGESTIONS.map((suggestion) => (
                  <option key={suggestion} value={suggestion} />
                ))}
              </datalist>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="vdoc-number">Número</Label>
              <Input id="vdoc-number" required value={form.number} onChange={(event) => setForm((f) => ({ ...f, number: event.target.value }))} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="vdoc-expires">Validade</Label>
              <Input
                id="vdoc-expires"
                type="date"
                required
                value={form.expires_at}
                onChange={(event) => setForm((f) => ({ ...f, expires_at: event.target.value }))}
              />
            </div>

            {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

            <div className="mt-auto flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setDrawerOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createDocument.isPending || updateDocument.isPending}>
                {createDocument.isPending || updateDocument.isPending ? "Salvando…" : "Salvar"}
              </Button>
            </div>
          </form>
        </SheetContent>
      </Sheet>
    </div>
  );
}

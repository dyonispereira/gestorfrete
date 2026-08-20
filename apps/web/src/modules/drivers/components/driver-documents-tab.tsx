"use client";

import * as React from "react";
import { FileText, Plus } from "lucide-react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
  Badge,
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
import type { CnhCategory, CreateDriverDocumentRequest, DriverDocument, DriverDocumentType } from "@gestorfrete/types";

import {
  useCreateDriverDocumentMutation,
  useDeleteDriverDocumentMutation,
  useDriverDocumentsQuery,
  useUpdateDriverDocumentMutation,
} from "@/modules/drivers/hooks/use-driver-documents";
import { ApiError } from "@/shared/lib/api-client";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const DOCUMENT_TYPE_LABEL: Record<DriverDocumentType, string> = {
  CNH: "CNH",
  RG: "RG",
  EXAME_TOXICOLOGICO: "Exame toxicológico",
  REGISTRO_ANTT: "Registro ANTT",
};

const CNH_CATEGORIES: CnhCategory[] = ["A", "B", "C", "D", "E"];

const EMPTY_FORM: CreateDriverDocumentRequest = { type: "CNH", number: "", cnh_category: undefined, expires_at: undefined };

interface DriverDocumentsTabProps {
  driverId: string;
  editable: boolean;
}

/**
 * `drivers.driver.view_cnh`/`.edit_cnh` exist as permission codes but no endpoint enforces them
 * (Lote Cadastros audit) — gating here is the same blanket `drivers.driver.view`/`.edit` used for
 * every document type, matching what the Backend actually checks.
 */
export function DriverDocumentsTab({ driverId, editable }: DriverDocumentsTabProps) {
  const documentsQuery = useDriverDocumentsQuery(driverId);
  const createDocument = useCreateDriverDocumentMutation(driverId);
  const updateDocument = useUpdateDriverDocumentMutation(driverId);
  const deleteDocument = useDeleteDriverDocumentMutation(driverId);

  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<DriverDocument | null>(null);
  const [form, setForm] = React.useState<CreateDriverDocumentRequest>(EMPTY_FORM);
  const [formError, setFormError] = React.useState<string | null>(null);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setDrawerOpen(true);
  }

  function openEdit(document: DriverDocument) {
    setEditing(document);
    setForm({
      type: document.type,
      number: document.number,
      cnh_category: document.cnh_category,
      expires_at: document.expires_at,
    });
    setFormError(null);
    setDrawerOpen(true);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      if (editing) {
        await updateDocument.mutateAsync({
          documentId: editing.id,
          body: { number: form.number, cnh_category: form.cnh_category, expires_at: form.expires_at },
        });
        toast.success("Documento atualizado.");
      } else {
        await createDocument.mutateAsync(form);
        toast.success("Documento adicionado.");
      }
      setDrawerOpen(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível salvar o documento.");
    }
  }

  async function handleDelete(documentId: string) {
    try {
      await deleteDocument.mutateAsync(documentId);
      toast.success("Documento removido.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível remover o documento.");
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
                  <Badge variant="outline">{DOCUMENT_TYPE_LABEL[document.type]}</Badge>
                  {document.cnh_category ? <Badge variant="outline">Categoria {document.cnh_category}</Badge> : null}
                  <Badge variant={document.status === "VALIDO" ? "success" : "destructive"}>
                    {document.status === "VALIDO" ? "Válido" : "Vencido"}
                  </Badge>
                </div>
                <p className="text-sm text-foreground">{document.number}</p>
                {document.expires_at ? (
                  <p className="text-sm text-muted-foreground">Vence em {document.expires_at}</p>
                ) : null}
              </div>
              {editable ? (
                <div className="flex shrink-0 gap-2">
                  <Button size="sm" variant="outline" onClick={() => openEdit(document)}>
                    Editar
                  </Button>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button size="sm" variant="destructive">
                        Remover
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Remover este documento?</AlertDialogTitle>
                        <AlertDialogDescription>Essa ação não pode ser desfeita pela tela.</AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancelar</AlertDialogCancel>
                        <AlertDialogAction onClick={() => handleDelete(document.id)}>Remover</AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      )}

      <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
        <SheetContent className="flex flex-col gap-6 sm:max-w-md">
          <SheetHeader>
            <SheetTitle>{editing ? "Editar documento" : "Novo documento"}</SheetTitle>
            <SheetDescription>Sem upload de arquivo — a API não tem esse campo ainda.</SheetDescription>
          </SheetHeader>
          <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label>Tipo</Label>
              <Select
                value={form.type}
                onValueChange={(value) => setForm((f) => ({ ...f, type: value as DriverDocumentType }))}
                disabled={Boolean(editing)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(Object.keys(DOCUMENT_TYPE_LABEL) as DriverDocumentType[]).map((value) => (
                    <SelectItem key={value} value={value}>
                      {DOCUMENT_TYPE_LABEL[value]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="document-number">Número</Label>
              <Input id="document-number" required value={form.number} onChange={(event) => setForm((f) => ({ ...f, number: event.target.value }))} />
            </div>
            {form.type === "CNH" ? (
              <div className="flex flex-col gap-1.5">
                <Label>Categoria CNH</Label>
                <Select value={form.cnh_category ?? ""} onValueChange={(value) => setForm((f) => ({ ...f, cnh_category: value as CnhCategory }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione…" />
                  </SelectTrigger>
                  <SelectContent>
                    {CNH_CATEGORIES.map((value) => (
                      <SelectItem key={value} value={value}>
                        {value}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            ) : null}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="document-expires">Validade</Label>
              <Input
                id="document-expires"
                type="date"
                value={form.expires_at ?? ""}
                onChange={(event) => setForm((f) => ({ ...f, expires_at: event.target.value || undefined }))}
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

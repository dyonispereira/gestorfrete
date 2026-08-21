"use client";

import * as React from "react";
import { Paperclip } from "lucide-react";

import { Button, Input, Label, toast } from "@gestorfrete/ui";

import { usePermissions } from "@/core/rbac/permissions-provider";
import {
  useCreateTripAttachmentMutation,
  useDeleteTripAttachmentMutation,
  useTripAttachmentsQuery,
} from "@/modules/freight/hooks/use-trip-attachments";
import { ApiError } from "@/shared/lib/api-client";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

/**
 * Criar/excluir exigem `freight.trip.edit` (rota) **e** `storage.attachment.create`/`.delete`
 * (handler) — as duas ao mesmo tempo. Sem PATCH — só create/delete (imutável, D415-adjacent). Sem
 * upload de arquivo aqui: não existe UI de upload no `storage` ainda, mesmo padrão já usado nos
 * Documentos de Veículo da Lote Frota — `file_id` é um UUID já existente, colado à mão.
 */
export function TripAttachmentsPanel({ tripId }: { tripId: string }) {
  const { hasPermission } = usePermissions();
  const attachmentsQuery = useTripAttachmentsQuery(tripId);
  const createAttachment = useCreateTripAttachmentMutation(tripId);
  const deleteAttachment = useDeleteTripAttachmentMutation(tripId);

  const [attachmentType, setAttachmentType] = React.useState("");
  const [fileId, setFileId] = React.useState("");

  const canCreate = hasPermission("freight.trip.edit") && hasPermission("storage.attachment.create");
  const canDelete = hasPermission("freight.trip.edit") && hasPermission("storage.attachment.delete");

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    try {
      await createAttachment.mutateAsync({ attachment_type: attachmentType, file_id: fileId });
      toast.success("Anexo adicionado.");
      setAttachmentType("");
      setFileId("");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível anexar o arquivo.");
    }
  }

  async function handleDelete(attachmentId: string) {
    try {
      await deleteAttachment.mutateAsync(attachmentId);
      toast.success("Anexo removido.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível remover o anexo.");
    }
  }

  if (attachmentsQuery.isLoading) return <LoadingState rows={3} />;
  if (attachmentsQuery.error)
    return <ErrorState description="Não foi possível carregar os anexos." onRetry={() => attachmentsQuery.refetch()} />;

  const attachments = attachmentsQuery.data?.data ?? [];

  return (
    <div className="flex flex-col gap-4">
      {canCreate ? (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-md border border-border p-4 sm:flex-row sm:items-end">
          <div className="flex flex-1 flex-col gap-1.5">
            <Label htmlFor="attachment-type">Tipo</Label>
            <Input id="attachment-type" required value={attachmentType} onChange={(event) => setAttachmentType(event.target.value)} />
          </div>
          <div className="flex flex-1 flex-col gap-1.5">
            <Label htmlFor="attachment-file-id">ID do arquivo (UUID)</Label>
            <Input id="attachment-file-id" required value={fileId} onChange={(event) => setFileId(event.target.value)} />
          </div>
          <Button type="submit" disabled={createAttachment.isPending}>
            {createAttachment.isPending ? "Anexando…" : "Anexar"}
          </Button>
        </form>
      ) : null}

      {attachments.length === 0 ? (
        <EmptyState icon={Paperclip} title="Nenhum anexo ainda" />
      ) : (
        <div className="flex flex-col gap-2">
          {attachments.map((attachment) => (
            <div key={attachment.id} className="flex items-center justify-between rounded-md border border-border p-3">
              <div>
                <p className="text-sm font-medium">{attachment.attachment_type}</p>
                <p className="text-xs text-muted-foreground">{attachment.description ?? attachment.file_id}</p>
              </div>
              {canDelete ? (
                <Button size="sm" variant="outline" onClick={() => handleDelete(attachment.id)} disabled={deleteAttachment.isPending}>
                  Remover
                </Button>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

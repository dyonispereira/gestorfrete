"use client";

import * as React from "react";
import { MessageSquare } from "lucide-react";

import { Badge, Button, Checkbox, Label, Textarea, toast } from "@gestorfrete/ui";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useSession } from "@/core/tenant/session-provider";
import {
  useCreateTripCommentMutation,
  useDeleteTripCommentMutation,
  useTripCommentsQuery,
} from "@/modules/freight/hooks/use-trip-comments";
import { ApiError } from "@/shared/lib/api-client";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

/**
 * Criar exige `freight.trip.view` (rota) **e** `storage.comment.create` (handler) — as duas ao
 * mesmo tempo, nunca só uma (mesma disciplina em Anexos). Editar/excluir são sempre "_own": só o
 * autor pode, então o botão só aparece quando `author_id` bate com o usuário logado, mesmo que a
 * permissão exista no papel.
 */
export function TripCommentsPanel({ tripId }: { tripId: string }) {
  const { hasPermission } = usePermissions();
  const { user } = useSession();
  const commentsQuery = useTripCommentsQuery(tripId);
  const createComment = useCreateTripCommentMutation(tripId);
  const deleteComment = useDeleteTripCommentMutation(tripId);

  const [text, setText] = React.useState("");
  const [visibleToClient, setVisibleToClient] = React.useState(false);

  const canCreate = hasPermission("freight.trip.view") && hasPermission("storage.comment.create");
  const canDeleteOwn = hasPermission("storage.comment.delete_own");

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    try {
      await createComment.mutateAsync({ text, visible_to_client: visibleToClient });
      setText("");
      setVisibleToClient(false);
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível comentar.");
    }
  }

  async function handleDelete(commentId: string) {
    try {
      await deleteComment.mutateAsync(commentId);
      toast.success("Comentário excluído.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível excluir o comentário.");
    }
  }

  if (commentsQuery.isLoading) return <LoadingState rows={3} />;
  if (commentsQuery.error)
    return <ErrorState description="Não foi possível carregar os comentários." onRetry={() => commentsQuery.refetch()} />;

  const comments = commentsQuery.data?.data ?? [];

  return (
    <div className="flex flex-col gap-4">
      {canCreate ? (
        <form onSubmit={handleSubmit} className="flex flex-col gap-2 rounded-md border border-border p-4">
          <Label htmlFor="trip-comment-text">Novo comentário</Label>
          <Textarea id="trip-comment-text" required value={text} onChange={(event) => setText(event.target.value)} />
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <Checkbox checked={visibleToClient} onCheckedChange={(checked) => setVisibleToClient(checked === true)} />
            Visível para o cliente
          </label>
          <Button type="submit" disabled={createComment.isPending || !text.trim()} className="self-end">
            {createComment.isPending ? "Enviando…" : "Comentar"}
          </Button>
        </form>
      ) : null}

      {comments.length === 0 ? (
        <EmptyState icon={MessageSquare} title="Nenhum comentário ainda" />
      ) : (
        <div className="flex flex-col gap-2">
          {comments.map((comment) => (
            <div key={comment.id} className="rounded-md border border-border p-3">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  {comment.visible_to_client ? <Badge variant="outline">Visível ao cliente</Badge> : null}
                  <span className="text-xs text-muted-foreground">
                    {new Date(comment.audit.created_at).toLocaleString("pt-BR")}
                  </span>
                </div>
                {canDeleteOwn && comment.author_id === user?.id ? (
                  <Button size="sm" variant="outline" onClick={() => handleDelete(comment.id)} disabled={deleteComment.isPending}>
                    Excluir
                  </Button>
                ) : null}
              </div>
              <p className="mt-1 text-sm">{comment.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

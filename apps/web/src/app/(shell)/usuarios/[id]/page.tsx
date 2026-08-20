"use client";

import * as React from "react";
import { useParams } from "next/navigation";

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
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Checkbox,
  Input,
  Label,
  toast,
} from "@gestorfrete/ui";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useRolesQuery } from "@/modules/identity/hooks/use-roles";
import { useDeactivateUserMutation, useUpdateUserMutation, useUserQuery } from "@/modules/identity/hooks/use-users";
import { UserStatusBadge } from "@/modules/identity/components/user-status-badge";
import { ApiError } from "@/shared/lib/api-client";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

export default function UserDetailPage() {
  const params = useParams<{ id: string }>();
  const userId = params.id;
  const { hasPermission } = usePermissions();

  const userQuery = useUserQuery(userId);
  const rolesQuery = useRolesQuery({ limit: 100 });
  const updateUser = useUpdateUserMutation(userId);
  const deactivateUser = useDeactivateUserMutation();

  const user = userQuery.data;
  useBreadcrumbLabel(`/usuarios/${userId}`, user?.nome);

  const [nome, setNome] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [roleIds, setRoleIds] = React.useState<Set<string>>(new Set());

  React.useEffect(() => {
    if (!user) return;
    setNome(user.nome);
    setEmail(user.email);
    setRoleIds(new Set(user.roles));
  }, [user]);

  const canEdit = hasPermission("identity_access.user.edit");
  const canDeactivate = hasPermission("identity_access.user.deactivate");

  function toggleRole(roleId: string) {
    if (!canEdit) return;
    setRoleIds((current) => {
      const next = new Set(current);
      if (next.has(roleId)) next.delete(roleId);
      else next.add(roleId);
      return next;
    });
  }

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    try {
      await updateUser.mutateAsync({ nome, email, role_ids: Array.from(roleIds) });
      toast.success("Usuário atualizado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível salvar.");
    }
  }

  async function handleDeactivate() {
    try {
      await deactivateUser.mutateAsync(userId);
      toast.success("Usuário desativado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível desativar.");
    }
  }

  if (userQuery.isLoading) return <LoadingState rows={6} />;
  if (userQuery.error || !user)
    return (
      <ErrorState
        title="Não foi possível carregar o usuário"
        description={userQuery.error instanceof Error ? userQuery.error.message : undefined}
        onRetry={() => userQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{user.nome}</h1>
          <div className="mt-1 flex items-center gap-2">
            <UserStatusBadge status={user.status} />
            <span className="text-sm text-muted-foreground">{user.email}</span>
          </div>
        </div>
        {canDeactivate && user.status === "ATIVO" ? (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive">Desativar usuário</Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Desativar {user.nome}?</AlertDialogTitle>
                <AlertDialogDescription>
                  O usuário perde acesso imediatamente. Essa ação pode ser revertida depois editando o status.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancelar</AlertDialogCancel>
                <AlertDialogAction onClick={handleDeactivate}>Desativar</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        ) : null}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Dados e papéis</CardTitle>
          <CardDescription>{canEdit ? "Edite os dados e os Papéis associados." : "Somente leitura."}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="flex flex-col gap-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="detail-nome">Nome</Label>
                <Input id="detail-nome" disabled={!canEdit} value={nome} onChange={(event) => setNome(event.target.value)} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="detail-email">E-mail</Label>
                <Input
                  id="detail-email"
                  type="email"
                  disabled={!canEdit}
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <Label>Papéis</Label>
              <div className="flex flex-col gap-2 rounded-md border border-border p-3">
                {rolesQuery.isLoading ? (
                  <p className="text-sm text-muted-foreground">Carregando papéis…</p>
                ) : (
                  rolesQuery.data?.data.map((role) => (
                    <label key={role.id} className="flex items-center gap-2 text-sm">
                      <Checkbox checked={roleIds.has(role.id)} disabled={!canEdit} onCheckedChange={() => toggleRole(role.id)} />
                      {role.nome}
                    </label>
                  ))
                )}
              </div>
            </div>

            {canEdit ? (
              <div className="flex justify-end">
                <Button type="submit" disabled={updateUser.isPending}>
                  {updateUser.isPending ? "Salvando…" : "Salvar alterações"}
                </Button>
              </div>
            ) : null}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

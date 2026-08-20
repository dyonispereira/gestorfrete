"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";

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
  Input,
  Label,
  Textarea,
  toast,
} from "@gestorfrete/ui";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useDeleteRoleMutation, useRoleQuery, useUpdateRoleMutation } from "@/modules/identity/hooks/use-roles";
import { PermissionMatrix } from "@/modules/identity/components/permission-matrix";
import { ApiError } from "@/shared/lib/api-client";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

export default function RoleDetailPage() {
  const params = useParams<{ id: string }>();
  const roleId = params.id;
  const router = useRouter();
  const { hasPermission } = usePermissions();

  const roleQuery = useRoleQuery(roleId);
  const updateRole = useUpdateRoleMutation(roleId);
  const deleteRole = useDeleteRoleMutation();

  const role = roleQuery.data;
  useBreadcrumbLabel(`/papeis/${roleId}`, role?.nome);

  const [nome, setNome] = React.useState("");
  const [descricao, setDescricao] = React.useState("");

  React.useEffect(() => {
    if (!role) return;
    setNome(role.nome);
    setDescricao(role.descricao ?? "");
  }, [role]);

  const canEdit = hasPermission("identity_access.role.edit");
  const canDelete = hasPermission("identity_access.role.delete");

  async function handleSaveInfo(event: React.FormEvent) {
    event.preventDefault();
    try {
      await updateRole.mutateAsync({ nome, descricao: descricao || undefined });
      toast.success("Papel atualizado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível salvar.");
    }
  }

  async function handleDelete() {
    try {
      await deleteRole.mutateAsync(roleId);
      toast.success("Papel excluído.");
      router.replace("/papeis");
    } catch (error) {
      if (error instanceof ApiError && error.code === "IDENTITY_ROLE_IN_USE") {
        toast.error("Este Papel ainda está atribuído a pelo menos um usuário — remova a associação antes de excluir.");
      } else {
        toast.error(error instanceof ApiError ? error.message : "Não foi possível excluir o Papel.");
      }
    }
  }

  if (roleQuery.isLoading) return <LoadingState rows={6} />;
  if (roleQuery.error || !role)
    return (
      <ErrorState
        title="Não foi possível carregar o papel"
        description={roleQuery.error instanceof Error ? roleQuery.error.message : undefined}
        onRetry={() => roleQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{role.nome}</h1>
          <p className="text-sm text-muted-foreground">{role.descricao || "Sem descrição."}</p>
        </div>
        {canDelete ? (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive">Excluir papel</Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Excluir {role.nome}?</AlertDialogTitle>
                <AlertDialogDescription>
                  Só é possível excluir um Papel que não está atribuído a nenhum usuário.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancelar</AlertDialogCancel>
                <AlertDialogAction onClick={handleDelete}>Excluir</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        ) : null}
      </div>

      {canEdit ? (
        <Card>
          <CardHeader>
            <CardTitle>Dados do papel</CardTitle>
            <CardDescription>Nome e descrição exibidos em todo o RBAC.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSaveInfo} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="role-detail-nome">Nome</Label>
                <Input id="role-detail-nome" value={nome} onChange={(event) => setNome(event.target.value)} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="role-detail-descricao">Descrição</Label>
                <Textarea id="role-detail-descricao" value={descricao} onChange={(event) => setDescricao(event.target.value)} />
              </div>
              <div className="flex justify-end">
                <Button type="submit" disabled={updateRole.isPending}>
                  {updateRole.isPending ? "Salvando…" : "Salvar dados"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      ) : null}

      <div>
        <h2 className="mb-3 text-lg font-semibold text-foreground">Permissões</h2>
        <PermissionMatrix role={role} editable={canEdit} />
      </div>
    </div>
  );
}

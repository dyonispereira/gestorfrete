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
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  toast,
} from "@gestorfrete/ui";
import type { EmployeeStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useDeleteEmployeeMutation, useEmployeeQuery, useUpdateEmployeeMutation } from "@/modules/identity/hooks/use-employees";
import { ApiError } from "@/shared/lib/api-client";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

const VARIANT_BY_STATUS: Record<EmployeeStatus, "success" | "secondary"> = { ATIVO: "success", INATIVO: "secondary" };
const LABEL_BY_STATUS: Record<EmployeeStatus, string> = { ATIVO: "Ativo", INATIVO: "Inativo" };

/** No sub-recurso — Funcionário não tem endereço, contato ou documentos (Lote Cadastros audit). */
export default function EmployeeDetailPage() {
  const params = useParams<{ id: string }>();
  const employeeId = params.id;
  const { hasPermission } = usePermissions();

  const employeeQuery = useEmployeeQuery(employeeId);
  const updateEmployee = useUpdateEmployeeMutation(employeeId);
  const deleteEmployee = useDeleteEmployeeMutation();

  const employee = employeeQuery.data;
  useBreadcrumbLabel(`/funcionarios/${employeeId}`, employee?.nome);

  const [nome, setNome] = React.useState("");
  const [cargo, setCargo] = React.useState("");
  const [hiredAt, setHiredAt] = React.useState("");

  React.useEffect(() => {
    if (!employee) return;
    setNome(employee.nome);
    setCargo(employee.cargo);
    setHiredAt(employee.hired_at ?? "");
  }, [employee]);

  const canEdit = hasPermission("identity_access.employee.edit");
  const canDelete = hasPermission("identity_access.employee.delete");

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    try {
      await updateEmployee.mutateAsync({ nome, cargo, hired_at: hiredAt || undefined });
      toast.success("Funcionário atualizado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível salvar.");
    }
  }

  async function handleDelete() {
    try {
      await deleteEmployee.mutateAsync(employeeId);
      toast.success("Funcionário desativado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível desativar.");
    }
  }

  if (employeeQuery.isLoading) return <LoadingState rows={6} />;
  if (employeeQuery.error || !employee)
    return (
      <ErrorState
        title="Não foi possível carregar o funcionário"
        description={employeeQuery.error instanceof Error ? employeeQuery.error.message : undefined}
        onRetry={() => employeeQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{employee.nome}</h1>
          <div className="mt-1 flex items-center gap-2">
            <Badge variant={VARIANT_BY_STATUS[employee.status]}>{LABEL_BY_STATUS[employee.status]}</Badge>
            <span className="text-sm text-muted-foreground">{employee.cargo}</span>
          </div>
        </div>
        {canDelete && employee.status === "ATIVO" ? (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive">Desativar funcionário</Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Desativar {employee.nome}?</AlertDialogTitle>
                <AlertDialogDescription>O funcionário deixa de aparecer nas listagens padrão.</AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancelar</AlertDialogCancel>
                <AlertDialogAction onClick={handleDelete}>Desativar</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        ) : null}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Dados do funcionário</CardTitle>
          <CardDescription>{canEdit ? "Editar dados básicos." : "Somente leitura."}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="flex flex-col gap-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="detail-nome">Nome</Label>
                <Input id="detail-nome" disabled={!canEdit} value={nome} onChange={(event) => setNome(event.target.value)} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="detail-cargo">Cargo</Label>
                <Input id="detail-cargo" disabled={!canEdit} value={cargo} onChange={(event) => setCargo(event.target.value)} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="detail-hired-at">Data de admissão</Label>
                <Input id="detail-hired-at" type="date" disabled={!canEdit} value={hiredAt} onChange={(event) => setHiredAt(event.target.value)} />
              </div>
            </div>
            {canEdit ? (
              <div className="flex justify-end">
                <Button type="submit" disabled={updateEmployee.isPending}>
                  {updateEmployee.isPending ? "Salvando…" : "Salvar alterações"}
                </Button>
              </div>
            ) : null}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

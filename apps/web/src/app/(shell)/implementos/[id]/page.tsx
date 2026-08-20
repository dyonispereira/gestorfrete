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
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  toast,
} from "@gestorfrete/ui";
import type { BodyType, ImplementAvailability } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useDeleteImplementMutation, useImplementQuery, useUpdateImplementMutation } from "@/modules/fleet/hooks/use-implements";
import { ImplementStatusBadge } from "@/modules/fleet/components/implement-status-badge";
import { ApiError } from "@/shared/lib/api-client";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

const BODY_TYPE_LABEL: Record<BodyType, string> = {
  CARRETA: "Carreta",
  TANQUE: "Tanque",
  BAU: "Baú",
  GRANELEIRO: "Graneleiro",
  PRANCHA: "Prancha",
  FRIGORIFICO: "Frigorífico",
  GAIOLA: "Gaiola",
};

const AVAILABILITY_LABEL: Record<ImplementAvailability, string> = { DISPONIVEL: "Disponível", EM_USO: "Em uso", INATIVO: "Inativo" };

export default function ImplementDetailPage() {
  const params = useParams<{ id: string }>();
  const implementId = params.id;
  const { hasPermission } = usePermissions();

  const implementQuery = useImplementQuery(implementId);
  const updateImplement = useUpdateImplementMutation(implementId);
  const deleteImplement = useDeleteImplementMutation();

  const implement = implementQuery.data;
  useBreadcrumbLabel(`/implementos/${implementId}`, implement?.plate);

  const [bodyType, setBodyType] = React.useState<BodyType>("CARRETA");
  const [loadCapacity, setLoadCapacity] = React.useState("");
  const [availability, setAvailability] = React.useState<ImplementAvailability>("DISPONIVEL");

  React.useEffect(() => {
    if (!implement) return;
    setBodyType(implement.body_type);
    setLoadCapacity(implement.load_capacity);
    setAvailability(implement.availability_status);
  }, [implement]);

  const canEdit = hasPermission("fleet.implement.edit");
  const canDelete = hasPermission("fleet.implement.delete");

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    try {
      await updateImplement.mutateAsync({ body_type: bodyType, load_capacity: loadCapacity, availability_status: availability });
      toast.success("Implemento atualizado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível salvar.");
    }
  }

  async function handleDelete() {
    try {
      await deleteImplement.mutateAsync(implementId);
      toast.success("Implemento desativado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível desativar.");
    }
  }

  if (implementQuery.isLoading) return <LoadingState rows={6} />;
  if (implementQuery.error || !implement)
    return (
      <ErrorState
        title="Não foi possível carregar o implemento"
        description={implementQuery.error instanceof Error ? implementQuery.error.message : undefined}
        onRetry={() => implementQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{implement.plate}</h1>
          <div className="mt-1 flex items-center gap-2">
            <ImplementStatusBadge status={implement.availability_status} />
            <span className="text-sm text-muted-foreground">RENAVAM {implement.renavam}</span>
          </div>
        </div>
        {canDelete ? (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive">Desativar implemento</Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Desativar {implement.plate}?</AlertDialogTitle>
                <AlertDialogDescription>O implemento deixa de aparecer nas listagens padrão.</AlertDialogDescription>
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
          <CardTitle>Dados do implemento</CardTitle>
          <CardDescription>{canEdit ? "Placa e RENAVAM não podem ser alterados." : "Somente leitura."}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="flex flex-col gap-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="flex flex-col gap-1.5">
                <Label>Tipo de carroceria</Label>
                <Select value={bodyType} onValueChange={(value) => setBodyType(value as BodyType)} disabled={!canEdit}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(Object.keys(BODY_TYPE_LABEL) as BodyType[]).map((value) => (
                      <SelectItem key={value} value={value}>
                        {BODY_TYPE_LABEL[value]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="detail-load-capacity">Capacidade de carga (kg)</Label>
                <Input id="detail-load-capacity" disabled={!canEdit} value={loadCapacity} onChange={(event) => setLoadCapacity(event.target.value)} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label>Disponibilidade</Label>
                <Select value={availability} onValueChange={(value) => setAvailability(value as ImplementAvailability)} disabled={!canEdit}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(Object.keys(AVAILABILITY_LABEL) as ImplementAvailability[]).map((value) => (
                      <SelectItem key={value} value={value}>
                        {AVAILABILITY_LABEL[value]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            {canEdit ? (
              <div className="flex justify-end">
                <Button type="submit" disabled={updateImplement.isPending}>
                  {updateImplement.isPending ? "Salvando…" : "Salvar alterações"}
                </Button>
              </div>
            ) : null}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

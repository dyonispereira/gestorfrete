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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  toast,
} from "@gestorfrete/ui";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useBlockDriverMutation, useDriverQuery, useUnblockDriverMutation, useUpdateDriverMutation } from "@/modules/drivers/hooks/use-drivers";
import { DriverStatusBadge } from "@/modules/drivers/components/driver-status-badge";
import { DriverDocumentsTab } from "@/modules/drivers/components/driver-documents-tab";
import { ApiError } from "@/shared/lib/api-client";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

const EMPLOYMENT_TYPE_LABEL = { EMPREGADO: "Empregado", AUTONOMO: "Autônomo" } as const;

export default function DriverDetailPage() {
  const params = useParams<{ id: string }>();
  const driverId = params.id;
  const { hasPermission } = usePermissions();

  const driverQuery = useDriverQuery(driverId);
  const updateDriver = useUpdateDriverMutation(driverId);
  const blockDriver = useBlockDriverMutation(driverId);
  const unblockDriver = useUnblockDriverMutation(driverId);

  const driver = driverQuery.data;
  useBreadcrumbLabel(`/motoristas/${driverId}`, driver?.nome);

  const [nome, setNome] = React.useState("");
  const [telefone, setTelefone] = React.useState("");
  const [email, setEmail] = React.useState("");

  React.useEffect(() => {
    if (!driver) return;
    setNome(driver.nome);
    setTelefone(driver.telefone ?? "");
    setEmail(driver.email ?? "");
  }, [driver]);

  const canEdit = hasPermission("drivers.driver.edit");
  const canBlock = hasPermission("drivers.driver.block");
  const canUnblock = hasPermission("drivers.driver.unblock");

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    try {
      await updateDriver.mutateAsync({ nome, telefone: telefone || undefined, email: email || undefined });
      toast.success("Motorista atualizado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível salvar.");
    }
  }

  async function handleBlock() {
    try {
      await blockDriver.mutateAsync();
      toast.success("Motorista bloqueado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível bloquear.");
    }
  }

  async function handleUnblock() {
    try {
      await unblockDriver.mutateAsync();
      toast.success("Motorista desbloqueado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível desbloquear.");
    }
  }

  if (driverQuery.isLoading) return <LoadingState rows={6} />;
  if (driverQuery.error || !driver)
    return (
      <ErrorState
        title="Não foi possível carregar o motorista"
        description={driverQuery.error instanceof Error ? driverQuery.error.message : undefined}
        onRetry={() => driverQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{driver.nome}</h1>
          <div className="mt-1 flex items-center gap-2">
            <DriverStatusBadge status={driver.fitness_status} />
            <span className="text-sm text-muted-foreground">
              {driver.cpf} — {EMPLOYMENT_TYPE_LABEL[driver.employment_type]}
            </span>
          </div>
        </div>
        {driver.fitness_status === "APTO" && canBlock ? (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive">Bloquear</Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Bloquear {driver.nome}?</AlertDialogTitle>
                <AlertDialogDescription>O motorista fica indisponível para novas viagens.</AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancelar</AlertDialogCancel>
                <AlertDialogAction onClick={handleBlock}>Bloquear</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        ) : driver.fitness_status === "BLOQUEADO" && canUnblock ? (
          <Button onClick={handleUnblock} disabled={unblockDriver.isPending}>
            {unblockDriver.isPending ? "Desbloqueando…" : "Desbloquear"}
          </Button>
        ) : null}
      </div>

      <Tabs defaultValue="dados">
        <TabsList>
          <TabsTrigger value="dados">Dados</TabsTrigger>
          <TabsTrigger value="documentos">Documentos</TabsTrigger>
        </TabsList>

        <TabsContent value="dados">
          <Card>
            <CardHeader>
              <CardTitle>Dados do motorista</CardTitle>
              <CardDescription>{canEdit ? "CPF e vínculo não podem ser alterados." : "Somente leitura."}</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSave} className="flex flex-col gap-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="detail-nome">Nome</Label>
                    <Input id="detail-nome" disabled={!canEdit} value={nome} onChange={(event) => setNome(event.target.value)} />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="detail-telefone">Telefone</Label>
                    <Input id="detail-telefone" disabled={!canEdit} value={telefone} onChange={(event) => setTelefone(event.target.value)} />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="detail-email">E-mail</Label>
                    <Input id="detail-email" type="email" disabled={!canEdit} value={email} onChange={(event) => setEmail(event.target.value)} />
                  </div>
                </div>
                {canEdit ? (
                  <div className="flex justify-end">
                    <Button type="submit" disabled={updateDriver.isPending}>
                      {updateDriver.isPending ? "Salvando…" : "Salvar alterações"}
                    </Button>
                  </div>
                ) : null}
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="documentos">
          <DriverDocumentsTab driverId={driverId} editable={canEdit} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

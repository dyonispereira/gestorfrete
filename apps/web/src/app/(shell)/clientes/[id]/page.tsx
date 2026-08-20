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
import { useClientQuery, useDeactivateClientMutation, useUpdateClientMutation } from "@/modules/crm/hooks/use-clients";
import { ClientStatusBadge } from "@/modules/crm/components/client-status-badge";
import { ContactsTab } from "@/modules/crm/components/contacts-tab";
import { AddressesTab } from "@/shared/addresses/components/addresses-tab";
import { ApiError } from "@/shared/lib/api-client";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

export default function ClientDetailPage() {
  const params = useParams<{ id: string }>();
  const clientId = params.id;
  const { hasPermission } = usePermissions();

  const clientQuery = useClientQuery(clientId);
  const updateClient = useUpdateClientMutation(clientId);
  const deactivateClient = useDeactivateClientMutation();

  const client = clientQuery.data;
  useBreadcrumbLabel(`/clientes/${clientId}`, client?.razao_social);

  const [razaoSocial, setRazaoSocial] = React.useState("");
  const [nomeFantasia, setNomeFantasia] = React.useState("");
  const [telefone, setTelefone] = React.useState("");
  const [email, setEmail] = React.useState("");

  React.useEffect(() => {
    if (!client) return;
    setRazaoSocial(client.razao_social);
    setNomeFantasia(client.nome_fantasia ?? "");
    setTelefone(client.telefone ?? "");
    setEmail(client.email ?? "");
  }, [client]);

  const canEdit = hasPermission("crm.client.edit");
  const canDeactivate = hasPermission("crm.client.delete");

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    try {
      await updateClient.mutateAsync({
        razao_social: razaoSocial,
        nome_fantasia: nomeFantasia || undefined,
        telefone: telefone || undefined,
        email: email || undefined,
      });
      toast.success("Cliente atualizado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível salvar.");
    }
  }

  async function handleDeactivate() {
    try {
      await deactivateClient.mutateAsync(clientId);
      toast.success("Cliente desativado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível desativar.");
    }
  }

  if (clientQuery.isLoading) return <LoadingState rows={6} />;
  if (clientQuery.error || !client)
    return (
      <ErrorState
        title="Não foi possível carregar o cliente"
        description={clientQuery.error instanceof Error ? clientQuery.error.message : undefined}
        onRetry={() => clientQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{client.razao_social}</h1>
          <div className="mt-1 flex items-center gap-2">
            <ClientStatusBadge status={client.status} />
            <span className="text-sm text-muted-foreground">{client.document}</span>
          </div>
        </div>
        {canDeactivate && client.status === "ATIVO" ? (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive">Desativar cliente</Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Desativar {client.razao_social}?</AlertDialogTitle>
                <AlertDialogDescription>O cliente deixa de aparecer nas listagens padrão.</AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancelar</AlertDialogCancel>
                <AlertDialogAction onClick={handleDeactivate}>Desativar</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        ) : null}
      </div>

      <Tabs defaultValue="dados">
        <TabsList>
          <TabsTrigger value="dados">Dados</TabsTrigger>
          <TabsTrigger value="enderecos">Endereços</TabsTrigger>
          <TabsTrigger value="contatos">Contatos</TabsTrigger>
        </TabsList>

        <TabsContent value="dados">
          <Card>
            <CardHeader>
              <CardTitle>Dados do cliente</CardTitle>
              <CardDescription>{canEdit ? "Documento não pode ser alterado." : "Somente leitura."}</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSave} className="flex flex-col gap-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="detail-razao-social">Razão social</Label>
                    <Input id="detail-razao-social" disabled={!canEdit} value={razaoSocial} onChange={(event) => setRazaoSocial(event.target.value)} />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="detail-nome-fantasia">Nome fantasia</Label>
                    <Input id="detail-nome-fantasia" disabled={!canEdit} value={nomeFantasia} onChange={(event) => setNomeFantasia(event.target.value)} />
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
                    <Button type="submit" disabled={updateClient.isPending}>
                      {updateClient.isPending ? "Salvando…" : "Salvar alterações"}
                    </Button>
                  </div>
                ) : null}
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="enderecos">
          <AddressesTab ownerBasePath="clients" ownerId={clientId} editable={canEdit} />
        </TabsContent>

        <TabsContent value="contatos">
          <ContactsTab clientId={clientId} editable={hasPermission("crm.client_contact.create") || hasPermission("crm.client_contact.edit")} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

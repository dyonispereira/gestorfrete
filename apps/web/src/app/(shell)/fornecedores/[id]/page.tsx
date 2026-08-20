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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  toast,
} from "@gestorfrete/ui";
import type { SupplierCategory } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useDeleteSupplierMutation, useSupplierQuery, useUpdateSupplierMutation } from "@/modules/maintenance/hooks/use-suppliers";
import { SupplierStatusBadge } from "@/modules/maintenance/components/supplier-status-badge";
import { SUPPLIER_CATEGORY_LABEL } from "@/modules/maintenance/components/supplier-category-label";
import { AddressesTab } from "@/shared/addresses/components/addresses-tab";
import { ApiError } from "@/shared/lib/api-client";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

export default function SupplierDetailPage() {
  const params = useParams<{ id: string }>();
  const supplierId = params.id;
  const { hasPermission } = usePermissions();

  const supplierQuery = useSupplierQuery(supplierId);
  const updateSupplier = useUpdateSupplierMutation(supplierId);
  const deleteSupplier = useDeleteSupplierMutation();

  const supplier = supplierQuery.data;
  useBreadcrumbLabel(`/fornecedores/${supplierId}`, supplier?.razao_social);

  const [razaoSocial, setRazaoSocial] = React.useState("");
  const [telefone, setTelefone] = React.useState("");
  const [category, setCategory] = React.useState<SupplierCategory | "">("");

  React.useEffect(() => {
    if (!supplier) return;
    setRazaoSocial(supplier.razao_social);
    setTelefone(supplier.telefone ?? "");
    setCategory(supplier.category ?? "");
  }, [supplier]);

  const canEdit = hasPermission("maintenance.supplier.edit");
  const canDelete = hasPermission("maintenance.supplier.delete");

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    try {
      await updateSupplier.mutateAsync({ razao_social: razaoSocial, telefone: telefone || undefined, category: category || undefined });
      toast.success("Fornecedor atualizado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível salvar.");
    }
  }

  async function handleDelete() {
    try {
      await deleteSupplier.mutateAsync(supplierId);
      toast.success("Fornecedor desativado.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível desativar.");
    }
  }

  if (supplierQuery.isLoading) return <LoadingState rows={6} />;
  if (supplierQuery.error || !supplier)
    return (
      <ErrorState
        title="Não foi possível carregar o fornecedor"
        description={supplierQuery.error instanceof Error ? supplierQuery.error.message : undefined}
        onRetry={() => supplierQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{supplier.razao_social}</h1>
          <div className="mt-1 flex items-center gap-2">
            <SupplierStatusBadge status={supplier.status} />
            <span className="text-sm text-muted-foreground">{supplier.cnpj}</span>
          </div>
        </div>
        {canDelete && supplier.status === "ATIVO" ? (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive">Desativar fornecedor</Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Desativar {supplier.razao_social}?</AlertDialogTitle>
                <AlertDialogDescription>O fornecedor deixa de aparecer nas listagens padrão.</AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancelar</AlertDialogCancel>
                <AlertDialogAction onClick={handleDelete}>Desativar</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        ) : null}
      </div>

      <Tabs defaultValue="dados">
        <TabsList>
          <TabsTrigger value="dados">Dados</TabsTrigger>
          <TabsTrigger value="enderecos">Endereços</TabsTrigger>
        </TabsList>

        <TabsContent value="dados">
          <Card>
            <CardHeader>
              <CardTitle>Dados do fornecedor</CardTitle>
              <CardDescription>{canEdit ? "CNPJ não pode ser alterado." : "Somente leitura."}</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSave} className="flex flex-col gap-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="detail-razao-social">Razão social</Label>
                    <Input id="detail-razao-social" disabled={!canEdit} value={razaoSocial} onChange={(event) => setRazaoSocial(event.target.value)} />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="detail-telefone">Telefone</Label>
                    <Input id="detail-telefone" disabled={!canEdit} value={telefone} onChange={(event) => setTelefone(event.target.value)} />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label>Categoria</Label>
                    <Select value={category} onValueChange={(value) => setCategory(value as SupplierCategory)} disabled={!canEdit}>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione…" />
                      </SelectTrigger>
                      <SelectContent>
                        {(Object.keys(SUPPLIER_CATEGORY_LABEL) as SupplierCategory[]).map((value) => (
                          <SelectItem key={value} value={value}>
                            {SUPPLIER_CATEGORY_LABEL[value]}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                {canEdit ? (
                  <div className="flex justify-end">
                    <Button type="submit" disabled={updateSupplier.isPending}>
                      {updateSupplier.isPending ? "Salvando…" : "Salvar alterações"}
                    </Button>
                  </div>
                ) : null}
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="enderecos">
          <AddressesTab ownerBasePath="suppliers" ownerId={supplierId} editable={canEdit} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

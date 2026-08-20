"use client";

import * as React from "react";
import { MapPin, Plus } from "lucide-react";

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
import type { Address, AddressType, CreateAddressRequest } from "@gestorfrete/types";

import {
  useAddressesQuery,
  useCreateAddressMutation,
  useDeleteAddressMutation,
  useUpdateAddressMutation,
} from "@/shared/addresses/hooks/use-addresses";
import type { AddressOwnerBasePath } from "@/shared/addresses/services/addresses";
import { ApiError } from "@/shared/lib/api-client";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const ADDRESS_TYPE_LABEL: Record<AddressType, string> = {
  PRINCIPAL: "Principal",
  COBRANCA: "Cobrança",
  ENTREGA: "Entrega",
  OUTRO: "Outro",
};

const EMPTY_FORM: CreateAddressRequest = {
  type: "PRINCIPAL",
  logradouro: "",
  numero: "",
  complemento: "",
  bairro: "",
  cidade: "",
  uf: "",
  cep: "",
};

interface AddressesTabProps {
  ownerBasePath: AddressOwnerBasePath;
  ownerId: string;
  editable: boolean;
}

/** Reused by Cliente and Fornecedor — Endereço is the one real polymorphic sub-recurso (Motorista/Funcionário don't have it). */
export function AddressesTab({ ownerBasePath, ownerId, editable }: AddressesTabProps) {
  const addressesQuery = useAddressesQuery(ownerBasePath, ownerId);
  const createAddress = useCreateAddressMutation(ownerBasePath, ownerId);
  const updateAddress = useUpdateAddressMutation(ownerBasePath, ownerId);
  const deleteAddress = useDeleteAddressMutation(ownerBasePath, ownerId);

  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Address | null>(null);
  const [form, setForm] = React.useState<CreateAddressRequest>(EMPTY_FORM);
  const [formError, setFormError] = React.useState<string | null>(null);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setDrawerOpen(true);
  }

  function openEdit(address: Address) {
    setEditing(address);
    setForm({
      type: address.type,
      logradouro: address.logradouro,
      numero: address.numero ?? "",
      complemento: address.complemento ?? "",
      bairro: address.bairro,
      cidade: address.cidade,
      uf: address.uf,
      cep: address.cep,
    });
    setFormError(null);
    setDrawerOpen(true);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      if (editing) {
        await updateAddress.mutateAsync({ addressId: editing.id, body: form });
        toast.success("Endereço atualizado.");
      } else {
        await createAddress.mutateAsync(form);
        toast.success("Endereço adicionado.");
      }
      setDrawerOpen(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível salvar o endereço.");
    }
  }

  async function handleDelete(addressId: string) {
    try {
      await deleteAddress.mutateAsync(addressId);
      toast.success("Endereço removido.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível remover o endereço.");
    }
  }

  if (addressesQuery.isLoading) return <LoadingState rows={3} />;
  if (addressesQuery.error)
    return (
      <ErrorState description="Não foi possível carregar os endereços." onRetry={() => addressesQuery.refetch()} />
    );

  const addresses = addressesQuery.data?.data ?? [];

  return (
    <div className="flex flex-col gap-4">
      {editable ? (
        <div className="flex justify-end">
          <Button size="sm" onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Novo endereço
          </Button>
        </div>
      ) : null}

      {addresses.length === 0 ? (
        <EmptyState icon={MapPin} title="Nenhum endereço cadastrado" />
      ) : (
        <div className="flex flex-col gap-3">
          {addresses.map((address) => (
            <div key={address.id} className="flex items-start justify-between gap-4 rounded-md border border-border p-4">
              <div className="flex flex-col gap-1">
                <Badge variant="outline">{ADDRESS_TYPE_LABEL[address.type]}</Badge>
                <p className="text-sm text-foreground">
                  {address.logradouro}
                  {address.numero ? `, ${address.numero}` : ""}
                  {address.complemento ? ` — ${address.complemento}` : ""}
                </p>
                <p className="text-sm text-muted-foreground">
                  {address.bairro} — {address.cidade}/{address.uf} — {address.cep}
                </p>
              </div>
              {editable ? (
                <div className="flex shrink-0 gap-2">
                  <Button size="sm" variant="outline" onClick={() => openEdit(address)}>
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
                        <AlertDialogTitle>Remover este endereço?</AlertDialogTitle>
                        <AlertDialogDescription>Essa ação não pode ser desfeita pela tela.</AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancelar</AlertDialogCancel>
                        <AlertDialogAction onClick={() => handleDelete(address.id)}>Remover</AlertDialogAction>
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
        <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>{editing ? "Editar endereço" : "Novo endereço"}</SheetTitle>
            <SheetDescription>Campos de acordo com o cadastro de endereço padrão do sistema.</SheetDescription>
          </SheetHeader>
          <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label>Tipo</Label>
              <Select value={form.type} onValueChange={(value) => setForm((f) => ({ ...f, type: value as AddressType }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(Object.keys(ADDRESS_TYPE_LABEL) as AddressType[]).map((type) => (
                    <SelectItem key={type} value={type}>
                      {ADDRESS_TYPE_LABEL[type]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="col-span-2 flex flex-col gap-1.5">
                <Label htmlFor="address-logradouro">Logradouro</Label>
                <Input
                  id="address-logradouro"
                  required
                  value={form.logradouro}
                  onChange={(event) => setForm((f) => ({ ...f, logradouro: event.target.value }))}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="address-numero">Número</Label>
                <Input
                  id="address-numero"
                  value={form.numero}
                  onChange={(event) => setForm((f) => ({ ...f, numero: event.target.value }))}
                />
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="address-complemento">Complemento</Label>
              <Input
                id="address-complemento"
                value={form.complemento}
                onChange={(event) => setForm((f) => ({ ...f, complemento: event.target.value }))}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="address-bairro">Bairro</Label>
              <Input
                id="address-bairro"
                required
                value={form.bairro}
                onChange={(event) => setForm((f) => ({ ...f, bairro: event.target.value }))}
              />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="col-span-2 flex flex-col gap-1.5">
                <Label htmlFor="address-cidade">Cidade</Label>
                <Input
                  id="address-cidade"
                  required
                  value={form.cidade}
                  onChange={(event) => setForm((f) => ({ ...f, cidade: event.target.value }))}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="address-uf">UF</Label>
                <Input
                  id="address-uf"
                  required
                  maxLength={2}
                  value={form.uf}
                  onChange={(event) => setForm((f) => ({ ...f, uf: event.target.value.toUpperCase() }))}
                />
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="address-cep">CEP</Label>
              <Input
                id="address-cep"
                required
                value={form.cep}
                onChange={(event) => setForm((f) => ({ ...f, cep: event.target.value }))}
              />
            </div>

            {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

            <div className="mt-auto flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setDrawerOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createAddress.isPending || updateAddress.isPending}>
                {createAddress.isPending || updateAddress.isPending ? "Salvando…" : "Salvar"}
              </Button>
            </div>
          </form>
        </SheetContent>
      </Sheet>
    </div>
  );
}

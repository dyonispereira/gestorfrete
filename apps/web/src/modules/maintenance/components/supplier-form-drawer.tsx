"use client";

import * as React from "react";

import {
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
import type { SupplierCategory } from "@gestorfrete/types";

import { useCreateSupplierMutation } from "@/modules/maintenance/hooks/use-suppliers";
import { SUPPLIER_CATEGORY_LABEL } from "./supplier-category-label";
import { ApiError } from "@/shared/lib/api-client";

interface SupplierFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** Create-only — CNPJ is immutable, there's no rename-document endpoint. */
export function SupplierFormDrawer({ open, onOpenChange }: SupplierFormDrawerProps) {
  const [razaoSocial, setRazaoSocial] = React.useState("");
  const [cnpj, setCnpj] = React.useState("");
  const [telefone, setTelefone] = React.useState("");
  const [category, setCategory] = React.useState<SupplierCategory | "">("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const createSupplier = useCreateSupplierMutation();

  function reset() {
    setRazaoSocial("");
    setCnpj("");
    setTelefone("");
    setCategory("");
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createSupplier.mutateAsync({
        razao_social: razaoSocial,
        cnpj,
        telefone: telefone || undefined,
        category: category || undefined,
      });
      toast.success("Fornecedor criado.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar o fornecedor.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Novo fornecedor</SheetTitle>
          <SheetDescription>O CNPJ não pode ser alterado depois.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="supplier-razao-social">Razão social</Label>
            <Input id="supplier-razao-social" required value={razaoSocial} onChange={(event) => setRazaoSocial(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="supplier-cnpj">CNPJ</Label>
            <Input id="supplier-cnpj" required value={cnpj} onChange={(event) => setCnpj(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="supplier-telefone">Telefone</Label>
            <Input id="supplier-telefone" value={telefone} onChange={(event) => setTelefone(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Categoria</Label>
            <Select value={category} onValueChange={(value) => setCategory(value as SupplierCategory)}>
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

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createSupplier.isPending}>
              {createSupplier.isPending ? "Criando…" : "Criar fornecedor"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

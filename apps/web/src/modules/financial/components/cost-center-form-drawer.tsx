"use client";

import * as React from "react";

import { Button, Input, Label, Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, toast } from "@gestorfrete/ui";

import { useCreateCostCenterMutation } from "@/modules/financial/hooks/use-cost-centers";
import { ApiError } from "@/shared/lib/api-client";

interface CostCenterFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** No Filial field — no endpoint exists to list Filiais to pick from (Lote Cadastros audit). */
export function CostCenterFormDrawer({ open, onOpenChange }: CostCenterFormDrawerProps) {
  const [nome, setNome] = React.useState("");
  const [accountingCode, setAccountingCode] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const createCostCenter = useCreateCostCenterMutation();

  function reset() {
    setNome("");
    setAccountingCode("");
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createCostCenter.mutateAsync({ nome, accounting_code: accountingCode });
      toast.success("Centro de custo criado.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar o centro de custo.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Novo centro de custo</SheetTitle>
          <SheetDescription>Vínculo com Filial ainda não tem tela própria de Filiais — fica de fora por enquanto.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="cost-center-nome">Nome</Label>
            <Input id="cost-center-nome" required value={nome} onChange={(event) => setNome(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="cost-center-accounting-code">Código contábil</Label>
            <Input id="cost-center-accounting-code" required value={accountingCode} onChange={(event) => setAccountingCode(event.target.value)} />
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createCostCenter.isPending}>
              {createCostCenter.isPending ? "Criando…" : "Criar centro de custo"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

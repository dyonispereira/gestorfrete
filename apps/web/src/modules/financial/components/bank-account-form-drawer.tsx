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
import type { BankAccountType } from "@gestorfrete/types";

import { useCreateBankAccountMutation } from "@/modules/financial/hooks/use-bank-accounts";
import { ApiError } from "@/shared/lib/api-client";

const TYPE_LABEL: Record<BankAccountType, string> = { CORRENTE: "Corrente", POUPANCA: "Poupança" };

export function BankAccountFormDrawer({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const [bank, setBank] = React.useState("");
  const [branch, setBranch] = React.useState("");
  const [accountNumber, setAccountNumber] = React.useState("");
  const [type, setType] = React.useState<BankAccountType>("CORRENTE");
  const [formError, setFormError] = React.useState<string | null>(null);

  const createBankAccount = useCreateBankAccountMutation();

  function reset() {
    setBank(""); setBranch(""); setAccountNumber(""); setType("CORRENTE"); setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createBankAccount.mutateAsync({ bank, branch, account_number: accountNumber, type });
      toast.success("Conta bancária criada.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar a conta bancária.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Nova conta bancária</SheetTitle>
          <SheetDescription>Saldo é calculado a partir de contas pagas/conciliadas — sem lançamento manual de extrato ainda.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="bank-account-bank">Banco</Label>
            <Input id="bank-account-bank" required value={bank} onChange={(e) => setBank(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="bank-account-branch">Agência</Label>
            <Input id="bank-account-branch" required value={branch} onChange={(e) => setBranch(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="bank-account-number">Número da conta</Label>
            <Input id="bank-account-number" required value={accountNumber} onChange={(e) => setAccountNumber(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="bank-account-type">Tipo</Label>
            <Select value={type} onValueChange={(v) => setType(v as BankAccountType)}>
              <SelectTrigger id="bank-account-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(TYPE_LABEL) as BankAccountType[]).map((value) => (
                  <SelectItem key={value} value={value}>
                    {TYPE_LABEL[value]}
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
            <Button type="submit" disabled={createBankAccount.isPending}>
              {createBankAccount.isPending ? "Criando…" : "Criar conta bancária"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

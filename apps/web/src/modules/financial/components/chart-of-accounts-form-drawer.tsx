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
import type { ChartOfAccounts, ChartOfAccountsStatus, ChartOfAccountsType } from "@gestorfrete/types";

import {
  useChartOfAccountsListQuery,
  useCreateChartOfAccountsMutation,
  useUpdateChartOfAccountsMutation,
} from "@/modules/financial/hooks/use-chart-of-accounts";
import { ApiError } from "@/shared/lib/api-client";

const TYPE_LABEL: Record<ChartOfAccountsType, string> = { RECEITA: "Receita", DESPESA: "Despesa" };

interface ChartOfAccountsFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  account?: ChartOfAccounts | null;
}

/** Sem parent no `create` do próprio account (evita ciclo trivial) — validação real de ciclo é do
 * backend (`FINANCIAL_CHART_OF_ACCOUNTS_CYCLE_DETECTED`), aqui só evita o caso óbvio. */
export function ChartOfAccountsFormDrawer({ open, onOpenChange, account }: ChartOfAccountsFormDrawerProps) {
  const isEdit = Boolean(account);
  const [accountCode, setAccountCode] = React.useState("");
  const [name, setName] = React.useState("");
  const [type, setType] = React.useState<ChartOfAccountsType>("DESPESA");
  const [parentId, setParentId] = React.useState("");
  const [status, setStatus] = React.useState<ChartOfAccountsStatus>("ATIVO");
  const [formError, setFormError] = React.useState<string | null>(null);

  const accountsQuery = useChartOfAccountsListQuery({ limit: 100 });
  const createAccount = useCreateChartOfAccountsMutation();
  const updateAccount = useUpdateChartOfAccountsMutation();

  React.useEffect(() => {
    if (account) {
      setAccountCode(account.account_code);
      setName(account.name);
      setType(account.type);
      setParentId(account.parent_id ?? "");
      setStatus(account.status);
    } else {
      setAccountCode(""); setName(""); setType("DESPESA"); setParentId(""); setStatus("ATIVO");
    }
    setFormError(null);
  }, [account, open]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      if (isEdit && account) {
        await updateAccount.mutateAsync({
          id: account.id, body: { name, parent_id: parentId || undefined, status },
        });
        toast.success("Conta atualizada.");
      } else {
        await createAccount.mutateAsync({ account_code: accountCode, name, type, parent_id: parentId || undefined });
        toast.success("Conta criada.");
      }
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível salvar a conta.");
    }
  }

  const isPending = createAccount.isPending || updateAccount.isPending;
  const otherAccounts = (accountsQuery.data?.data ?? []).filter((a) => a.id !== account?.id);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>{isEdit ? "Editar conta contábil" : "Nova conta contábil"}</SheetTitle>
          <SheetDescription>Plano de Contas hierárquico — cada conta pode ter uma conta-pai.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="chart-code">Código contábil</Label>
            <Input id="chart-code" required disabled={isEdit} value={accountCode} onChange={(e) => setAccountCode(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="chart-name">Nome</Label>
            <Input id="chart-name" required value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="chart-type">Tipo</Label>
            <Select value={type} onValueChange={(v) => setType(v as ChartOfAccountsType)} disabled={isEdit}>
              <SelectTrigger id="chart-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(TYPE_LABEL) as ChartOfAccountsType[]).map((value) => (
                  <SelectItem key={value} value={value}>
                    {TYPE_LABEL[value]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="chart-parent">Conta-pai (opcional)</Label>
            <Select value={parentId} onValueChange={setParentId}>
              <SelectTrigger id="chart-parent">
                <SelectValue placeholder="Nenhuma — conta de nível raiz" />
              </SelectTrigger>
              <SelectContent>
                {otherAccounts.map((option) => (
                  <SelectItem key={option.id} value={option.id}>
                    {option.account_code} — {option.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {isEdit ? (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="chart-status">Status</Label>
              <Select value={status} onValueChange={(v) => setStatus(v as ChartOfAccountsStatus)}>
                <SelectTrigger id="chart-status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ATIVO">Ativo</SelectItem>
                  <SelectItem value="INATIVO">Inativo</SelectItem>
                </SelectContent>
              </Select>
            </div>
          ) : null}

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Salvando…" : isEdit ? "Salvar" : "Criar conta"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

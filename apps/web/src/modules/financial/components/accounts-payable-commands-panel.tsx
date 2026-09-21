"use client";

import * as React from "react";

import {
  Button,
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
  Textarea,
  toast,
} from "@gestorfrete/ui";
import type { AccountsPayable } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import {
  useApproveAccountsPayableMutation,
  usePayAccountsPayableMutation,
  useRejectAccountsPayableMutation,
} from "@/modules/financial/hooks/use-accounts-payable";
import { useBankAccountsListQuery } from "@/modules/financial/hooks/use-bank-accounts";
import { ApiError } from "@/shared/lib/api-client";

type DialogKey = "reject" | "pay";

/** Só renderiza o(s) comando(s) válido(s) para o `status` atual — mesmo princípio de
 * `WorkOrderCommandsPanel`/`TripCommandsPanel`. `LANCADA` nunca é observável (D255-style: a
 * alçada já decide `AGUARDANDO_APROVACAO`/`APROVADA` no próprio `create`), então nenhum botão de
 * "editar"/"excluir" aparece aqui — o backend já resolveu isso antes do primeiro render. */
export function AccountsPayableCommandsPanel({ payable }: { payable: AccountsPayable }) {
  const { hasPermission } = usePermissions();
  const status = payable.status;

  const [dialog, setDialog] = React.useState<DialogKey | null>(null);
  const [justification, setJustification] = React.useState("");
  const [bankAccountId, setBankAccountId] = React.useState("");

  const approve = useApproveAccountsPayableMutation();
  const reject = useRejectAccountsPayableMutation();
  const pay = usePayAccountsPayableMutation();
  const bankAccountsQuery = useBankAccountsListQuery({ limit: 50, status: "ATIVA" });

  const canApprove = hasPermission("financial.payable.approve");
  const canReject = hasPermission("financial.payable.reject");
  const canPay = hasPermission("financial.payable.pay");

  async function handleApprove() {
    try {
      await approve.mutateAsync({ id: payable.id, body: {} });
      toast.success("Conta a pagar aprovada.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível aprovar.");
    }
  }

  async function handleReject() {
    try {
      await reject.mutateAsync({ id: payable.id, body: { justification } });
      toast.success("Conta a pagar rejeitada.");
      setDialog(null);
      setJustification("");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível rejeitar.");
    }
  }

  async function handlePay() {
    try {
      await pay.mutateAsync({ id: payable.id, body: { bank_account_id: bankAccountId } });
      toast.success("Conta a pagar paga.");
      setDialog(null);
      setBankAccountId("");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível registrar o pagamento.");
    }
  }

  const buttons: React.ReactNode[] = [];
  if (status === "AGUARDANDO_APROVACAO" && canApprove) {
    buttons.push(
      <Button key="approve" onClick={handleApprove} disabled={approve.isPending}>
        Aprovar
      </Button>
    );
  }
  if (status === "AGUARDANDO_APROVACAO" && canReject) {
    buttons.push(
      <Button key="reject" variant="destructive" onClick={() => setDialog("reject")}>
        Rejeitar
      </Button>
    );
  }
  if (status === "APROVADA" && canPay) {
    buttons.push(
      <Button key="pay" onClick={() => setDialog("pay")}>
        Pagar
      </Button>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {buttons.length > 0 ? <div className="flex flex-wrap gap-2">{buttons}</div> : null}

      <Sheet open={dialog === "reject"} onOpenChange={(open) => !open && setDialog(null)}>
        <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Rejeitar conta a pagar</SheetTitle>
            <SheetDescription>Registre o motivo — obrigatório, fica no histórico.</SheetDescription>
          </SheetHeader>
          <div className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="payable-reject-justification">Justificativa</Label>
              <Textarea
                id="payable-reject-justification" required value={justification}
                onChange={(e) => setJustification(e.target.value)}
              />
            </div>
            <div className="mt-auto flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setDialog(null)}>
                Voltar
              </Button>
              <Button variant="destructive" disabled={!justification.trim() || reject.isPending} onClick={handleReject}>
                Rejeitar conta a pagar
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>

      <Sheet open={dialog === "pay"} onOpenChange={(open) => !open && setDialog(null)}>
        <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Pagar conta a pagar</SheetTitle>
            <SheetDescription>Selecione a conta bancária de origem do pagamento.</SheetDescription>
          </SheetHeader>
          <div className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="payable-pay-bank-account">Conta bancária</Label>
              <Select value={bankAccountId} onValueChange={setBankAccountId}>
                <SelectTrigger id="payable-pay-bank-account">
                  <SelectValue placeholder="Selecione uma conta bancária ativa" />
                </SelectTrigger>
                <SelectContent>
                  {bankAccountsQuery.data?.data.map((account) => (
                    <SelectItem key={account.id} value={account.id}>
                      {account.bank} — {account.account_number}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="mt-auto flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setDialog(null)}>
                Voltar
              </Button>
              <Button disabled={!bankAccountId || pay.isPending} onClick={handlePay}>
                Confirmar pagamento
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}

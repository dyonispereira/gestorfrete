"use client";

import { Badge, Button, Table, TableBody, TableCell, TableHead, TableHeader, TableRow, toast } from "@gestorfrete/ui";
import type { PaymentMethod } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useUpdatePaymentMethodMutation } from "@/modules/financial/hooks/use-payment-methods";
import { ApiError } from "@/shared/lib/api-client";

export function PaymentMethodsTable({ paymentMethods }: { paymentMethods: PaymentMethod[] }) {
  const { hasPermission } = usePermissions();
  const updatePaymentMethod = useUpdatePaymentMethodMutation();
  const canEdit = hasPermission("financial.payment_method.edit");

  async function toggleStatus(paymentMethod: PaymentMethod) {
    const nextStatus = paymentMethod.status === "ATIVA" ? "INATIVA" : "ATIVA";
    try {
      await updatePaymentMethod.mutateAsync({ id: paymentMethod.id, body: { status: nextStatus } });
      toast.success(nextStatus === "ATIVA" ? "Forma de pagamento ativada." : "Forma de pagamento desativada.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível atualizar o status.");
    }
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Nome</TableHead>
          <TableHead>Status</TableHead>
          <TableHead />
        </TableRow>
      </TableHeader>
      <TableBody>
        {paymentMethods.map((paymentMethod) => (
          <TableRow key={paymentMethod.id}>
            <TableCell className="font-medium">{paymentMethod.nome}</TableCell>
            <TableCell>
              <Badge variant={paymentMethod.status === "ATIVA" ? "outline" : "destructive"}>
                {paymentMethod.status === "ATIVA" ? "Ativa" : "Inativa"}
              </Badge>
            </TableCell>
            <TableCell className="text-right">
              {canEdit ? (
                <Button size="sm" variant="outline" onClick={() => toggleStatus(paymentMethod)} disabled={updatePaymentMethod.isPending}>
                  {paymentMethod.status === "ATIVA" ? "Desativar" : "Ativar"}
                </Button>
              ) : null}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

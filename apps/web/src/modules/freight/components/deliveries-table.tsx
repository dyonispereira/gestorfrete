"use client";

import * as React from "react";

import { Button, Table, TableBody, TableCell, TableHead, TableHeader, TableRow, toast } from "@gestorfrete/ui";
import type { Delivery } from "@gestorfrete/types";

import { useRegisterProofOfDeliveryMutation } from "@/modules/freight/hooks/use-deliveries";
import { ApiError } from "@/shared/lib/api-client";

import { DeliveryStatusBadge } from "./delivery-status-badge";

interface DeliveriesTableProps {
  tripId: string;
  deliveries: Delivery[];
  canEdit: boolean;
  canRegisterPod: boolean;
  onEdit: (delivery: Delivery) => void;
}

/**
 * Não há `GET` para consultar se o Canhoto de uma Entrega já foi registrado — só o `POST .../
 * canhoto` existe. "Registrado nesta sessão" é rastreado localmente (`registeredIds`) só para
 * esconder o botão depois de um sucesso recente; após recarregar a página o botão volta a
 * aparecer, e clicar de novo simplesmente devolve o erro do domínio (Canhoto já registrado) —
 * comportamento honesto dado o que o Backend expõe, não uma tentativa de simular um GET que não
 * existe.
 */
export function DeliveriesTable({ tripId, deliveries, canEdit, canRegisterPod, onEdit }: DeliveriesTableProps) {
  const registerPod = useRegisterProofOfDeliveryMutation(tripId);
  const [registeredIds, setRegisteredIds] = React.useState<Set<string>>(new Set());

  async function handleRegisterPod(deliveryId: string) {
    try {
      await registerPod.mutateAsync({ deliveryId });
      toast.success("Canhoto registrado.");
      setRegisteredIds((current) => new Set(current).add(deliveryId));
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível registrar o canhoto.");
    }
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Ordem</TableHead>
          <TableHead>Destinatário</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Ações</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {deliveries.map((delivery) => (
          <TableRow key={delivery.id}>
            <TableCell className="font-medium">{delivery.order}</TableCell>
            <TableCell>{delivery.recipient}</TableCell>
            <TableCell>
              <DeliveryStatusBadge status={delivery.status} />
            </TableCell>
            <TableCell className="flex justify-end gap-2">
              {canEdit ? (
                <Button size="sm" variant="outline" onClick={() => onEdit(delivery)}>
                  Editar
                </Button>
              ) : null}
              {canRegisterPod && delivery.status === "CONCLUIDA" && !registeredIds.has(delivery.id) ? (
                <Button size="sm" onClick={() => handleRegisterPod(delivery.id)} disabled={registerPod.isPending}>
                  Registrar canhoto
                </Button>
              ) : null}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

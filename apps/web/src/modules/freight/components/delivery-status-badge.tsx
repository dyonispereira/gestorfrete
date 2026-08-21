import { Badge } from "@gestorfrete/ui";
import type { DeliveryStatus } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<DeliveryStatus, "success" | "warning" | "destructive" | "secondary" | "outline"> = {
  PENDENTE: "outline",
  CONCLUIDA: "success",
  RECUSADA: "destructive",
  DEVOLVIDA: "warning",
  CANCELADA: "secondary",
};

const LABEL_BY_STATUS: Record<DeliveryStatus, string> = {
  PENDENTE: "Pendente",
  CONCLUIDA: "Concluída",
  RECUSADA: "Recusada",
  DEVOLVIDA: "Devolvida",
  CANCELADA: "Cancelada",
};

export function DeliveryStatusBadge({ status }: { status: DeliveryStatus }) {
  return <Badge variant={VARIANT_BY_STATUS[status]}>{LABEL_BY_STATUS[status]}</Badge>;
}

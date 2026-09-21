import { Badge } from "@gestorfrete/ui";
import type { ReceivableStatus } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<ReceivableStatus, "outline" | "warning" | "success" | "secondary"> = {
  PENDENTE: "outline",
  VENCIDA: "warning",
  PARCIALMENTE_RECEBIDO: "secondary",
  RECEBIDA: "success",
  CONCILIADA: "success",
};

const LABEL_BY_STATUS: Record<ReceivableStatus, string> = {
  PENDENTE: "Pendente",
  VENCIDA: "Vencida",
  PARCIALMENTE_RECEBIDO: "Parcialmente recebida",
  RECEBIDA: "Recebida",
  CONCILIADA: "Conciliada",
};

export function ReceivableStatusBadge({ status }: { status: ReceivableStatus }) {
  return <Badge variant={VARIANT_BY_STATUS[status]}>{LABEL_BY_STATUS[status]}</Badge>;
}

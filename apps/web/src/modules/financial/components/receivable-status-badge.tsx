import { Badge } from "@gestorfrete/ui";
import type { ReceivableStatus } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<ReceivableStatus, "outline" | "warning" | "success" | "secondary"> = {
  PENDENTE: "outline",
  VENCIDA: "warning",
  RECEBIDA: "success",
  CONCILIADA: "success",
};

const LABEL_BY_STATUS: Record<ReceivableStatus, string> = {
  PENDENTE: "Pendente",
  VENCIDA: "Vencida",
  RECEBIDA: "Recebida",
  CONCILIADA: "Conciliada",
};

export function ReceivableStatusBadge({ status }: { status: ReceivableStatus }) {
  return <Badge variant={VARIANT_BY_STATUS[status]}>{LABEL_BY_STATUS[status]}</Badge>;
}

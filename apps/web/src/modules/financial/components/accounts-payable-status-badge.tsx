import { Badge } from "@gestorfrete/ui";
import type { PayableStatus } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<PayableStatus, "outline" | "warning" | "success" | "secondary" | "destructive"> = {
  LANCADA: "outline",
  AGUARDANDO_APROVACAO: "warning",
  APROVADA: "secondary",
  PAGA: "success",
  CONCILIADA: "success",
  REJEITADA: "destructive",
};

const LABEL_BY_STATUS: Record<PayableStatus, string> = {
  LANCADA: "Lançada",
  AGUARDANDO_APROVACAO: "Aguardando aprovação",
  APROVADA: "Aprovada",
  PAGA: "Paga",
  CONCILIADA: "Conciliada",
  REJEITADA: "Rejeitada",
};

export function AccountsPayableStatusBadge({ status }: { status: PayableStatus }) {
  return <Badge variant={VARIANT_BY_STATUS[status]}>{LABEL_BY_STATUS[status]}</Badge>;
}

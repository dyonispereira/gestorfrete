import { Badge } from "@gestorfrete/ui";
import type { ChecklistStatus } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<ChecklistStatus, "outline" | "secondary" | "warning" | "success" | "destructive"> = {
  PENDENTE: "outline",
  EM_PREENCHIMENTO: "secondary",
  CONCLUIDO: "warning",
  APROVADO: "success",
  REPROVADO: "destructive",
};

const LABEL_BY_STATUS: Record<ChecklistStatus, string> = {
  PENDENTE: "Pendente",
  EM_PREENCHIMENTO: "Em preenchimento",
  CONCLUIDO: "Concluído",
  APROVADO: "Aprovado",
  REPROVADO: "Reprovado",
};

export function ChecklistStatusBadge({ status }: { status: ChecklistStatus }) {
  return <Badge variant={VARIANT_BY_STATUS[status]}>{LABEL_BY_STATUS[status]}</Badge>;
}

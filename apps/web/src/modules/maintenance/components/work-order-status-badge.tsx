import { Badge } from "@gestorfrete/ui";
import type { WorkOrderStatus } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<WorkOrderStatus, "outline" | "secondary" | "warning" | "success" | "destructive"> = {
  ABERTA: "outline",
  EM_DIAGNOSTICO: "secondary",
  AGUARDANDO_APROVACAO: "warning",
  AGUARDANDO_PECA: "warning",
  EM_EXECUCAO: "secondary",
  CONCLUIDA: "success",
  FECHADA: "success",
  CANCELADA: "destructive",
};

const LABEL_BY_STATUS: Record<WorkOrderStatus, string> = {
  ABERTA: "Aberta",
  EM_DIAGNOSTICO: "Em diagnóstico",
  AGUARDANDO_APROVACAO: "Aguardando aprovação",
  AGUARDANDO_PECA: "Aguardando peça",
  EM_EXECUCAO: "Em execução",
  CONCLUIDA: "Concluída",
  FECHADA: "Fechada",
  CANCELADA: "Cancelada",
};

export function WorkOrderStatusBadge({ status }: { status: WorkOrderStatus }) {
  return <Badge variant={VARIANT_BY_STATUS[status]}>{LABEL_BY_STATUS[status]}</Badge>;
}

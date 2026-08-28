import { Badge } from "@gestorfrete/ui";
import type { CteStatus } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<CteStatus, "default" | "secondary" | "outline" | "success" | "warning" | "destructive"> = {
  RASCUNHO: "outline",
  VALIDADO: "secondary",
  ASSINADO: "secondary",
  TRANSMITIDO: "warning",
  AUTORIZADO: "success",
  CANCELADO: "destructive",
  DENEGADO: "destructive",
  INUTILIZADO: "secondary",
};

const LABEL_BY_STATUS: Record<CteStatus, string> = {
  RASCUNHO: "Rascunho",
  VALIDADO: "Validado",
  ASSINADO: "Assinado",
  TRANSMITIDO: "Transmitido",
  AUTORIZADO: "Autorizado",
  CANCELADO: "Cancelado",
  DENEGADO: "Denegado",
  INUTILIZADO: "Inutilizado",
};

export function CteStatusBadge({ status }: { status: CteStatus }) {
  return <Badge variant={VARIANT_BY_STATUS[status]}>{LABEL_BY_STATUS[status]}</Badge>;
}

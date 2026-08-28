import { Badge } from "@gestorfrete/ui";
import type { MdfeStatus } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<MdfeStatus, "outline" | "success" | "destructive"> = {
  PENDENTE: "outline",
  AUTORIZADO: "success",
  ENCERRADO: "success",
  CANCELADO: "destructive",
};

const LABEL_BY_STATUS: Record<MdfeStatus, string> = {
  PENDENTE: "Pendente",
  AUTORIZADO: "Autorizado",
  ENCERRADO: "Encerrado",
  CANCELADO: "Cancelado",
};

export function MdfeStatusBadge({ status }: { status: MdfeStatus }) {
  return <Badge variant={VARIANT_BY_STATUS[status]}>{LABEL_BY_STATUS[status]}</Badge>;
}

import { Badge } from "@gestorfrete/ui";
import type { ImplementAvailability } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<ImplementAvailability, "success" | "warning" | "secondary"> = {
  DISPONIVEL: "success",
  EM_USO: "warning",
  INATIVO: "secondary",
};

const LABEL_BY_STATUS: Record<ImplementAvailability, string> = {
  DISPONIVEL: "Disponível",
  EM_USO: "Em uso",
  INATIVO: "Inativo",
};

export function ImplementStatusBadge({ status }: { status: ImplementAvailability }) {
  return <Badge variant={VARIANT_BY_STATUS[status]}>{LABEL_BY_STATUS[status]}</Badge>;
}

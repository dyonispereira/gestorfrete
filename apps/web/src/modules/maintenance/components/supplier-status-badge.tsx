import { Badge } from "@gestorfrete/ui";
import type { SupplierStatus } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<SupplierStatus, "success" | "secondary"> = {
  ATIVO: "success",
  INATIVO: "secondary",
};

const LABEL_BY_STATUS: Record<SupplierStatus, string> = {
  ATIVO: "Ativo",
  INATIVO: "Inativo",
};

export function SupplierStatusBadge({ status }: { status: SupplierStatus }) {
  return <Badge variant={VARIANT_BY_STATUS[status]}>{LABEL_BY_STATUS[status]}</Badge>;
}

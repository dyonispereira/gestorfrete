import { Badge } from "@gestorfrete/ui";
import type { PriceTableStatus } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<PriceTableStatus, "secondary" | "success" | "destructive"> = {
  RASCUNHO: "secondary", VIGENTE: "success", EXPIRADA: "destructive",
};
const LABEL_BY_STATUS: Record<PriceTableStatus, string> = {
  RASCUNHO: "Rascunho", VIGENTE: "Vigente", EXPIRADA: "Expirada",
};

export function PriceTableStatusBadge({ status }: { status: PriceTableStatus }) {
  return <Badge variant={VARIANT_BY_STATUS[status]}>{LABEL_BY_STATUS[status]}</Badge>;
}

import { Badge } from "@gestorfrete/ui";
import type { InvoiceStatus } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<InvoiceStatus, "success" | "destructive"> = { EMITIDA: "success", CANCELADA: "destructive" };
const LABEL_BY_STATUS: Record<InvoiceStatus, string> = { EMITIDA: "Emitida", CANCELADA: "Cancelada" };

export function InvoiceStatusBadge({ status }: { status: InvoiceStatus }) {
  return <Badge variant={VARIANT_BY_STATUS[status]}>{LABEL_BY_STATUS[status]}</Badge>;
}

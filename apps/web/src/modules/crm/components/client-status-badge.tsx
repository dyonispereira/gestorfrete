import { Badge } from "@gestorfrete/ui";
import type { ClientStatus } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<ClientStatus, "success" | "secondary"> = {
  ATIVO: "success",
  INATIVO: "secondary",
};

const LABEL_BY_STATUS: Record<ClientStatus, string> = {
  ATIVO: "Ativo",
  INATIVO: "Inativo",
};

export function ClientStatusBadge({ status }: { status: ClientStatus }) {
  return <Badge variant={VARIANT_BY_STATUS[status]}>{LABEL_BY_STATUS[status]}</Badge>;
}

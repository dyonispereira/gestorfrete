import { Badge } from "@gestorfrete/ui";
import type { UserStatus } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<UserStatus, "success" | "secondary" | "destructive"> = {
  ATIVO: "success",
  INATIVO: "secondary",
  BLOQUEADO: "destructive",
};

const LABEL_BY_STATUS: Record<UserStatus, string> = {
  ATIVO: "Ativo",
  INATIVO: "Inativo",
  BLOQUEADO: "Bloqueado",
};

export function UserStatusBadge({ status }: { status: UserStatus }) {
  return <Badge variant={VARIANT_BY_STATUS[status]}>{LABEL_BY_STATUS[status]}</Badge>;
}

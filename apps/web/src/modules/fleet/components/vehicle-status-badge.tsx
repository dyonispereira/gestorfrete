import { Badge } from "@gestorfrete/ui";
import type { VehicleStatus } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<VehicleStatus, "success" | "secondary"> = { ATIVO: "success", INATIVO: "secondary" };
const LABEL_BY_STATUS: Record<VehicleStatus, string> = { ATIVO: "Ativo", INATIVO: "Inativo" };

export function VehicleStatusBadge({ status }: { status: VehicleStatus }) {
  return <Badge variant={VARIANT_BY_STATUS[status]}>{LABEL_BY_STATUS[status]}</Badge>;
}

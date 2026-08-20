import { Badge } from "@gestorfrete/ui";
import type { DriverFitnessStatus } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<DriverFitnessStatus, "success" | "destructive"> = {
  APTO: "success",
  BLOQUEADO: "destructive",
};

const LABEL_BY_STATUS: Record<DriverFitnessStatus, string> = {
  APTO: "Apto",
  BLOQUEADO: "Bloqueado",
};

/** `fitness_status` is computed by `block()`/`unblock()` — this badge is always read-only. */
export function DriverStatusBadge({ status }: { status: DriverFitnessStatus }) {
  return <Badge variant={VARIANT_BY_STATUS[status]}>{LABEL_BY_STATUS[status]}</Badge>;
}

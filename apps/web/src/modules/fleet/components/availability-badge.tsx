import { Badge, Skeleton } from "@gestorfrete/ui";
import type { AvailabilityStatus } from "@gestorfrete/types";

import { useVehicleAvailabilityQuery } from "@/modules/fleet/hooks/use-vehicle-availability";

const VARIANT_BY_STATUS: Record<AvailabilityStatus, "success" | "warning" | "secondary" | "destructive"> = {
  DISPONIVEL: "success",
  EM_VIAGEM: "warning",
  EM_MANUTENCAO: "warning",
  INATIVO: "secondary",
};

const LABEL_BY_STATUS: Record<AvailabilityStatus, string> = {
  DISPONIVEL: "Disponível",
  EM_VIAGEM: "Em viagem",
  EM_MANUTENCAO: "Em manutenção",
  INATIVO: "Inativo",
};

/**
 * Read model only — never a click target, never an "alterar disponibilidade" affordance anywhere.
 * The projector behind this isn't wired to real trip/maintenance events yet in this environment
 * (Lote Frota audit) — shown as real API data regardless, not hidden.
 */
export function AvailabilityBadge({ vehicleId }: { vehicleId: string }) {
  const availabilityQuery = useVehicleAvailabilityQuery(vehicleId);

  if (availabilityQuery.isLoading) return <Skeleton className="h-5 w-24" />;
  if (availabilityQuery.error || !availabilityQuery.data) return <Badge variant="outline">—</Badge>;

  const status = availabilityQuery.data.status;
  return <Badge variant={VARIANT_BY_STATUS[status]}>{LABEL_BY_STATUS[status]}</Badge>;
}

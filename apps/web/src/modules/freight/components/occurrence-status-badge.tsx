import { Badge } from "@gestorfrete/ui";
import type { OccurrenceSeverity, OccurrenceStatus } from "@gestorfrete/types";

const STATUS_VARIANT: Record<OccurrenceStatus, "warning" | "success"> = { ABERTA: "warning", RESOLVIDA: "success" };
const STATUS_LABEL: Record<OccurrenceStatus, string> = { ABERTA: "Aberta", RESOLVIDA: "Resolvida" };

export function OccurrenceStatusBadge({ status }: { status: OccurrenceStatus }) {
  return <Badge variant={STATUS_VARIANT[status]}>{STATUS_LABEL[status]}</Badge>;
}

const SEVERITY_VARIANT: Record<OccurrenceSeverity, "secondary" | "warning" | "destructive"> = {
  BAIXA: "secondary",
  MEDIA: "warning",
  ALTA: "warning",
  CRITICA: "destructive",
};
const SEVERITY_LABEL: Record<OccurrenceSeverity, string> = { BAIXA: "Baixa", MEDIA: "Média", ALTA: "Alta", CRITICA: "Crítica" };

export function OccurrenceSeverityBadge({ severity }: { severity: OccurrenceSeverity }) {
  return <Badge variant={SEVERITY_VARIANT[severity]}>{SEVERITY_LABEL[severity]}</Badge>;
}

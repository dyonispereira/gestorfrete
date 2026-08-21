import { Badge } from "@gestorfrete/ui";
import type { TripFinancialStatus, TripFiscalStatus, TripOperationalStatus, TripStatus } from "@gestorfrete/types";

type BadgeVariant = "default" | "secondary" | "outline" | "success" | "warning" | "destructive";

const OPERATIONAL_VARIANT: Record<TripOperationalStatus, BadgeVariant> = {
  RASCUNHO: "outline",
  PLANEJADA: "secondary",
  AGUARDANDO_CHECKLIST: "warning",
  LIBERADA: "secondary",
  EM_DESLOCAMENTO: "default",
  CARREGANDO: "default",
  EM_TRANSITO: "default",
  EM_ENTREGA: "default",
  FINALIZADA: "success",
  INTERROMPIDA: "destructive",
  CANCELADA: "destructive",
};

const OPERATIONAL_LABEL: Record<TripOperationalStatus, string> = {
  RASCUNHO: "Rascunho",
  PLANEJADA: "Planejada",
  AGUARDANDO_CHECKLIST: "Aguardando checklist",
  LIBERADA: "Liberada",
  EM_DESLOCAMENTO: "Em deslocamento",
  CARREGANDO: "Carregando",
  EM_TRANSITO: "Em trânsito",
  EM_ENTREGA: "Em entrega",
  FINALIZADA: "Finalizada",
  INTERROMPIDA: "Interrompida",
  CANCELADA: "Cancelada",
};

const FISCAL_VARIANT: Record<TripFiscalStatus, BadgeVariant> = {
  PENDENTE: "outline",
  CTE_EMITIDO: "secondary",
  MDFE_EMITIDO: "secondary",
  MDFE_ENCERRADO: "success",
  CTE_CANCELADO: "destructive",
};

const FISCAL_LABEL: Record<TripFiscalStatus, string> = {
  PENDENTE: "Fiscal: pendente",
  CTE_EMITIDO: "CT-e emitido",
  MDFE_EMITIDO: "MDF-e emitido",
  MDFE_ENCERRADO: "MDF-e encerrado",
  CTE_CANCELADO: "CT-e cancelado",
};

const FINANCIAL_VARIANT: Record<TripFinancialStatus, BadgeVariant> = {
  AGUARDANDO_FATURAMENTO: "outline",
  FATURADA: "secondary",
  AGUARDANDO_RECEBIMENTO: "warning",
  RECEBIDA: "success",
};

const FINANCIAL_LABEL: Record<TripFinancialStatus, string> = {
  AGUARDANDO_FATURAMENTO: "Aguardando faturamento",
  FATURADA: "Faturada",
  AGUARDANDO_RECEBIMENTO: "Aguardando recebimento",
  RECEBIDA: "Recebida",
};

/**
 * Três dimensões independentes (D020) — nunca resumidas em um único badge. `closed`/`encerrada`
 * é derivado pelo Postgres (D019) e nunca setado por comando algum; mostrado como um selo à parte,
 * nunca como parte da dimensão Operacional.
 */
export function TripStatusBadges({ status }: { status: TripStatus }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge variant={OPERATIONAL_VARIANT[status.operational]}>{OPERATIONAL_LABEL[status.operational]}</Badge>
      <Badge variant={FISCAL_VARIANT[status.fiscal]}>{FISCAL_LABEL[status.fiscal]}</Badge>
      <Badge variant={FINANCIAL_VARIANT[status.financial]}>{FINANCIAL_LABEL[status.financial]}</Badge>
      {status.closed ? <Badge variant="success">Encerrada</Badge> : null}
    </div>
  );
}

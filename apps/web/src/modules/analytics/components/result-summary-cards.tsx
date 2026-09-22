import { Card, CardContent, CardHeader, CardTitle } from "@gestorfrete/ui";
import type { ResultTotals } from "@gestorfrete/types";

import { formatKm, formatMoney, formatPercent } from "@/modules/analytics/lib/format";

/** Topo do painel (pedido explícito do usuário): Receita Realizada | Custo Realizado | Resultado |
 * Margem % | Viagens | KM. `km` fica "Indisponível" quando não há dado — nunca 0 fabricado (gap
 * registrado em docs/domain/012-resultado-gerencial.md). */
export function ResultSummaryCards({ totals }: { totals: ResultTotals }) {
  const cards = [
    { label: "Receita Realizada", value: formatMoney(totals.realized_revenue) },
    { label: "Custo Realizado", value: formatMoney(totals.realized_cost) },
    {
      label: "Resultado",
      value: formatMoney(totals.realized_margin),
      negative: Number(totals.realized_margin) < 0,
    },
    { label: "Margem %", value: formatPercent(totals.realized_margin_pct) },
    { label: "Viagens", value: String(totals.trips) },
    { label: "KM rodado", value: formatKm(totals.km) },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {cards.map((card) => (
        <Card key={card.label}>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">{card.label}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className={`text-lg font-semibold ${card.negative ? "text-destructive" : "text-foreground"}`}>
              {card.value}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

"use client";

import Link from "next/link";
import { MapPin } from "lucide-react";

import { Badge, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { InvoiceTrip } from "@gestorfrete/types";

import { useTripQuery } from "@/modules/freight/hooks/use-trips";
import { useDeliveriesQuery } from "@/modules/freight/hooks/use-deliveries";
import { useCtesQuery } from "@/modules/documents/hooks/use-ctes";
import { CteStatusBadge } from "@/modules/documents/components/cte-status-badge";

function formatMoney(value: string): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function addressLabel(address: Record<string, unknown> | undefined): string {
  if (!address) return "—";
  const cidade = typeof address.cidade === "string" ? address.cidade : undefined;
  const uf = typeof address.uf === "string" ? address.uf : undefined;
  if (cidade && uf) return `${cidade}/${uf}`;
  return cidade ?? uf ?? "—";
}

/**
 * Fatura → Item → Viagem → Entrega → CT-e (pedido explícito do usuário) — cada linha resolve a
 * Viagem, suas Entregas (para origem/destino) e seu CT-e via navegação real a partir de
 * `viagem_id`, nunca um FK direto no item para Entrega/CT-e (D008: financial não vira proprietária
 * de fato fiscal — `InvoiceTrip` só guarda `viagem_id`+`valor`).
 */
function InvoiceTripRow({ invoiceTrip }: { invoiceTrip: InvoiceTrip }) {
  const tripQuery = useTripQuery(invoiceTrip.trip_id);
  const deliveriesQuery = useDeliveriesQuery(invoiceTrip.trip_id);
  const ctesQuery = useCtesQuery({ trip_id: invoiceTrip.trip_id, limit: 5 });

  const deliveries = deliveriesQuery.data?.data ?? [];
  const cte = ctesQuery.data?.data[0];

  return (
    <TableRow>
      <TableCell className="font-medium">
        <Link href={`/viagens/${invoiceTrip.trip_id}`} className="text-primary hover:underline">
          {tripQuery.data?.codigo ?? invoiceTrip.trip_id}
        </Link>
      </TableCell>
      <TableCell className="text-muted-foreground">
        {tripQuery.data?.scheduled_date ? new Date(tripQuery.data.scheduled_date).toLocaleDateString("pt-BR") : "—"}
      </TableCell>
      <TableCell className="text-muted-foreground">
        <div className="flex items-center gap-1.5">
          <MapPin className="h-3.5 w-3.5" />
          {deliveries.length > 0
            ? `${addressLabel(deliveries[0]?.delivery_address)}${deliveries.length > 1 ? ` (+${deliveries.length - 1})` : ""}`
            : "—"}
        </div>
      </TableCell>
      <TableCell>
        {cte ? (
          <Link href={`/ctes/${cte.id}`} className="flex items-center gap-2 text-primary hover:underline">
            {cte.number}/{cte.series}
            <CteStatusBadge status={cte.status} />
          </Link>
        ) : (
          <Badge variant="outline">Sem CT-e</Badge>
        )}
      </TableCell>
      <TableCell className="text-right font-medium">{formatMoney(invoiceTrip.value)}</TableCell>
    </TableRow>
  );
}

export function InvoiceTripsTab({ trips }: { trips: InvoiceTrip[] }) {
  if (trips.length === 0) {
    return <p className="text-sm text-muted-foreground">Fatura por Entrega — sem Viagens itemizadas.</p>;
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Viagem</TableHead>
          <TableHead>Data</TableHead>
          <TableHead>Entrega</TableHead>
          <TableHead>CT-e</TableHead>
          <TableHead className="text-right">Valor</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {trips.map((invoiceTrip) => (
          <InvoiceTripRow key={invoiceTrip.id} invoiceTrip={invoiceTrip} />
        ))}
      </TableBody>
    </Table>
  );
}

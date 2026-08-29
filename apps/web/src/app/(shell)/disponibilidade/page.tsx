"use client";

import * as React from "react";
import Link from "next/link";

import { Badge, Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { AvailabilityStatus } from "@gestorfrete/types";

import { useVehicleAvailabilityListQuery } from "@/modules/fleet/hooks/use-vehicle-availability";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const VARIANT_BY_STATUS: Record<AvailabilityStatus, "success" | "warning" | "secondary"> = {
  DISPONIVEL: "success",
  EM_VIAGEM: "warning",
  EM_MANUTENCAO: "warning",
  INATIVO: "secondary",
};

const STATUS_OPTIONS: Array<{ value: "all" | AvailabilityStatus; label: string }> = [
  { value: "all", label: "Todos os status" },
  { value: "DISPONIVEL", label: "Disponível" },
  { value: "EM_VIAGEM", label: "Em viagem" },
  { value: "EM_MANUTENCAO", label: "Em manutenção" },
  { value: "INATIVO", label: "Inativo" },
];

const LABEL_BY_STATUS: Record<AvailabilityStatus, string> = {
  DISPONIVEL: "Disponível",
  EM_VIAGEM: "Em viagem",
  EM_MANUTENCAO: "Em manutenção",
  INATIVO: "Inativo",
};

/**
 * Read model puro — nenhuma ação nesta tela, de propósito. Não existe endpoint de escrita para
 * Disponibilidade em lugar nenhum do Backend. O lado de `maintenance` do projetor (`EM_MANUTENCAO`
 * ↔ `DISPONIVEL` em OS aberta/concluída/cancelada) está conectado desde a Lote Frota e Manutenção,
 * Parte 2; o lado de `freight` (`EM_VIAGEM` no despacho) ainda não está — gap real, não escondido.
 */
export default function VehicleAvailabilityPage() {
  const [page, setPage] = React.useState(1);
  const [status, setStatus] = React.useState<"all" | AvailabilityStatus>("all");

  const availabilityQuery = useVehicleAvailabilityListQuery({ page, limit: 20, status: status === "all" ? undefined : status });

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Disponibilidade</h1>
        <p className="text-sm text-muted-foreground">
          Consulta somente leitura — a disponibilidade é calculada pelo sistema, nunca alterada manualmente aqui.
        </p>
      </div>

      <Select
        value={status}
        onValueChange={(value) => {
          setStatus(value as "all" | AvailabilityStatus);
          setPage(1);
        }}
      >
        <SelectTrigger className="sm:w-48">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {STATUS_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {availabilityQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : availabilityQuery.error ? (
        <ErrorState
          title="Não foi possível carregar a disponibilidade"
          description={availabilityQuery.error instanceof Error ? availabilityQuery.error.message : undefined}
          onRetry={() => availabilityQuery.refetch()}
        />
      ) : availabilityQuery.data && availabilityQuery.data.data.length > 0 ? (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Veículo</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Atualizado em</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {availabilityQuery.data.data.map((row) => (
                <TableRow key={row.vehicle_id}>
                  <TableCell className="font-mono text-xs">
                    <Link href={`/veiculos/${row.vehicle_id}`} className="text-muted-foreground hover:text-foreground hover:underline">
                      {row.vehicle_id}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Badge variant={VARIANT_BY_STATUS[row.status]}>{LABEL_BY_STATUS[row.status]}</Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{new Date(row.updated_at).toLocaleString("pt-BR")}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <Pagination
            page={availabilityQuery.data.meta.pagination.page}
            limit={availabilityQuery.data.meta.pagination.limit}
            total={availabilityQuery.data.meta.pagination.total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState title="Nenhum dado de disponibilidade ainda" description="A frota ainda não gerou nenhum evento de disponibilidade." />
      )}
    </div>
  );
}

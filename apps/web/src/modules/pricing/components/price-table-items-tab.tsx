"use client";

import * as React from "react";
import { Plus, Trash2 } from "lucide-react";

import { Button, Table, TableBody, TableCell, TableHead, TableHeader, TableRow, toast } from "@gestorfrete/ui";
import type { PriceTableStatus, PriceTableUnit } from "@gestorfrete/types";

import { useDeletePriceTableItemMutation, usePriceTableItemsQuery } from "@/modules/pricing/hooks/use-price-tables";
import { PriceTableItemFormDrawer } from "@/modules/pricing/components/price-table-item-form-drawer";
import { ApiError } from "@/shared/lib/api-client";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const UNIT_LABEL: Record<PriceTableUnit, string> = {
  VIAGEM: "Por viagem", KM: "Por km", TONELADA: "Por tonelada", KG: "Por kg",
  FAIXA_DISTANCIA: "Faixa de distância", PERCENTUAL: "Percentual",
};

function formatMoney(value: string | undefined): string {
  if (value === undefined) return "—";
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

interface PriceTableItemsTabProps {
  priceTableId: string;
  tableStatus: PriceTableStatus;
  canEdit: boolean;
}

export function PriceTableItemsTab({ priceTableId, tableStatus, canEdit }: PriceTableItemsTabProps) {
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const itemsQuery = usePriceTableItemsQuery(priceTableId);
  const deleteItem = useDeletePriceTableItemMutation(priceTableId);

  const canMutateItems = canEdit && tableStatus === "RASCUNHO";

  async function handleDelete(itemId: string) {
    try {
      await deleteItem.mutateAsync(itemId);
      toast.success("Item removido.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível remover o item.");
    }
  }

  if (itemsQuery.isLoading) return <LoadingState rows={3} />;
  if (itemsQuery.error)
    return (
      <ErrorState
        title="Não foi possível carregar os itens"
        description={itemsQuery.error instanceof Error ? itemsQuery.error.message : undefined}
        onRetry={() => itemsQuery.refetch()}
      />
    );

  const items = itemsQuery.data ?? [];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {tableStatus === "RASCUNHO"
            ? "Itens editáveis enquanto a tabela estiver em rascunho."
            : "Tabela já ativada — itens não podem mais ser alterados."}
        </p>
        {canMutateItems ? (
          <Button size="sm" onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Novo item
          </Button>
        ) : null}
      </div>

      {items.length === 0 ? (
        <EmptyState title="Nenhum item cadastrado" description="Adicione ao menos 1 item para poder ativar a tabela." />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Unidade</TableHead>
              <TableHead>Categoria</TableHead>
              <TableHead>Valor</TableHead>
              <TableHead>Mínimo</TableHead>
              <TableHead>Ajustes</TableHead>
              {canMutateItems ? <TableHead /> : null}
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) => (
              <TableRow key={item.id}>
                <TableCell>
                  {UNIT_LABEL[item.unidade_calculo]}
                  {item.unidade_calculo === "FAIXA_DISTANCIA" ? (
                    <span className="block text-xs text-muted-foreground">
                      {item.faixa_distancia_min_km}–{item.faixa_distancia_max_km} km (
                      {item.faixa_modo === "TARIFA_POR_KM" ? "tarifa/km" : "valor fixo"})
                    </span>
                  ) : null}
                  {item.unidade_calculo === "PERCENTUAL" ? (
                    <span className="block text-xs text-muted-foreground">{item.base_percentual_descricao}</span>
                  ) : null}
                </TableCell>
                <TableCell className="text-muted-foreground">{item.categoria_veiculo_id ? "Específica" : "Qualquer"}</TableCell>
                <TableCell className="font-medium">
                  {item.unidade_calculo === "PERCENTUAL" ? `${item.valor}%` : formatMoney(item.valor)}
                </TableCell>
                <TableCell className="text-muted-foreground">{formatMoney(item.valor_minimo)}</TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {[
                    item.adicional_fixo ? `+${formatMoney(item.adicional_fixo)}` : null,
                    item.desconto_fixo ? `-${formatMoney(item.desconto_fixo)}` : null,
                    item.adicional_percentual ? `+${item.adicional_percentual}%` : null,
                    item.desconto_percentual ? `-${item.desconto_percentual}%` : null,
                  ]
                    .filter(Boolean)
                    .join(" · ") || "—"}
                </TableCell>
                {canMutateItems ? (
                  <TableCell>
                    <Button size="icon" variant="ghost" onClick={() => handleDelete(item.id)} disabled={deleteItem.isPending}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                ) : null}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <PriceTableItemFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} priceTableId={priceTableId} />
    </div>
  );
}

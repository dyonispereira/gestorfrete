"use client";

import * as React from "react";
import { Package, Plus } from "lucide-react";

import {
  Button,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  toast,
} from "@gestorfrete/ui";
import type { WorkOrderItemCostCategory } from "@gestorfrete/types";

import { useCreateWorkOrderItemMutation, useWorkOrderItemsQuery } from "@/modules/maintenance/hooks/use-work-order-items";
import { ApiError } from "@/shared/lib/api-client";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const CATEGORY_LABEL: Record<WorkOrderItemCostCategory, string> = {
  PECAS: "Peças",
  PNEUS: "Pneus",
  SERVICOS: "Serviços",
  TERCEIROS: "Terceiros",
  MAO_DE_OBRA_INTERNA: "Mão de obra interna",
  MAO_DE_OBRA_TERCEIRIZADA: "Mão de obra terceirizada",
  DESLOCAMENTO: "Deslocamento",
  OUTROS: "Outros",
};

function formatMoney(value: string): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

interface WorkOrderItemsTabProps {
  workOrderId: string;
  canCreate: boolean;
}

/** `valor_total` é `GENERATED` no Backend — nunca digitado, só quantidade × valor unitário
 * refletidos aqui. `custo_previsto`/`custo_realizado` da OS (não mostrados nesta aba, na Visão
 * Geral) são recalculados pelo Backend a cada item — nunca editáveis diretamente. */
export function WorkOrderItemsTab({ workOrderId, canCreate }: WorkOrderItemsTabProps) {
  const itemsQuery = useWorkOrderItemsQuery(workOrderId);
  const createItem = useCreateWorkOrderItemMutation(workOrderId);

  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [costCategory, setCostCategory] = React.useState<WorkOrderItemCostCategory>("PECAS");
  const [description, setDescription] = React.useState("");
  const [quantity, setQuantity] = React.useState("");
  const [unitValue, setUnitValue] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createItem.mutateAsync({
        cost_category: costCategory, description, quantity, unit_value: unitValue,
      });
      toast.success("Item adicionado.");
      setDescription("");
      setQuantity("");
      setUnitValue("");
      setDrawerOpen(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível adicionar o item.");
    }
  }

  if (itemsQuery.isLoading) return <LoadingState rows={3} />;
  if (itemsQuery.error)
    return <ErrorState description="Não foi possível carregar os itens." onRetry={() => itemsQuery.refetch()} />;

  const items = itemsQuery.data?.data ?? [];

  const subtotalsByCategory = new Map<WorkOrderItemCostCategory, number>();
  for (const item of items) {
    subtotalsByCategory.set(item.cost_category, (subtotalsByCategory.get(item.cost_category) ?? 0) + Number(item.total_value));
  }
  const grandTotal = [...subtotalsByCategory.values()].reduce((sum, value) => sum + value, 0);

  return (
    <div className="flex flex-col gap-4">
      {canCreate ? (
        <div className="flex justify-end">
          <Button size="sm" onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Novo item
          </Button>
        </div>
      ) : null}

      {items.length === 0 ? (
        <EmptyState icon={Package} title="Nenhum item registrado ainda" />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Categoria</TableHead>
              <TableHead>Descrição</TableHead>
              <TableHead>Qtd.</TableHead>
              <TableHead>Valor unitário</TableHead>
              <TableHead>Total</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) => (
              <TableRow key={item.id}>
                <TableCell className="text-muted-foreground">{CATEGORY_LABEL[item.cost_category]}</TableCell>
                <TableCell>{item.description}</TableCell>
                <TableCell>{item.quantity}</TableCell>
                <TableCell>{formatMoney(item.unit_value)}</TableCell>
                <TableCell className="font-medium">{formatMoney(item.total_value)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {items.length > 0 ? (
        <div className="flex flex-col gap-1 rounded-md border border-border p-4 text-sm">
          {[...subtotalsByCategory.entries()].map(([category, subtotal]) => (
            <div key={category} className="flex items-center justify-between gap-2 text-muted-foreground">
              <span>{CATEGORY_LABEL[category]}</span>
              <span>{formatMoney(subtotal.toFixed(2))}</span>
            </div>
          ))}
          <div className="mt-1 flex items-center justify-between gap-2 border-t border-border pt-2 font-medium">
            <span>Custo total (sempre derivado dos itens)</span>
            <span>{formatMoney(grandTotal.toFixed(2))}</span>
          </div>
        </div>
      ) : null}

      <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
        <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Novo item</SheetTitle>
            <SheetDescription>Bloqueado depois de Concluída/Fechada/Cancelada.</SheetDescription>
          </SheetHeader>
          <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="work-order-item-category">Categoria</Label>
              <Select value={costCategory} onValueChange={(value) => setCostCategory(value as WorkOrderItemCostCategory)}>
                <SelectTrigger id="work-order-item-category">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(Object.keys(CATEGORY_LABEL) as WorkOrderItemCostCategory[]).map((value) => (
                    <SelectItem key={value} value={value}>
                      {CATEGORY_LABEL[value]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="work-order-item-description">Descrição</Label>
              <Input id="work-order-item-description" required value={description} onChange={(event) => setDescription(event.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="work-order-item-quantity">Quantidade</Label>
                <Input id="work-order-item-quantity" type="number" step="0.01" required value={quantity} onChange={(event) => setQuantity(event.target.value)} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="work-order-item-unit-value">Valor unitário</Label>
                <Input id="work-order-item-unit-value" type="number" step="0.01" required value={unitValue} onChange={(event) => setUnitValue(event.target.value)} />
              </div>
            </div>

            {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

            <div className="mt-auto flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setDrawerOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createItem.isPending}>
                {createItem.isPending ? "Adicionando…" : "Adicionar item"}
              </Button>
            </div>
          </form>
        </SheetContent>
      </Sheet>
    </div>
  );
}

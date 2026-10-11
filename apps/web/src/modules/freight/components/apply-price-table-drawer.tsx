"use client";

import * as React from "react";

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
  toast,
} from "@gestorfrete/ui";

import { usePriceTableItemsQuery, usePriceTablesQuery } from "@/modules/pricing/hooks/use-price-tables";
import { useApplyPriceTableMutation } from "@/modules/freight/hooks/use-trips";
import { ApiError } from "@/shared/lib/api-client";

interface ApplyPriceTableDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tripId: string;
}

/** Só lista tabelas VIGENTE de VENDA — COMPRA fica bloqueada no backend sem Transportador (Lote 5,
 * ainda não implementado), então nem é oferecida aqui para não levar a um erro certo. */
export function ApplyPriceTableDrawer({ open, onOpenChange, tripId }: ApplyPriceTableDrawerProps) {
  const [priceTableId, setPriceTableId] = React.useState("");
  const [itemId, setItemId] = React.useState("");
  const [basePercentualValor, setBasePercentualValor] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const tablesQuery = usePriceTablesQuery({ direcao: "VENDA", status: "VIGENTE", limit: 100 });
  const itemsQuery = usePriceTableItemsQuery(priceTableId || undefined);
  const applyPriceTable = useApplyPriceTableMutation();

  const selectedItem = itemsQuery.data?.find((item) => item.id === itemId);

  function reset() {
    setPriceTableId(""); setItemId(""); setBasePercentualValor(""); setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await applyPriceTable.mutateAsync({
        tripId,
        variables: {
          price_table_item_id: itemId,
          base_percentual_valor: selectedItem?.unidade_calculo === "PERCENTUAL" ? basePercentualValor : undefined,
        },
      });
      toast.success("Tabela de frete aplicada.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível aplicar a tabela de frete.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Aplicar tabela de frete</SheetTitle>
          <SheetDescription>O valor é calculado e congelado na Viagem — remover depois exige nenhum CT-e já emitido.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="apply-price-table">Tabela de frete (venda, vigente)</Label>
            <Select value={priceTableId} onValueChange={(value) => { setPriceTableId(value); setItemId(""); }}>
              <SelectTrigger id="apply-price-table">
                <SelectValue placeholder="Selecione uma tabela" />
              </SelectTrigger>
              <SelectContent>
                {tablesQuery.data?.data.map((table) => (
                  <SelectItem key={table.id} value={table.id}>
                    {table.nome}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {tablesQuery.data?.data.length === 0 ? (
              <p className="text-xs text-muted-foreground">Nenhuma tabela de venda vigente — crie e ative uma em Comercial → Tabelas de Frete.</p>
            ) : null}
          </div>

          {priceTableId ? (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="apply-price-table-item">Item</Label>
              <Select value={itemId} onValueChange={setItemId}>
                <SelectTrigger id="apply-price-table-item">
                  <SelectValue placeholder="Selecione um item" />
                </SelectTrigger>
                <SelectContent>
                  {itemsQuery.data?.map((item) => (
                    <SelectItem key={item.id} value={item.id}>
                      {item.unidade_calculo} — {item.unidade_calculo === "PERCENTUAL" ? `${item.valor}%` : item.valor}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ) : null}

          {selectedItem?.unidade_calculo === "PERCENTUAL" ? (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="apply-base-percentual">
                Base do percentual ({selectedItem.base_percentual_descricao})
              </Label>
              <Input
                id="apply-base-percentual" required type="number" step="0.01" value={basePercentualValor}
                onChange={(event) => setBasePercentualValor(event.target.value)}
              />
            </div>
          ) : null}

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={applyPriceTable.isPending || !itemId}>
              {applyPriceTable.isPending ? "Aplicando…" : "Aplicar"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

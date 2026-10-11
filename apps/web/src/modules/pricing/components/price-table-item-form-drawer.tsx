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
import type { FaixaDistanciaMode, PriceTableUnit } from "@gestorfrete/types";

import { useVehicleCategoriesQuery } from "@/modules/fleet/hooks/use-vehicle-categories";
import { useCreatePriceTableItemMutation } from "@/modules/pricing/hooks/use-price-tables";
import { ApiError } from "@/shared/lib/api-client";

const UNIT_LABEL: Record<PriceTableUnit, string> = {
  VIAGEM: "Valor fixo por viagem", KM: "Valor por km", TONELADA: "Valor por tonelada",
  KG: "Valor por kg", FAIXA_DISTANCIA: "Faixa de distância", PERCENTUAL: "Percentual sobre base",
};

interface PriceTableItemFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  priceTableId: string;
}

/** Campos condicionais por `unidade_calculo` — mesma regra validada no backend (achado real:
 * PERCENTUAL exige `base_percentual_descricao` aqui, e `base_percentual_valor` só depois, no
 * momento da aplicação na Viagem — nunca uma base inventada neste formulário). */
export function PriceTableItemFormDrawer({ open, onOpenChange, priceTableId }: PriceTableItemFormDrawerProps) {
  const [unidade, setUnidade] = React.useState<PriceTableUnit>("VIAGEM");
  const [categoriaVeiculoId, setCategoriaVeiculoId] = React.useState("");
  const [faixaMin, setFaixaMin] = React.useState("");
  const [faixaMax, setFaixaMax] = React.useState("");
  const [faixaModo, setFaixaModo] = React.useState<FaixaDistanciaMode>("TARIFA_POR_KM");
  const [valor, setValor] = React.useState("");
  const [valorMinimo, setValorMinimo] = React.useState("");
  const [adicionalFixo, setAdicionalFixo] = React.useState("");
  const [descontoFixo, setDescontoFixo] = React.useState("");
  const [adicionalPercentual, setAdicionalPercentual] = React.useState("");
  const [descontoPercentual, setDescontoPercentual] = React.useState("");
  const [basePercentualDescricao, setBasePercentualDescricao] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const categoriesQuery = useVehicleCategoriesQuery({ limit: 100 });
  const createItem = useCreatePriceTableItemMutation(priceTableId);

  function reset() {
    setUnidade("VIAGEM"); setCategoriaVeiculoId(""); setFaixaMin(""); setFaixaMax("");
    setFaixaModo("TARIFA_POR_KM"); setValor(""); setValorMinimo(""); setAdicionalFixo("");
    setDescontoFixo(""); setAdicionalPercentual(""); setDescontoPercentual("");
    setBasePercentualDescricao(""); setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createItem.mutateAsync({
        unidade_calculo: unidade,
        categoria_veiculo_id: categoriaVeiculoId || undefined,
        faixa_distancia_min_km: unidade === "FAIXA_DISTANCIA" ? faixaMin : undefined,
        faixa_distancia_max_km: unidade === "FAIXA_DISTANCIA" ? faixaMax : undefined,
        faixa_modo: unidade === "FAIXA_DISTANCIA" ? faixaModo : undefined,
        valor,
        valor_minimo: valorMinimo || undefined,
        adicional_fixo: adicionalFixo || undefined,
        desconto_fixo: descontoFixo || undefined,
        adicional_percentual: adicionalPercentual || undefined,
        desconto_percentual: descontoPercentual || undefined,
        base_percentual_descricao: unidade === "PERCENTUAL" ? basePercentualDescricao : undefined,
      });
      toast.success("Item adicionado.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível adicionar o item.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 sm:max-w-md overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Novo item</SheetTitle>
          <SheetDescription>Critério de cálculo + valor — só pode ser criado enquanto a tabela está em rascunho.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="item-unidade-calculo">Unidade de cálculo</Label>
            <Select value={unidade} onValueChange={(value) => setUnidade(value as PriceTableUnit)}>
              <SelectTrigger id="item-unidade-calculo">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(UNIT_LABEL) as PriceTableUnit[]).map((unit) => (
                  <SelectItem key={unit} value={unit}>
                    {UNIT_LABEL[unit]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="item-categoria-veiculo">Categoria de veículo (opcional — vazio aplica a qualquer categoria)</Label>
            <Select value={categoriaVeiculoId || "none"} onValueChange={(value) => setCategoriaVeiculoId(value === "none" ? "" : value)}>
              <SelectTrigger id="item-categoria-veiculo">
                <SelectValue placeholder="Qualquer categoria" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Qualquer categoria</SelectItem>
                {categoriesQuery.data?.data.map((category) => (
                  <SelectItem key={category.id} value={category.id}>
                    {category.nome}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {unidade === "FAIXA_DISTANCIA" ? (
            <>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="item-faixa-min">Distância mín. (km)</Label>
                  <Input id="item-faixa-min" required type="number" step="0.01" value={faixaMin} onChange={(e) => setFaixaMin(e.target.value)} />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="item-faixa-max">Distância máx. (km)</Label>
                  <Input id="item-faixa-max" required type="number" step="0.01" value={faixaMax} onChange={(e) => setFaixaMax(e.target.value)} />
                </div>
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="item-faixa-modo">Modo</Label>
                <Select value={faixaModo} onValueChange={(value) => setFaixaModo(value as FaixaDistanciaMode)}>
                  <SelectTrigger id="item-faixa-modo">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="TARIFA_POR_KM">Tarifa por km dentro da faixa</SelectItem>
                    <SelectItem value="VALOR_FIXO">Valor fixo pela faixa inteira</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </>
          ) : null}

          {unidade === "PERCENTUAL" ? (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="item-base-descricao">Base do percentual (descrição explícita)</Label>
              <Input
                id="item-base-descricao" required value={basePercentualDescricao}
                onChange={(event) => setBasePercentualDescricao(event.target.value)}
                placeholder="Ex: valor do contrato guarda-chuva vigente"
              />
            </div>
          ) : null}

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="item-valor">
              {unidade === "PERCENTUAL" ? "Percentual (%)" : "Valor"}
            </Label>
            <Input id="item-valor" required type="number" step="0.01" value={valor} onChange={(event) => setValor(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="item-valor-minimo">Valor mínimo (opcional)</Label>
            <Input id="item-valor-minimo" type="number" step="0.01" value={valorMinimo} onChange={(event) => setValorMinimo(event.target.value)} />
          </div>

          <div className="grid grid-cols-2 gap-3 border-t border-border pt-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="item-adicional-fixo">Adicional fixo</Label>
              <Input id="item-adicional-fixo" type="number" step="0.01" value={adicionalFixo} onChange={(e) => setAdicionalFixo(e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="item-desconto-fixo">Desconto fixo</Label>
              <Input id="item-desconto-fixo" type="number" step="0.01" value={descontoFixo} onChange={(e) => setDescontoFixo(e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="item-adicional-percentual">Adicional %</Label>
              <Input id="item-adicional-percentual" type="number" step="0.01" value={adicionalPercentual} onChange={(e) => setAdicionalPercentual(e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="item-desconto-percentual">Desconto %</Label>
              <Input id="item-desconto-percentual" type="number" step="0.01" value={descontoPercentual} onChange={(e) => setDescontoPercentual(e.target.value)} />
            </div>
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createItem.isPending}>
              {createItem.isPending ? "Adicionando…" : "Adicionar item"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

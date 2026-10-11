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
import type { PriceTableDirection } from "@gestorfrete/types";

import { useClientsQuery } from "@/modules/crm/hooks/use-clients";
import { useCreatePriceTableMutation } from "@/modules/pricing/hooks/use-price-tables";
import { ApiError } from "@/shared/lib/api-client";

interface PriceTableFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** `cliente_id` só faz sentido para `direcao=VENDA` — ausência quer dizer "tabela geral", aplicável
 * a qualquer cliente. `direcao=COMPRA` nunca mostra o seletor (backend rejeita se vier junto). */
export function PriceTableFormDrawer({ open, onOpenChange }: PriceTableFormDrawerProps) {
  const [nome, setNome] = React.useState("");
  const [direcao, setDirecao] = React.useState<PriceTableDirection>("VENDA");
  const [vigenciaInicio, setVigenciaInicio] = React.useState("");
  const [vigenciaFim, setVigenciaFim] = React.useState("");
  const [clienteId, setClienteId] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const clientsQuery = useClientsQuery({ limit: 100 });
  const createPriceTable = useCreatePriceTableMutation();

  function reset() {
    setNome(""); setDirecao("VENDA"); setVigenciaInicio(""); setVigenciaFim(""); setClienteId("");
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createPriceTable.mutateAsync({
        nome, direcao, vigencia_inicio: vigenciaInicio, vigencia_fim: vigenciaFim || undefined,
        cliente_id: direcao === "VENDA" && clienteId ? clienteId : undefined,
      });
      toast.success("Tabela de frete criada.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar a tabela de frete.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Nova tabela de frete</SheetTitle>
          <SheetDescription>Comece em rascunho — adicione itens depois e ative quando estiver pronta.</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="price-table-nome">Nome</Label>
            <Input id="price-table-nome" required value={nome} onChange={(event) => setNome(event.target.value)} />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="price-table-direcao">Direção</Label>
            <Select value={direcao} onValueChange={(value) => setDirecao(value as PriceTableDirection)}>
              <SelectTrigger id="price-table-direcao">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="VENDA">Venda (cobrado do cliente)</SelectItem>
                <SelectItem value="COMPRA">Compra (pago a transportador)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {direcao === "VENDA" ? (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="price-table-cliente">Cliente (opcional — vazio aplica a todos)</Label>
              <Select value={clienteId || "none"} onValueChange={(value) => setClienteId(value === "none" ? "" : value)}>
                <SelectTrigger id="price-table-cliente">
                  <SelectValue placeholder="Todos os clientes" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Todos os clientes</SelectItem>
                  {clientsQuery.data?.data.map((client) => (
                    <SelectItem key={client.id} value={client.id}>
                      {client.razao_social}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ) : null}

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="price-table-vigencia-inicio">Vigência — início</Label>
            <Input
              id="price-table-vigencia-inicio" type="date" required value={vigenciaInicio}
              onChange={(event) => setVigenciaInicio(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="price-table-vigencia-fim">Vigência — fim (opcional)</Label>
            <Input
              id="price-table-vigencia-fim" type="date" value={vigenciaFim}
              onChange={(event) => setVigenciaFim(event.target.value)}
            />
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createPriceTable.isPending}>
              {createPriceTable.isPending ? "Criando…" : "Criar tabela"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

"use client";

import * as React from "react";
import Link from "next/link";
import { Plus } from "lucide-react";

import {
  Badge,
  Button,
  Checkbox,
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
import type { CombinationType } from "@gestorfrete/types";

import { useCreateVehicleCompositionMutation, useVehicleCompositionsQuery } from "@/modules/fleet/hooks/use-vehicle-compositions";
import { useImplementsQuery } from "@/modules/fleet/hooks/use-implements";
import { ApiError } from "@/shared/lib/api-client";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const COMBINATION_TYPE_LABEL: Record<CombinationType, string> = { SIMPLES: "Simples", BITREM: "Bitrem", RODOTREM: "Rodotrem" };

interface CompositionsTimelineProps {
  vehicleId: string;
  editable: boolean;
}

/**
 * D248 — Composição nunca é editada in-place. "Nova composição" é o único botão que existe; ele
 * faz `POST /vehicle-compositions` com o estado completo, e o Backend fecha a vigência anterior
 * automaticamente. Não há botão de editar/excluir aqui, de propósito.
 */
export function CompositionsTimeline({ vehicleId, editable }: CompositionsTimelineProps) {
  const currentQuery = useVehicleCompositionsQuery({ veiculo_tracionador_id: vehicleId, vigente: true, limit: 100 });
  const historyQuery = useVehicleCompositionsQuery({ veiculo_tracionador_id: vehicleId, vigente: false, limit: 100 });
  const implementsQuery = useImplementsQuery({ limit: 100 });
  const createComposition = useCreateVehicleCompositionMutation();

  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [combinationType, setCombinationType] = React.useState<CombinationType>("SIMPLES");
  const [totalAxles, setTotalAxles] = React.useState("");
  const [selectedImplements, setSelectedImplements] = React.useState<string[]>([]);
  const [formError, setFormError] = React.useState<string | null>(null);

  function toggleImplement(implementId: string) {
    setSelectedImplements((current) =>
      current.includes(implementId) ? current.filter((id) => id !== implementId) : [...current, implementId]
    );
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createComposition.mutateAsync({
        tractor_unit_id: vehicleId,
        combination_type: combinationType,
        total_axles: Number(totalAxles),
        implements: selectedImplements.map((implement_id, index) => ({ implement_id, order: index + 1 })),
      });
      toast.success("Nova composição criada — a anterior foi encerrada automaticamente.");
      setSelectedImplements([]);
      setTotalAxles("");
      setDrawerOpen(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível criar a composição.");
    }
  }

  if (currentQuery.isLoading || historyQuery.isLoading) return <LoadingState rows={3} />;
  if (currentQuery.error || historyQuery.error)
    return <ErrorState description="Não foi possível carregar as composições." onRetry={() => currentQuery.refetch()} />;

  const current = currentQuery.data?.data ?? [];
  const history = [...(historyQuery.data?.data ?? [])].sort(
    (a, b) => new Date(b.starts_at).getTime() - new Date(a.starts_at).getTime()
  );
  // Deduped by id: `current` (vigente=true) and `history` (vigente=false) are two independent
  // queries that can transiently overlap right after a create (one refetches before the other),
  // since the Backend's own "current" set changes as a side effect of that same write.
  const all = Array.from(new Map([...current, ...history].map((composition) => [composition.id, composition])).values());

  return (
    <div className="flex flex-col gap-4">
      {editable ? (
        <div className="flex justify-end">
          <Button size="sm" onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Nova composição
          </Button>
        </div>
      ) : null}

      {all.length === 0 ? (
        <EmptyState title="Nenhuma composição registrada" />
      ) : (
        <div className="flex flex-col gap-3 border-l-2 border-border pl-4">
          {all.map((composition) => (
            <div key={composition.id} className="relative rounded-md border border-border p-4">
              <span
                className={`absolute -left-[21px] top-5 h-2.5 w-2.5 rounded-full ${
                  composition.ends_at ? "bg-muted-foreground" : "bg-primary"
                }`}
              />
              <div className="flex items-center gap-2">
                <Badge variant={composition.ends_at ? "secondary" : "success"}>{composition.ends_at ? "Encerrada" : "Vigente"}</Badge>
                <span className="text-sm font-medium">{COMBINATION_TYPE_LABEL[composition.combination_type]}</span>
                <span className="text-sm text-muted-foreground">{composition.total_axles} eixos</span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Desde {new Date(composition.starts_at).toLocaleString("pt-BR")}
                {composition.ends_at ? ` até ${new Date(composition.ends_at).toLocaleString("pt-BR")}` : ""}
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {composition.implements.map((item) => (
                  <Link key={item.implement_id} href={`/implementos/${item.implement_id}`}>
                    <Badge variant="outline">Implemento {item.implement_id.slice(0, 8)}</Badge>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
        <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Nova composição</SheetTitle>
            <SheetDescription>Cria uma nova vigência — a composição vigente atual é encerrada automaticamente.</SheetDescription>
          </SheetHeader>
          <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label>Tipo de combinação</Label>
              <Select value={combinationType} onValueChange={(value) => setCombinationType(value as CombinationType)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(Object.keys(COMBINATION_TYPE_LABEL) as CombinationType[]).map((value) => (
                    <SelectItem key={value} value={value}>
                      {COMBINATION_TYPE_LABEL[value]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="composition-axles">Total de eixos</Label>
              <Input id="composition-axles" type="number" required value={totalAxles} onChange={(event) => setTotalAxles(event.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Implementos</Label>
              <div className="flex max-h-56 flex-col gap-2 overflow-y-auto rounded-md border border-border p-3">
                {implementsQuery.isLoading ? (
                  <p className="text-sm text-muted-foreground">Carregando implementos…</p>
                ) : implementsQuery.data?.data.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Nenhum implemento cadastrado ainda.</p>
                ) : (
                  implementsQuery.data?.data.map((implement) => (
                    <label key={implement.id} className="flex items-center gap-2 text-sm">
                      <Checkbox
                        checked={selectedImplements.includes(implement.id)}
                        onCheckedChange={() => toggleImplement(implement.id)}
                      />
                      {implement.plate} — {implement.codigo}
                    </label>
                  ))
                )}
              </div>
            </div>

            {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

            <div className="mt-auto flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setDrawerOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createComposition.isPending}>
                {createComposition.isPending ? "Criando…" : "Criar composição"}
              </Button>
            </div>
          </form>
        </SheetContent>
      </Sheet>
    </div>
  );
}

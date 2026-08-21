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
  Textarea,
  toast,
} from "@gestorfrete/ui";
import type { OccurrenceSeverity, OccurrenceType } from "@gestorfrete/types";

import { useCreateOccurrenceMutation } from "@/modules/freight/hooks/use-occurrences";
import { ApiError } from "@/shared/lib/api-client";

const TYPE_LABEL: Record<OccurrenceType, string> = {
  ATRASO: "Atraso",
  AVARIA: "Avaria",
  PANE: "Pane",
  SINISTRO: "Sinistro",
  OUTRO: "Outro",
};

const SEVERITY_LABEL: Record<OccurrenceSeverity, string> = { BAIXA: "Baixa", MEDIA: "Média", ALTA: "Alta", CRITICA: "Crítica" };

interface OccurrenceFormDrawerProps {
  tripId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Create-only aqui — Ocorrência é uma entidade genérica única para todos os tipos (D076). O
 * campo `location` (latitude/longitude) existe no contrato mas não é persistido no Backend
 * (lacuna documentada em `017-trip-occurrences.md`) — omitido deste formulário de propósito, para
 * não sugerir que o dado é salvo quando não é.
 */
export function OccurrenceFormDrawer({ tripId, open, onOpenChange }: OccurrenceFormDrawerProps) {
  const [type, setType] = React.useState<OccurrenceType>("ATRASO");
  const [description, setDescription] = React.useState("");
  const [severity, setSeverity] = React.useState<OccurrenceSeverity | "">("");
  const [occurredAt, setOccurredAt] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const createOccurrence = useCreateOccurrenceMutation(tripId);

  function reset() {
    setType("ATRASO");
    setDescription("");
    setSeverity("");
    setOccurredAt("");
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createOccurrence.mutateAsync({
        type,
        description,
        severity: severity || undefined,
        occurred_at: occurredAt ? new Date(occurredAt).toISOString() : new Date().toISOString(),
      });
      toast.success("Ocorrência registrada.");
      reset();
      onOpenChange(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Não foi possível registrar a ocorrência.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Nova ocorrência</SheetTitle>
          <SheetDescription>Registra um evento na viagem (atraso, avaria, pane, sinistro).</SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="occurrence-type">Tipo</Label>
            <Select value={type} onValueChange={(value) => setType(value as OccurrenceType)}>
              <SelectTrigger id="occurrence-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(TYPE_LABEL) as OccurrenceType[]).map((value) => (
                  <SelectItem key={value} value={value}>
                    {TYPE_LABEL[value]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="occurrence-description">Descrição</Label>
            <Textarea id="occurrence-description" required value={description} onChange={(event) => setDescription(event.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Gravidade (opcional)</Label>
            <Select value={severity} onValueChange={(value) => setSeverity(value as OccurrenceSeverity)}>
              <SelectTrigger>
                <SelectValue placeholder="Não informada" />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(SEVERITY_LABEL) as OccurrenceSeverity[]).map((value) => (
                  <SelectItem key={value} value={value}>
                    {SEVERITY_LABEL[value]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="occurrence-occurred-at">Data/hora do evento</Label>
            <Input
              id="occurrence-occurred-at"
              type="datetime-local"
              required
              value={occurredAt}
              onChange={(event) => setOccurredAt(event.target.value)}
            />
          </div>

          {formError ? <p className="text-sm text-destructive">{formError}</p> : null}

          <div className="mt-auto flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createOccurrence.isPending}>
              {createOccurrence.isPending ? "Registrando…" : "Registrar ocorrência"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

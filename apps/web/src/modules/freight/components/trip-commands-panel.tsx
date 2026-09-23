"use client";

import * as React from "react";

import { Button, Input, Label, Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, Textarea, toast } from "@gestorfrete/ui";
import type { Trip, TripOperationalStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import {
  useAcceptTripMutation,
  useCancelarTripMutation,
  useCloseAdministrativeTripMutation,
  useDispatchTripMutation,
  useFinishTripMutation,
  useInterromperTripMutation,
  useRetomarTripMutation,
  useStartTripMutation,
} from "@/modules/freight/hooks/use-trips";
import { ApiError } from "@/shared/lib/api-client";

const INTERRUPTIBLE: TripOperationalStatus[] = ["EM_DESLOCAMENTO", "CARREGANDO", "EM_TRANSITO", "EM_ENTREGA"];
const CANCELLABLE: TripOperationalStatus[] = ["RASCUNHO", "PLANEJADA", "AGUARDANDO_CHECKLIST", "LIBERADA", "INTERROMPIDA"];
const TERMINAL: TripOperationalStatus[] = ["FINALIZADA", "CANCELADA"];

type CommandKey = "accept" | "dispatch" | "start" | "finish" | "interromper" | "retomar" | "cancelar" | "close-administrative";
type DialogCommandKey = "interromper" | "cancelar" | "close-administrative";

/**
 * Só renderiza o(s) comando(s) válido(s) para o `status.operational` atual — nunca um botão para
 * uma transição inválida (`docs/flows/002-VIAGEM.md`). Status nunca muda por PATCH: cada botão é
 * um `POST .../commands/<verbo>` (D233). `encerrada` é derivada pelo Postgres e nunca tem botão —
 * não aparece aqui em nenhuma hipótese, nem para Admin SaaS (D019/D020).
 *
 * Nota (auditoria deste Lote): `AGUARDANDO_CHECKLIST→LIBERADA`, `EM_DESLOCAMENTO→CARREGANDO` e
 * `CARREGANDO→EM_TRANSITO` não têm nenhum endpoint HTTP — dependem de módulos futuros (Checklist,
 * Coleta, Romaneio) ainda não implementados. Isso significa que, hoje, uma Viagem criada por esta
 * UI nunca alcança `LIBERADA`/`EM_ENTREGA` de verdade — Despachar/Iniciar/Finalizar/Interromper só
 * ficam clicáveis quando o estado correspondente existir (o que, na prática, ainda não acontece
 * neste ambiente). O componente é construído para a máquina de estados completa mesmo assim, para
 * não precisar ser reescrito quando esses módulos existirem.
 *
 * V1 Operational Hardening, Parte 2 — Despachar/Iniciar ganham um campo opcional de hodômetro de
 * saída ao lado do botão, Finalizar um de hodômetro de chegada — inline, nunca atrás de um diálogo
 * extra: continua sendo um único clique para quem não usa hodômetro (D-consistente com todo botão
 * "simples" já existente aqui), o campo só é lido se estiver preenchido. Grava a leitura de
 * fronteira em `leituras_hodometro` (`fleet`), nunca uma segunda fonte da verdade.
 */
export function TripCommandsPanel({ trip }: { trip: Trip }) {
  const { hasPermission } = usePermissions();
  const status = trip.status.operational;

  const [openDialog, setOpenDialog] = React.useState<DialogCommandKey | null>(null);
  const [text, setText] = React.useState("");
  const [departureOdometerKm, setDepartureOdometerKm] = React.useState("");
  const [arrivalOdometerKm, setArrivalOdometerKm] = React.useState("");

  const accept = useAcceptTripMutation();
  const dispatch = useDispatchTripMutation();
  const start = useStartTripMutation();
  const finish = useFinishTripMutation();
  const interromper = useInterromperTripMutation();
  const retomar = useRetomarTripMutation();
  const cancelar = useCancelarTripMutation();
  const closeAdministrative = useCloseAdministrativeTripMutation();

  async function runSimple(
    key: CommandKey,
    mutation: ReturnType<typeof useAcceptTripMutation>,
    successMessage: string
  ) {
    try {
      await mutation.mutateAsync({ tripId: trip.id, variables: undefined });
      toast.success(successMessage);
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : `Não foi possível executar "${key}".`);
    }
  }

  async function runDispatch(mutation: typeof dispatch | typeof start, key: "dispatch" | "start", successMessage: string) {
    try {
      await mutation.mutateAsync({
        tripId: trip.id,
        variables: departureOdometerKm ? { departure_odometer_km: departureOdometerKm } : undefined,
      });
      toast.success(successMessage);
      setDepartureOdometerKm("");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : `Não foi possível executar "${key}".`);
    }
  }

  async function runFinish() {
    try {
      await finish.mutateAsync({
        tripId: trip.id, variables: arrivalOdometerKm ? { arrival_odometer_km: arrivalOdometerKm } : undefined,
      });
      toast.success("Viagem finalizada.");
      setArrivalOdometerKm("");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível executar \"finish\".");
    }
  }

  async function runWithText(key: DialogCommandKey) {
    try {
      if (key === "interromper") await interromper.mutateAsync({ tripId: trip.id, variables: { notes: text } });
      if (key === "cancelar") await cancelar.mutateAsync({ tripId: trip.id, variables: { notes: text } });
      if (key === "close-administrative")
        await closeAdministrative.mutateAsync({ tripId: trip.id, variables: { justification: text } });
      toast.success("Viagem atualizada.");
      setOpenDialog(null);
      setText("");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível executar a ação.");
    }
  }

  const buttons: React.ReactNode[] = [];
  let odometerField: React.ReactNode = null;

  if (status === "PLANEJADA" && hasPermission("freight.trip.edit")) {
    buttons.push(
      <Button key="accept" variant="outline" onClick={() => runSimple("accept", accept, "Viagem aceita.")}>
        Aceitar
      </Button>
    );
  }
  if (status === "LIBERADA" && (hasPermission("freight.trip.dispatch") || hasPermission("freight.trip.start"))) {
    odometerField = (
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="trip-departure-odometer-km">Hodômetro de saída (opcional)</Label>
        <Input
          id="trip-departure-odometer-km" type="number" step="0.01" className="w-40"
          value={departureOdometerKm} onChange={(event) => setDepartureOdometerKm(event.target.value)}
        />
      </div>
    );
  }
  if (status === "LIBERADA" && hasPermission("freight.trip.dispatch")) {
    buttons.push(
      <Button key="dispatch" onClick={() => runDispatch(dispatch, "dispatch", "Viagem despachada.")}>
        Despachar
      </Button>
    );
  }
  if (status === "LIBERADA" && hasPermission("freight.trip.start")) {
    buttons.push(
      <Button key="start" onClick={() => runDispatch(start, "start", "Viagem iniciada.")}>
        Iniciar
      </Button>
    );
  }
  if (status === "EM_ENTREGA" && hasPermission("freight.trip.finish")) {
    odometerField = (
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="trip-arrival-odometer-km">Hodômetro de chegada (opcional)</Label>
        <Input
          id="trip-arrival-odometer-km" type="number" step="0.01" className="w-40"
          value={arrivalOdometerKm} onChange={(event) => setArrivalOdometerKm(event.target.value)}
        />
      </div>
    );
    buttons.push(
      <Button key="finish" onClick={() => runFinish()}>
        Finalizar
      </Button>
    );
  }
  if (INTERRUPTIBLE.includes(status) && hasPermission("freight.trip.edit")) {
    buttons.push(
      <Button key="interromper" variant="outline" onClick={() => setOpenDialog("interromper")}>
        Interromper
      </Button>
    );
  }
  if (status === "INTERROMPIDA" && hasPermission("freight.trip.edit")) {
    buttons.push(
      <Button key="retomar" variant="outline" onClick={() => runSimple("retomar", retomar, "Viagem retomada.")}>
        Retomar
      </Button>
    );
  }
  if (CANCELLABLE.includes(status) && hasPermission("freight.trip.cancel")) {
    buttons.push(
      <Button key="cancelar" variant="destructive" onClick={() => setOpenDialog("cancelar")}>
        Cancelar
      </Button>
    );
  }
  if (!TERMINAL.includes(status) && hasPermission("freight.trip.close")) {
    buttons.push(
      <Button key="close-administrative" variant="outline" onClick={() => setOpenDialog("close-administrative")}>
        Encerramento administrativo
      </Button>
    );
  }

  const dialogCopy: Record<DialogCommandKey, { title: string; description: string; label: string; confirm: string }> = {
    interromper: {
      title: "Interromper viagem",
      description: "Registre o motivo (pane, sinistro, etc.) — obrigatório.",
      label: "Observação",
      confirm: "Interromper",
    },
    cancelar: {
      title: "Cancelar viagem",
      description: "Registre o motivo do cancelamento — obrigatório.",
      label: "Observação",
      confirm: "Cancelar viagem",
    },
    "close-administrative": {
      title: "Encerramento administrativo",
      description: "Força o encerramento (→ Finalizada) fora do fluxo normal — sempre auditado com justificativa.",
      label: "Justificativa",
      confirm: "Encerrar administrativamente",
    },
  };

  return (
    <div className="flex flex-col gap-3">
      {odometerField}
      {buttons.length > 0 ? <div className="flex flex-wrap gap-2">{buttons}</div> : null}

      <Sheet open={openDialog !== null} onOpenChange={(open) => !open && setOpenDialog(null)}>
        <SheetContent className="flex flex-col gap-6 overflow-y-auto sm:max-w-md">
          {openDialog ? (
            <>
              <SheetHeader>
                <SheetTitle>{dialogCopy[openDialog].title}</SheetTitle>
                <SheetDescription>{dialogCopy[openDialog].description}</SheetDescription>
              </SheetHeader>
              <div className="flex flex-1 flex-col gap-4">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="command-text">{dialogCopy[openDialog].label}</Label>
                  <Textarea id="command-text" required value={text} onChange={(event) => setText(event.target.value)} />
                </div>
                <div className="mt-auto flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setOpenDialog(null)}>
                    Voltar
                  </Button>
                  <Button
                    variant={openDialog === "cancelar" ? "destructive" : "default"}
                    disabled={
                      !text.trim() ||
                      interromper.isPending ||
                      cancelar.isPending ||
                      closeAdministrative.isPending
                    }
                    onClick={() => runWithText(openDialog)}
                  >
                    {dialogCopy[openDialog].confirm}
                  </Button>
                </div>
              </div>
            </>
          ) : null}
        </SheetContent>
      </Sheet>
    </div>
  );
}

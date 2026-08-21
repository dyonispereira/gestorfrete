import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@gestorfrete/ui";
import type { Trip } from "@gestorfrete/types";

/**
 * `references.*` são IDs vivos da entidade atual; `snapshots.*` congelam num momento específico
 * (`client_snapshot` na criação, `driver_name_snapshot`/`tractor_unit_plate_snapshot` no
 * despacho) e nunca ressincronizam — mostrados aqui deliberadamente separados, nunca misturados
 * na mesma linha, para não sugerir que um é "atualização" do outro.
 */
export function TripSnapshotsCard({ trip }: { trip: Trip }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Referências (atuais)</CardTitle>
          <CardDescription>Apontam para o estado vivo das entidades.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 text-sm">
          <Row label="Cliente" value={trip.references.client_id} />
          <Row label="Motorista" value={trip.references.driver_id} />
          <Row label="Veículo tracionador" value={trip.references.tractor_unit_id} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Snapshots (histórico)</CardTitle>
          <CardDescription>Congelados no momento da criação/despacho — nunca ressincronizam.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 text-sm">
          <Row label="Motorista (snapshot)" value={trip.snapshots.driver_name_snapshot} />
          <Row label="Placa (snapshot)" value={trip.snapshots.tractor_unit_plate_snapshot} />
          <Row label="Receita prevista (snapshot)" value={trip.snapshots.predicted_revenue_snapshot} />
        </CardContent>
      </Card>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string | undefined }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value ?? "—"}</span>
    </div>
  );
}

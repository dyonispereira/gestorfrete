import { apiFetch } from "@/shared/lib/api-client";
import type {
  CancelarTripRequest,
  CloseAdministrativeTripRequest,
  CreateTripRequest,
  DispatchTripRequest,
  FinishTripRequest,
  InterromperTripRequest,
  PaginatedResponse,
  Trip,
  UpdateTripRequest,
} from "@gestorfrete/types";

export interface ListTripsParams {
  page?: number;
  limit?: number;
  status_operacional?: string;
  status_fiscal?: string;
  status_financeiro?: string;
  motorista_id?: string;
  veiculo_id?: string;
  cliente_id?: string;
  data_programada?: string;
  codigo?: string;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listTrips(params: ListTripsParams = {}): Promise<PaginatedResponse<Trip>> {
  return apiFetch<PaginatedResponse<Trip>>(`/viagens${toQuery(params)}`);
}

export function getTrip(id: string): Promise<Trip> {
  return apiFetch<Trip>(`/viagens/${id}`);
}

export function createTrip(body: CreateTripRequest): Promise<Trip> {
  return apiFetch<Trip>("/viagens", { method: "POST", body });
}

export function updateTrip(id: string, body: UpdateTripRequest): Promise<Trip> {
  return apiFetch<Trip>(`/viagens/${id}`, { method: "PATCH", body });
}

/** Blocked outside RASCUNHO/PLANEJADA (422 `FREIGHT_TRIP_CANNOT_DELETE_STARTED`). */
export function deleteTrip(id: string): Promise<void> {
  return apiFetch<void>(`/viagens/${id}`, { method: "DELETE" });
}

/* ── Comandos de status (018-trip-status.md) — status nunca é alterado por PATCH. ── */

export function acceptTrip(id: string): Promise<Trip> {
  return apiFetch<Trip>(`/viagens/${id}/commands/accept`, { method: "POST" });
}

export function dispatchTrip(id: string, body?: DispatchTripRequest): Promise<Trip> {
  return apiFetch<Trip>(`/viagens/${id}/commands/dispatch`, { method: "POST", body: body ?? {} });
}

export function startTrip(id: string, body?: DispatchTripRequest): Promise<Trip> {
  return apiFetch<Trip>(`/viagens/${id}/commands/start`, { method: "POST", body: body ?? {} });
}

export function finishTrip(id: string, body?: FinishTripRequest): Promise<Trip> {
  return apiFetch<Trip>(`/viagens/${id}/commands/finish`, { method: "POST", body: body ?? {} });
}

export function interromperTrip(id: string, body: InterromperTripRequest): Promise<Trip> {
  return apiFetch<Trip>(`/viagens/${id}/commands/interromper`, { method: "POST", body });
}

export function retomarTrip(id: string): Promise<Trip> {
  return apiFetch<Trip>(`/viagens/${id}/commands/retomar`, { method: "POST" });
}

export function cancelarTrip(id: string, body: CancelarTripRequest): Promise<Trip> {
  return apiFetch<Trip>(`/viagens/${id}/commands/cancelar`, { method: "POST", body });
}

export function closeAdministrativeTrip(id: string, body: CloseAdministrativeTripRequest): Promise<Trip> {
  return apiFetch<Trip>(`/viagens/${id}/commands/close-administrative`, { method: "POST", body });
}

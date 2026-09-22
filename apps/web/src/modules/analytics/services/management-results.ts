import { apiFetch } from "@/shared/lib/api-client";
import type {
  ClientResult,
  ClientResultDetail,
  DriverResult,
  DriverResultDetail,
  OverviewResult,
  PaginatedResponse,
  TripResult,
  VehicleResult,
  VehicleResultDetail,
} from "@gestorfrete/types";

export interface PeriodParams {
  date_from?: string;
  date_to?: string;
}

function toQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

/** Todo endpoint de Resultado Gerencial usa os mesmos dois parâmetros de período (090-management-
 * results.md) — `date_from`/`date_to` no front viram `data_programada__gte`/`__lte` na API. */
function periodQuery(period: PeriodParams, extra: Record<string, string | number | undefined> = {}): string {
  return toQuery({ data_programada__gte: period.date_from, data_programada__lte: period.date_to, ...extra });
}

export function getOverview(period: PeriodParams): Promise<OverviewResult> {
  return apiFetch<OverviewResult>(`/analytics/resultado-gerencial/visao-geral${periodQuery(period)}`);
}

export interface ListTripResultsParams extends PeriodParams {
  client_id?: string;
  vehicle_id?: string;
  driver_id?: string;
  page?: number;
  limit?: number;
}

export function listTripResults(params: ListTripResultsParams): Promise<PaginatedResponse<TripResult>> {
  const { date_from, date_to, ...rest } = params;
  return apiFetch<PaginatedResponse<TripResult>>(
    `/analytics/resultado-gerencial/viagens${periodQuery({ date_from, date_to }, rest)}`
  );
}

export function listVehicleResults(period: PeriodParams): Promise<VehicleResult[]> {
  return apiFetch<VehicleResult[]>(`/analytics/resultado-gerencial/veiculos${periodQuery(period)}`);
}

export function getVehicleResultDetail(vehicleId: string, period: PeriodParams): Promise<VehicleResultDetail> {
  return apiFetch<VehicleResultDetail>(`/analytics/resultado-gerencial/veiculos/${vehicleId}${periodQuery(period)}`);
}

export function listClientResults(period: PeriodParams): Promise<ClientResult[]> {
  return apiFetch<ClientResult[]>(`/analytics/resultado-gerencial/clientes${periodQuery(period)}`);
}

export function getClientResultDetail(clientId: string, period: PeriodParams): Promise<ClientResultDetail> {
  return apiFetch<ClientResultDetail>(`/analytics/resultado-gerencial/clientes/${clientId}${periodQuery(period)}`);
}

export function listDriverResults(period: PeriodParams): Promise<DriverResult[]> {
  return apiFetch<DriverResult[]>(`/analytics/resultado-gerencial/motoristas${periodQuery(period)}`);
}

export function getDriverResultDetail(driverId: string, period: PeriodParams): Promise<DriverResultDetail> {
  return apiFetch<DriverResultDetail>(`/analytics/resultado-gerencial/motoristas/${driverId}${periodQuery(period)}`);
}

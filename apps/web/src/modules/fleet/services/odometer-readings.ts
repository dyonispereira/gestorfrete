import { apiFetch } from "@/shared/lib/api-client";
import type { CreateOdometerReadingRequest, CursorPaginatedResponse, OdometerReading } from "@gestorfrete/types";

export interface ListOdometerReadingsParams {
  cursor?: string;
  limit?: number;
  origem?: string;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

/** Time Series — no update/delete service function exists, matches the Backend having none. */
export function listOdometerReadings(
  vehicleId: string,
  params: ListOdometerReadingsParams = {}
): Promise<CursorPaginatedResponse<OdometerReading>> {
  return apiFetch<CursorPaginatedResponse<OdometerReading>>(`/veiculos/${vehicleId}/odometro/leituras${toQuery(params)}`);
}

export function createOdometerReading(vehicleId: string, body: CreateOdometerReadingRequest): Promise<OdometerReading> {
  return apiFetch<OdometerReading>(`/veiculos/${vehicleId}/odometro/leituras`, { method: "POST", body });
}

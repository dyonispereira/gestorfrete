import { apiFetch } from "@/shared/lib/api-client";
import type { FiscalConfiguration, UpdateFiscalConfigurationRequest } from "@gestorfrete/types";

/** Singular por tenant — sem lista, sem POST/DELETE (criada só no onboarding, fora de escopo). */
export function getFiscalConfiguration(): Promise<FiscalConfiguration> {
  return apiFetch<FiscalConfiguration>("/configuracao-fiscal");
}

/** Cada campo enviado exige sua própria permissão no Backend — um campo sem permissão rejeita a requisição inteira. */
export function updateFiscalConfiguration(body: UpdateFiscalConfigurationRequest): Promise<FiscalConfiguration> {
  return apiFetch<FiscalConfiguration>("/configuracao-fiscal", { method: "PATCH", body });
}

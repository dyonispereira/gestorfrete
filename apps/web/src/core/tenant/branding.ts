import type { TenantContext } from "@gestorfrete/types";

export interface TenantBranding {
  displayName: string;
  /** HSL channel triplet (`h s% l%`), same format as every other token in `globals.css`. */
  primaryColorHsl: string | null;
  logoUrl: string | null;
}

/**
 * Derives branding from real Tenant data. `GET/PATCH /tenant/settings/branding`
 * has no contract yet — `docs/api/002-tenants.md` explicitly defers it
 * ("fica para um lote futuro, não inventados aqui só porque 'parecem parte
 * do Tenant'"), and neither `Tenant` nor `TenantContext` carries a
 * logo/color field. So this only uses what's genuinely available today
 * (`razao_social`) and leaves `primaryColorHsl`/`logoUrl` null rather than
 * fabricating per-tenant values — the Shell falls back to the default
 * `--primary` token (see `globals.css`) until a real branding endpoint gets
 * its own decision.
 */
export function resolveTenantBranding(tenant: TenantContext | null): TenantBranding {
  return {
    displayName: tenant?.razao_social ?? "GestorFrete",
    primaryColorHsl: null,
    logoUrl: null,
  };
}

/** Applies branding to the document root as a CSS variable, read by the `tenant-brand` token. */
export function applyTenantBranding(branding: TenantBranding): void {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  if (branding.primaryColorHsl) {
    root.style.setProperty("--tenant-brand", branding.primaryColorHsl);
  } else {
    root.style.removeProperty("--tenant-brand");
  }
}

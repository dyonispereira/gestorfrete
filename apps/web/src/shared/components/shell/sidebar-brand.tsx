"use client";

import { Truck } from "lucide-react";

import { useSession } from "@/core/tenant/session-provider";
import { resolveTenantBranding } from "@/core/tenant/branding";

export function SidebarBrand() {
  const { tenant } = useSession();
  const branding = resolveTenantBranding(tenant);

  return (
    <div className="flex h-header-h items-center gap-2.5 border-b border-sidebar-border px-4">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-sidebar-primary text-sidebar-primary-foreground">
        <Truck className="h-4.5 w-4.5" />
      </div>
      <div className="flex min-w-0 flex-col">
        <span className="truncate text-sm font-semibold text-sidebar-foreground">{branding.displayName}</span>
        <span className="truncate text-xs text-sidebar-foreground/50">GestorFrete ERP</span>
      </div>
    </div>
  );
}

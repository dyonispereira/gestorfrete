"use client";

import * as React from "react";

import { Toaster } from "@gestorfrete/ui";

import { QueryProvider } from "@/shared/lib/query-provider";
import { AuthProvider } from "@/core/auth/auth-provider";
import { SessionProvider, useSession } from "@/core/tenant/session-provider";
import { PermissionsProvider } from "@/core/rbac/permissions-provider";
import { applyTenantBranding, resolveTenantBranding } from "@/core/tenant/branding";
import { BreadcrumbLabelProvider } from "@/shared/components/shell/breadcrumb-label-context";

function TenantBrandingEffect() {
  const { tenant } = useSession();

  React.useEffect(() => {
    applyTenantBranding(resolveTenantBranding(tenant));
  }, [tenant]);

  return null;
}

export function AppProviders({ children }: { children: React.ReactNode }) {
  return (
    <QueryProvider>
      <AuthProvider>
        <SessionProvider>
          <PermissionsProvider>
            <BreadcrumbLabelProvider>
              <TenantBrandingEffect />
              {children}
              <Toaster />
            </BreadcrumbLabelProvider>
          </PermissionsProvider>
        </SessionProvider>
      </AuthProvider>
    </QueryProvider>
  );
}

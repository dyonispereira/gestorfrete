"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@gestorfrete/ui";
import { useAuthorizedNav } from "@/core/rbac/use-authorized-nav";

import { LoadingState } from "@/shared/components/states/loading-state";
import { usePermissions } from "@/core/rbac/permissions-provider";

export function NavContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const groups = useAuthorizedNav();
  const { isLoading } = usePermissions();

  if (isLoading) {
    return (
      <div className="px-3 py-2">
        <LoadingState rows={5} />
      </div>
    );
  }

  return (
    <nav className="flex flex-col gap-4 px-3 py-2" aria-label="Navegação principal">
      {groups.map((group) => (
        <div key={group.id} className="flex flex-col gap-1">
          <p className="px-2 text-xs font-semibold uppercase tracking-wide text-sidebar-foreground/50">
            {group.label}
          </p>
          {group.items.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(`${item.href}/`);
            const Icon = item.icon;
            return (
              <Link
                key={item.id}
                href={item.href}
                onClick={onNavigate}
                title={item.description}
                className={cn(
                  "flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground"
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span className="truncate">{item.label}</span>
              </Link>
            );
          })}
        </div>
      ))}
    </nav>
  );
}

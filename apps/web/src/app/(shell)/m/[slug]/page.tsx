"use client";

import { notFound } from "next/navigation";
import { Construction } from "lucide-react";

import { NAV_GROUPS } from "@/core/rbac/nav-config";
import { EmptyState } from "@/shared/components/states/empty-state";

const ALL_ITEMS = NAV_GROUPS.flatMap((group) => group.items);

/**
 * Shared placeholder for every authorized-but-not-yet-built module. The
 * Sidebar/Command already gate access by real RBAC before a User ever lands
 * here — this page just tells them the screen itself isn't built yet,
 * instead of a generic Next.js 404 or a fabricated CRUD screen with no data
 * behind it.
 */
export default function ModulePlaceholderPage({ params }: { params: { slug: string } }) {
  const item = ALL_ITEMS.find((candidate) => candidate.href === `/m/${params.slug}`);
  if (!item) notFound();

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">{item.label}</h1>
        <p className="text-sm text-muted-foreground">{item.description}</p>
      </div>
      <EmptyState
        icon={Construction}
        title="Módulo ainda não implementado"
        description="Esta tela chega em um lote posterior do Frontend (Sprint 12). O acesso já é controlado por RBAC real — você só vê este item porque tem a permissão para ele."
      />
    </div>
  );
}

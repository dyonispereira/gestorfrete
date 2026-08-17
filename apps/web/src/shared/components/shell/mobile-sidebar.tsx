"use client";

import * as React from "react";
import { Menu } from "lucide-react";

import { Button, Sheet, SheetContent, SheetTitle } from "@gestorfrete/ui";

import { NavContent } from "@/shared/components/shell/nav-content";
import { SidebarBrand } from "@/shared/components/shell/sidebar-brand";

/** Mobile navigation — a Sheet drawer, same content/tokens as the desktop Sidebar (D-consistent). */
export function MobileSidebar() {
  const [open, setOpen] = React.useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setOpen(true)} aria-label="Abrir menu">
        <Menu className="h-5 w-5" />
      </Button>
      <SheetContent
        side="left"
        className="flex w-sidebar-w flex-col gap-0 border-sidebar-border bg-sidebar p-0 text-sidebar-foreground [&_svg]:text-sidebar-foreground"
      >
        <SheetTitle className="sr-only">Navegação</SheetTitle>
        <SidebarBrand />
        <div className="flex-1 overflow-y-auto">
          <NavContent onNavigate={() => setOpen(false)} />
        </div>
      </SheetContent>
    </Sheet>
  );
}

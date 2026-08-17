import { ScrollArea } from "@gestorfrete/ui";

import { NavContent } from "@/shared/components/shell/nav-content";
import { SidebarBrand } from "@/shared/components/shell/sidebar-brand";

/** Desktop sidebar — always-dark navigation rail (`--sidebar-*` tokens), fixed width. */
export function Sidebar() {
  return (
    <aside className="hidden w-sidebar-w shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground lg:flex">
      <SidebarBrand />
      <ScrollArea className="flex-1">
        <NavContent />
      </ScrollArea>
    </aside>
  );
}

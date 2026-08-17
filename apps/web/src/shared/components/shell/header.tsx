import { MobileSidebar } from "@/shared/components/shell/mobile-sidebar";
import { BreadcrumbNav } from "@/shared/components/shell/breadcrumb-nav";
import { CommandMenu } from "@/shared/components/shell/command-menu";
import { UserMenu } from "@/shared/components/shell/user-menu";

export function Header() {
  return (
    <header className="sticky top-0 z-30 flex h-header-h shrink-0 items-center gap-3 border-b border-border bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80 sm:px-6">
      <MobileSidebar />
      <div className="hidden lg:block">
        <BreadcrumbNav />
      </div>
      <div className="flex flex-1 items-center justify-end gap-3">
        <CommandMenu />
        <UserMenu />
      </div>
    </header>
  );
}

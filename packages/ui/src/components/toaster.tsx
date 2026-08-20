"use client";

import { Toaster as SonnerToaster } from "sonner";

export { toast } from "sonner";

/**
 * Single mount point for feedback (create/edit/delete success/error) —
 * nothing in the app gave the User any confirmation before this Lote.
 * Styled via CSS variables already defined by `globals.css`, not
 * `sonner`'s own theme system.
 */
export function Toaster() {
  return (
    <SonnerToaster
      position="bottom-right"
      toastOptions={{
        classNames: {
          toast: "bg-popover text-popover-foreground border border-border shadow-popover",
          description: "text-muted-foreground",
          actionButton: "bg-primary text-primary-foreground",
          cancelButton: "bg-muted text-muted-foreground",
        },
      }}
    />
  );
}

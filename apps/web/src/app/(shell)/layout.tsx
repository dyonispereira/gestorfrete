import { RequireAuth } from "@/core/auth/require-auth";
import { AppShell } from "@/shared/components/shell/app-shell";

export default function ShellLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <AppShell>{children}</AppShell>
    </RequireAuth>
  );
}

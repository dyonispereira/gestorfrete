"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/core/auth/auth-provider";
import { LoadingState } from "@/shared/components/states/loading-state";

/**
 * Client-side route guard. Tokens live in `localStorage` (see
 * `token-storage.ts`), which Next.js middleware can't read — so protection
 * happens here, not in `middleware.ts`. `isAuthenticated` starts `null`
 * until the first client render resolves it, avoiding a false redirect
 * before we've actually checked.
 */
export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (isAuthenticated === false) router.replace("/login");
  }, [isAuthenticated, router]);

  if (isAuthenticated !== true) {
    return (
      <div className="flex h-dvh items-center justify-center bg-background p-6">
        <div className="w-full max-w-sm">
          <LoadingState rows={4} />
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

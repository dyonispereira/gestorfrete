"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/core/auth/auth-provider";
import { LoadingState } from "@/shared/components/states/loading-state";

export default function RootPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (isAuthenticated === true) router.replace("/dashboard");
    if (isAuthenticated === false) router.replace("/login");
  }, [isAuthenticated, router]);

  return (
    <div className="flex h-dvh items-center justify-center bg-background p-6">
      <div className="w-full max-w-sm">
        <LoadingState rows={3} />
      </div>
    </div>
  );
}

"use client";

import { useQuery } from "@tanstack/react-query";

import * as permissionsService from "@/modules/identity/services/permissions";
import type { Permission } from "@gestorfrete/types";

const MAX_PAGE_SIZE = 100;

async function fetchAllPermissions(): Promise<Permission[]> {
  const all: Permission[] = [];
  let page = 1;
  // The catalog (404 codes, seeded from RBAC_MATRIX.md) is small enough to load in full for the
  // Permissions screen and the Role permission matrix — both need the entire real universe of
  // codes, never a hardcoded subset, and the API caps `limit` at 100 (`PAGINATION.md`).
  for (;;) {
    const response = await permissionsService.listPermissions({ page, limit: MAX_PAGE_SIZE });
    all.push(...response.data);
    if (all.length >= response.meta.pagination.total || response.data.length === 0) break;
    page += 1;
  }
  return all;
}

/** Full permission catalog, every page concatenated — see `fetchAllPermissions`. */
export function useAllPermissionsQuery() {
  return useQuery({
    queryKey: ["permissions", "all"],
    queryFn: fetchAllPermissions,
    staleTime: 5 * 60_000,
  });
}

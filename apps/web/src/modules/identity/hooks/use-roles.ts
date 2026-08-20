"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as rolesService from "@/modules/identity/services/roles";
import type { CreateRoleRequest, UpdateRoleRequest } from "@gestorfrete/types";

export function useRolesQuery(params: rolesService.ListRolesParams) {
  return useQuery({
    queryKey: ["roles", "list", params],
    queryFn: () => rolesService.listRoles(params),
  });
}

/**
 * Query key here is exactly `["roles", roleId]` — the same key
 * `PermissionsProvider` (`core/rbac/permissions-provider.tsx`) uses to
 * resolve the current User's effective permissions. Every mutation below
 * invalidates it deliberately, so editing a Role's permissions takes effect
 * on the next request without a manual reload of stored permissions
 * (Sprint 12 Identity Lote, cenário 4).
 */
export function useRoleQuery(roleId: string | undefined) {
  return useQuery({
    queryKey: ["roles", roleId],
    queryFn: () => rolesService.getRole(roleId as string),
    enabled: Boolean(roleId),
  });
}

function useInvalidateRole(roleId: string) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ["roles", "list"] });
    queryClient.invalidateQueries({ queryKey: ["roles", roleId] });
  };
}

export function useCreateRoleMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateRoleRequest) => rolesService.createRole(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roles", "list"] });
    },
  });
}

export function useUpdateRoleMutation(roleId: string) {
  const invalidate = useInvalidateRole(roleId);
  return useMutation({
    mutationFn: (body: UpdateRoleRequest) => rolesService.updateRole(roleId, body),
    onSuccess: invalidate,
  });
}

export function useDeleteRoleMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (roleId: string) => rolesService.deleteRole(roleId),
    onSuccess: (_data, roleId) => {
      queryClient.invalidateQueries({ queryKey: ["roles", "list"] });
      queryClient.invalidateQueries({ queryKey: ["roles", roleId] });
    },
  });
}

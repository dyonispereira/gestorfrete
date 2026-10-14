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

export function useRoleQuery(roleId: string | undefined) {
  return useQuery({
    queryKey: ["roles", roleId],
    queryFn: () => rolesService.getRole(roleId as string),
    enabled: Boolean(roleId),
  });
}

/**
 * Invalidates both the Role's own cache entries and `["auth", "me"]` —
 * `PermissionsProvider` now reads its effective-permissions set from
 * `GET /auth/me` (RBAC structural fix), not from `GET /roles/{id}`, so a
 * Role edit/delete only reaches an already-logged-in User's menu/guards on
 * the next request if this session query is invalidated too (Sprint 12
 * Identity Lote, cenário 4).
 */
function useInvalidateRole(roleId: string) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ["roles", "list"] });
    queryClient.invalidateQueries({ queryKey: ["roles", roleId] });
    queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
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

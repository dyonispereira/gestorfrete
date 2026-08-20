"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as usersService from "@/modules/identity/services/users";
import type { CreateUserRequest, UpdateUserRequest } from "@gestorfrete/types";

export function useUsersQuery(params: usersService.ListUsersParams) {
  return useQuery({
    queryKey: ["users", params],
    queryFn: () => usersService.listUsers(params),
  });
}

export function useUserQuery(userId: string | undefined) {
  return useQuery({
    queryKey: ["users", userId],
    queryFn: () => usersService.getUser(userId as string),
    enabled: Boolean(userId),
  });
}

export function useCreateUserMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateUserRequest) => usersService.createUser(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });
}

export function useUpdateUserMutation(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: UpdateUserRequest) => usersService.updateUser(userId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      queryClient.invalidateQueries({ queryKey: ["users", userId] });
    },
  });
}

export function useDeactivateUserMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => usersService.deactivateUser(userId),
    onSuccess: (_data, userId) => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      queryClient.invalidateQueries({ queryKey: ["users", userId] });
    },
  });
}

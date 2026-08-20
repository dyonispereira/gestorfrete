import { apiFetch } from "@/shared/lib/api-client";
import type { CreateUserRequest, PaginatedResponse, UpdateUserRequest, User } from "@gestorfrete/types";

export interface ListUsersParams {
  page?: number;
  limit?: number;
  status?: string;
  role?: string;
  search?: string;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listUsers(params: ListUsersParams = {}): Promise<PaginatedResponse<User>> {
  return apiFetch<PaginatedResponse<User>>(`/users${toQuery(params)}`);
}

export function getUser(id: string): Promise<User> {
  return apiFetch<User>(`/users/${id}`);
}

export function createUser(body: CreateUserRequest): Promise<User> {
  return apiFetch<User>("/users", { method: "POST", body });
}

export function updateUser(id: string, body: UpdateUserRequest): Promise<User> {
  return apiFetch<User>(`/users/${id}`, { method: "PATCH", body });
}

export function deactivateUser(id: string): Promise<void> {
  return apiFetch<void>(`/users/${id}`, { method: "DELETE" });
}

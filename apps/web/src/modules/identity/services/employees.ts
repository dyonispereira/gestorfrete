import { apiFetch } from "@/shared/lib/api-client";
import type { CreateEmployeeRequest, Employee, PaginatedResponse, UpdateEmployeeRequest } from "@gestorfrete/types";

export interface ListEmployeesParams {
  page?: number;
  limit?: number;
  status?: string;
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

export function listEmployees(params: ListEmployeesParams = {}): Promise<PaginatedResponse<Employee>> {
  return apiFetch<PaginatedResponse<Employee>>(`/employees${toQuery(params)}`);
}

export function getEmployee(id: string): Promise<Employee> {
  return apiFetch<Employee>(`/employees/${id}`);
}

export function createEmployee(body: CreateEmployeeRequest): Promise<Employee> {
  return apiFetch<Employee>("/employees", { method: "POST", body });
}

export function updateEmployee(id: string, body: UpdateEmployeeRequest): Promise<Employee> {
  return apiFetch<Employee>(`/employees/${id}`, { method: "PATCH", body });
}

export function deleteEmployee(id: string): Promise<void> {
  return apiFetch<void>(`/employees/${id}`, { method: "DELETE" });
}

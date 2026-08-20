"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as employeesService from "@/modules/identity/services/employees";
import type { CreateEmployeeRequest, UpdateEmployeeRequest } from "@gestorfrete/types";

export function useEmployeesQuery(params: employeesService.ListEmployeesParams) {
  return useQuery({
    queryKey: ["employees", "list", params],
    queryFn: () => employeesService.listEmployees(params),
  });
}

export function useEmployeeQuery(employeeId: string | undefined) {
  return useQuery({
    queryKey: ["employees", employeeId],
    queryFn: () => employeesService.getEmployee(employeeId as string),
    enabled: Boolean(employeeId),
  });
}

export function useCreateEmployeeMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateEmployeeRequest) => employeesService.createEmployee(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["employees", "list"] }),
  });
}

export function useUpdateEmployeeMutation(employeeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: UpdateEmployeeRequest) => employeesService.updateEmployee(employeeId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["employees", "list"] });
      queryClient.invalidateQueries({ queryKey: ["employees", employeeId] });
    },
  });
}

export function useDeleteEmployeeMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (employeeId: string) => employeesService.deleteEmployee(employeeId),
    onSuccess: (_data, employeeId) => {
      queryClient.invalidateQueries({ queryKey: ["employees", "list"] });
      queryClient.invalidateQueries({ queryKey: ["employees", employeeId] });
    },
  });
}

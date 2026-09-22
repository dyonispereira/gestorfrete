"use client";

import { useQuery } from "@tanstack/react-query";

import * as managementResultsService from "@/modules/analytics/services/management-results";
import type { PeriodParams } from "@/modules/analytics/services/management-results";

export function useOverviewQuery(period: PeriodParams) {
  return useQuery({
    queryKey: ["management-results", "visao-geral", period],
    queryFn: () => managementResultsService.getOverview(period),
  });
}

export function useTripResultsQuery(params: managementResultsService.ListTripResultsParams) {
  return useQuery({
    queryKey: ["management-results", "viagens", params],
    queryFn: () => managementResultsService.listTripResults(params),
  });
}

export function useVehicleResultsQuery(period: PeriodParams) {
  return useQuery({
    queryKey: ["management-results", "veiculos", period],
    queryFn: () => managementResultsService.listVehicleResults(period),
  });
}

export function useVehicleResultDetailQuery(vehicleId: string | undefined, period: PeriodParams) {
  return useQuery({
    queryKey: ["management-results", "veiculos", vehicleId, period],
    queryFn: () => managementResultsService.getVehicleResultDetail(vehicleId as string, period),
    enabled: Boolean(vehicleId),
  });
}

export function useClientResultsQuery(period: PeriodParams) {
  return useQuery({
    queryKey: ["management-results", "clientes", period],
    queryFn: () => managementResultsService.listClientResults(period),
  });
}

export function useClientResultDetailQuery(clientId: string | undefined, period: PeriodParams) {
  return useQuery({
    queryKey: ["management-results", "clientes", clientId, period],
    queryFn: () => managementResultsService.getClientResultDetail(clientId as string, period),
    enabled: Boolean(clientId),
  });
}

export function useDriverResultsQuery(period: PeriodParams) {
  return useQuery({
    queryKey: ["management-results", "motoristas", period],
    queryFn: () => managementResultsService.listDriverResults(period),
  });
}

export function useDriverResultDetailQuery(driverId: string | undefined, period: PeriodParams) {
  return useQuery({
    queryKey: ["management-results", "motoristas", driverId, period],
    queryFn: () => managementResultsService.getDriverResultDetail(driverId as string, period),
    enabled: Boolean(driverId),
  });
}

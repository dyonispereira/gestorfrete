"use client";

import { Badge, Button, Table, TableBody, TableCell, TableHead, TableHeader, TableRow, toast } from "@gestorfrete/ui";
import type { VehicleCategory, VehicleCategoryStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useUpdateVehicleCategoryMutation } from "@/modules/fleet/hooks/use-vehicle-categories";
import { ApiError } from "@/shared/lib/api-client";

const VARIANT_BY_STATUS: Record<VehicleCategoryStatus, "success" | "secondary"> = {
  ATIVA: "success",
  INATIVA: "secondary",
};
const LABEL_BY_STATUS: Record<VehicleCategoryStatus, string> = { ATIVA: "Ativa", INATIVA: "Inativa" };

function ToggleStatusButton({ category }: { category: VehicleCategory }) {
  const { hasPermission } = usePermissions();
  const update = useUpdateVehicleCategoryMutation(category.id);

  if (!hasPermission("fleet.vehicle_category.edit")) return null;

  const nextStatus: VehicleCategoryStatus = category.status === "ATIVA" ? "INATIVA" : "ATIVA";

  async function handleToggle() {
    try {
      await update.mutateAsync({ status: nextStatus });
      toast.success(nextStatus === "ATIVA" ? "Categoria ativada." : "Categoria desativada.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível atualizar a categoria.");
    }
  }

  return (
    <Button size="sm" variant="outline" disabled={update.isPending} onClick={() => handleToggle()}>
      {category.status === "ATIVA" ? "Desativar" : "Ativar"}
    </Button>
  );
}

export function VehicleCategoriesTable({ categories }: { categories: VehicleCategory[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Nome</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Ações</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {categories.map((category) => (
          <TableRow key={category.id}>
            <TableCell className="font-medium">{category.nome}</TableCell>
            <TableCell>
              <Badge variant={VARIANT_BY_STATUS[category.status]}>{LABEL_BY_STATUS[category.status]}</Badge>
            </TableCell>
            <TableCell className="text-right">
              <ToggleStatusButton category={category} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

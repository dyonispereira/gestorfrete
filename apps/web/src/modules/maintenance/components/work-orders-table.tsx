import Link from "next/link";
import { Wrench } from "lucide-react";

import { Badge, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { WorkOrder, WorkOrderType } from "@gestorfrete/types";

import { WorkOrderStatusBadge } from "./work-order-status-badge";

const TYPE_LABEL: Record<WorkOrderType, string> = {
  PREVENTIVA: "Preventiva",
  CORRETIVA: "Corretiva",
  EMERGENCIAL: "Emergencial",
  GARANTIA: "Garantia",
};

export function WorkOrdersTable({ workOrders }: { workOrders: WorkOrder[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Código</TableHead>
          <TableHead>Tipo</TableHead>
          <TableHead>Origem</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {workOrders.map((workOrder) => (
          <TableRow key={workOrder.id}>
            <TableCell className="font-medium">
              <Link href={`/ordens-servico/${workOrder.id}`} className="flex items-center gap-2 hover:underline">
                <Wrench className="h-4 w-4 text-muted-foreground" />
                {workOrder.codigo}
              </Link>
            </TableCell>
            <TableCell>
              <Badge variant="outline">{TYPE_LABEL[workOrder.type]}</Badge>
            </TableCell>
            <TableCell className="text-muted-foreground">{workOrder.opening_origin}</TableCell>
            <TableCell>
              <WorkOrderStatusBadge status={workOrder.status} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

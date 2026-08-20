import Link from "next/link";

import { Badge, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { CostCenter, CostCenterStatus } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<CostCenterStatus, "success" | "secondary"> = { ATIVO: "success", INATIVO: "secondary" };
const LABEL_BY_STATUS: Record<CostCenterStatus, string> = { ATIVO: "Ativo", INATIVO: "Inativo" };

export function CostCentersTable({ costCenters }: { costCenters: CostCenter[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Nome</TableHead>
          <TableHead>Código contábil</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {costCenters.map((costCenter) => (
          <TableRow key={costCenter.id}>
            <TableCell className="font-medium">
              <Link href={`/centros-custo/${costCenter.id}`} className="hover:underline">
                {costCenter.nome}
              </Link>
            </TableCell>
            <TableCell className="text-muted-foreground">{costCenter.accounting_code}</TableCell>
            <TableCell>
              <Badge variant={VARIANT_BY_STATUS[costCenter.status]}>{LABEL_BY_STATUS[costCenter.status]}</Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

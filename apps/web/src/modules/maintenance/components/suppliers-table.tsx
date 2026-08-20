import Link from "next/link";

import { Badge, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { Supplier } from "@gestorfrete/types";

import { SupplierStatusBadge } from "./supplier-status-badge";
import { SUPPLIER_CATEGORY_LABEL } from "./supplier-category-label";

export function SuppliersTable({ suppliers }: { suppliers: Supplier[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Razão Social</TableHead>
          <TableHead>CNPJ</TableHead>
          <TableHead>Categoria</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {suppliers.map((supplier) => (
          <TableRow key={supplier.id}>
            <TableCell className="font-medium">
              <Link href={`/fornecedores/${supplier.id}`} className="hover:underline">
                {supplier.razao_social}
              </Link>
            </TableCell>
            <TableCell className="text-muted-foreground">{supplier.cnpj}</TableCell>
            <TableCell>{supplier.category ? <Badge variant="outline">{SUPPLIER_CATEGORY_LABEL[supplier.category]}</Badge> : "—"}</TableCell>
            <TableCell>
              <SupplierStatusBadge status={supplier.status} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

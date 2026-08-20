import Link from "next/link";

import { Badge, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@gestorfrete/ui";
import type { Employee, EmployeeStatus } from "@gestorfrete/types";

const VARIANT_BY_STATUS: Record<EmployeeStatus, "success" | "secondary"> = { ATIVO: "success", INATIVO: "secondary" };
const LABEL_BY_STATUS: Record<EmployeeStatus, string> = { ATIVO: "Ativo", INATIVO: "Inativo" };

/** Leanest Cadastros entity — really has no phone/email/CPF, so the table doesn't show any. */
export function EmployeesTable({ employees }: { employees: Employee[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Nome</TableHead>
          <TableHead>Cargo</TableHead>
          <TableHead>Admissão</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {employees.map((employee) => (
          <TableRow key={employee.id}>
            <TableCell className="font-medium">
              <Link href={`/funcionarios/${employee.id}`} className="hover:underline">
                {employee.nome}
              </Link>
            </TableCell>
            <TableCell className="text-muted-foreground">{employee.cargo}</TableCell>
            <TableCell className="text-muted-foreground">{employee.hired_at ?? "—"}</TableCell>
            <TableCell>
              <Badge variant={VARIANT_BY_STATUS[employee.status]}>{LABEL_BY_STATUS[employee.status]}</Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

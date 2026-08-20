"use client";

import * as React from "react";

import {
  Badge,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@gestorfrete/ui";

import { useAllPermissionsQuery } from "@/modules/identity/hooks/use-permissions-catalog";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

/**
 * Catálogo somente leitura de `GET /permissions` — organiza e apresenta,
 * nunca inventa um código. Todo agrupamento/filtro é derivado do que a API
 * já retorna (`module`), nunca de uma lista escrita neste arquivo.
 */
export function PermissionsCatalogTable() {
  const [search, setSearch] = React.useState("");
  const [moduleFilter, setModuleFilter] = React.useState<string>("all");

  const catalogQuery = useAllPermissionsQuery();

  const modules = React.useMemo(() => {
    const set = new Set((catalogQuery.data ?? []).map((permission) => permission.module));
    return Array.from(set).sort();
  }, [catalogQuery.data]);

  const filtered = React.useMemo(() => {
    const term = search.trim().toLowerCase();
    return (catalogQuery.data ?? []).filter((permission) => {
      if (moduleFilter !== "all" && permission.module !== moduleFilter) return false;
      if (!term) return true;
      return permission.code.toLowerCase().includes(term) || permission.name.toLowerCase().includes(term);
    });
  }, [catalogQuery.data, search, moduleFilter]);

  if (catalogQuery.isLoading) return <LoadingState rows={8} />;
  if (catalogQuery.error)
    return (
      <ErrorState description="Não foi possível carregar o catálogo de permissões." onRetry={() => catalogQuery.refetch()} />
    );

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          placeholder="Buscar por código ou nome…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="sm:max-w-xs"
        />
        <Select value={moduleFilter} onValueChange={setModuleFilter}>
          <SelectTrigger className="sm:w-56">
            <SelectValue placeholder="Todos os módulos" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os módulos</SelectItem>
            {modules.map((module) => (
              <SelectItem key={module} value={module}>
                {module}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {filtered.length === 0 ? (
        <EmptyState title="Nenhuma permissão encontrada" description="Ajuste a busca ou o filtro de módulo." />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Código</TableHead>
              <TableHead>Nome</TableHead>
              <TableHead>Módulo</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((permission) => (
              <TableRow key={permission.id}>
                <TableCell className="font-mono text-xs text-muted-foreground">{permission.code}</TableCell>
                <TableCell>{permission.name}</TableCell>
                <TableCell>
                  <Badge variant="outline">{permission.module}</Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}

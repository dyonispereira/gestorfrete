import { PermissionsCatalogTable } from "@/modules/identity/components/permissions-catalog-table";

export default function PermissionsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Permissões</h1>
        <p className="text-sm text-muted-foreground">
          Catálogo somente leitura — atribua permissões a um Papel em <span className="font-mono">/papeis</span>.
        </p>
      </div>
      <PermissionsCatalogTable />
    </div>
  );
}

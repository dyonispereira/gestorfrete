import { FiscalEventsTable } from "@/modules/documents/components/fiscal-events-table";

export default function FiscalEventsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Eventos Fiscais</h1>
        <p className="text-sm text-muted-foreground">
          Log técnico das integrações com SEFAZ/ANTT — consulta somente leitura, sem ação de &ldquo;consultar agora&rdquo;.
        </p>
      </div>

      <FiscalEventsTable />
    </div>
  );
}

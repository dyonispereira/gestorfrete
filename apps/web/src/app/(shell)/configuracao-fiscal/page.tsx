import { FiscalConfigurationForm } from "@/modules/documents/components/fiscal-configuration-form";

export default function FiscalConfigurationPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Configuração Fiscal</h1>
        <p className="text-sm text-muted-foreground">
          Fonte única de numeração de CT-e/MDF-e. Cada seção só é editável com a permissão específica.
        </p>
      </div>

      <FiscalConfigurationForm />
    </div>
  );
}

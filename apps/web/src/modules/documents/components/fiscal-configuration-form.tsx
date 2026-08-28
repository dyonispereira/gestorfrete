"use client";

import * as React from "react";

import {
  Badge,
  Button,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  toast,
} from "@gestorfrete/ui";
import type { FiscalConfigurationEnvironment } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useFiscalConfigurationQuery, useUpdateFiscalConfigurationMutation } from "@/modules/documents/hooks/use-fiscal-configuration";
import { ApiError } from "@/shared/lib/api-client";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

/**
 * `PATCH` exige permissão por campo (D267-style) — um campo enviado sem a permissão rejeita a
 * requisição inteira, nunca um PATCH parcial. Cada grupo aqui é desabilitado (não escondido, o
 * valor atual ainda precisa ser visível) quando o ator não tem a permissão correspondente:
 * `tax_regime`→`.edit`; `certificate_expires_at`→`.manage_certificate`; `cte_series`/
 * `mdfe_series`→`.manage_series`; `environment`→`.switch_environment`. Cada grupo é salvo com seu
 * próprio botão, para nunca enviar um campo desabilitado no mesmo PATCH de um habilitado.
 */
export function FiscalConfigurationForm() {
  const { hasPermission } = usePermissions();
  const configQuery = useFiscalConfigurationQuery();
  const update = useUpdateFiscalConfigurationMutation();

  const canEditRegime = hasPermission("documents.fiscal_config.edit");
  const canManageCertificate = hasPermission("documents.fiscal_config.manage_certificate");
  const canManageSeries = hasPermission("documents.fiscal_config.manage_series");
  const canSwitchEnvironment = hasPermission("documents.fiscal_config.switch_environment");

  const [taxRegime, setTaxRegime] = React.useState("");
  const [certificateExpiresAt, setCertificateExpiresAt] = React.useState("");
  const [cteSeries, setCteSeries] = React.useState("");
  const [mdfeSeries, setMdfeSeries] = React.useState("");
  const [environment, setEnvironment] = React.useState<FiscalConfigurationEnvironment>("HOMOLOGACAO");

  React.useEffect(() => {
    const config = configQuery.data;
    if (!config) return;
    setTaxRegime(config.tax_regime);
    setCertificateExpiresAt(config.certificate_expires_at);
    setCteSeries(config.cte_series);
    setMdfeSeries(config.mdfe_series);
    setEnvironment(config.environment);
  }, [configQuery.data]);

  async function saveField(body: Parameters<typeof update.mutateAsync>[0], successMessage: string) {
    try {
      await update.mutateAsync(body);
      toast.success(successMessage);
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Não foi possível salvar.");
    }
  }

  if (configQuery.isLoading) return <LoadingState rows={5} />;
  if (configQuery.error || !configQuery.data)
    return (
      <ErrorState
        title="Não foi possível carregar a Configuração Fiscal"
        description={configQuery.error instanceof Error ? configQuery.error.message : undefined}
        onRetry={() => configQuery.refetch()}
      />
    );

  const config = configQuery.data;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3 rounded-md border border-border p-4 text-sm">
        <span className="text-muted-foreground">Próximo número CT-e</span>
        <Badge variant="outline">{config.next_cte_number}</Badge>
        <span className="text-muted-foreground">Próximo número MDF-e</span>
        <Badge variant="outline">{config.next_mdfe_number}</Badge>
        <span className="text-muted-foreground">Status</span>
        <Badge variant={config.status === "ATIVA" ? "success" : "secondary"}>{config.status}</Badge>
      </div>

      <div className="flex flex-col gap-3 rounded-md border border-border p-4">
        <Label htmlFor="fiscal-config-tax-regime">Regime tributário</Label>
        <div className="flex gap-2">
          <Input
            id="fiscal-config-tax-regime"
            disabled={!canEditRegime}
            value={taxRegime}
            onChange={(event) => setTaxRegime(event.target.value)}
          />
          {canEditRegime ? (
            <Button
              disabled={update.isPending}
              onClick={() => saveField({ tax_regime: taxRegime }, "Regime tributário atualizado.")}
            >
              Salvar regime tributário
            </Button>
          ) : null}
        </div>
      </div>

      <div className="flex flex-col gap-3 rounded-md border border-border p-4">
        <Label htmlFor="fiscal-config-certificate-expires">Validade do certificado digital</Label>
        <div className="flex gap-2">
          <Input
            id="fiscal-config-certificate-expires"
            type="date"
            disabled={!canManageCertificate}
            value={certificateExpiresAt}
            onChange={(event) => setCertificateExpiresAt(event.target.value)}
          />
          {canManageCertificate ? (
            <Button
              disabled={update.isPending}
              onClick={() => saveField({ certificate_expires_at: certificateExpiresAt }, "Certificado atualizado.")}
            >
              Salvar certificado
            </Button>
          ) : null}
        </div>
      </div>

      <div className="flex flex-col gap-3 rounded-md border border-border p-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="fiscal-config-cte-series">Série CT-e</Label>
            <Input
              id="fiscal-config-cte-series"
              disabled={!canManageSeries}
              value={cteSeries}
              onChange={(event) => setCteSeries(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="fiscal-config-mdfe-series">Série MDF-e</Label>
            <Input
              id="fiscal-config-mdfe-series"
              disabled={!canManageSeries}
              value={mdfeSeries}
              onChange={(event) => setMdfeSeries(event.target.value)}
            />
          </div>
        </div>
        {canManageSeries ? (
          <Button
            disabled={update.isPending}
            className="self-start"
            onClick={() => saveField({ cte_series: cteSeries, mdfe_series: mdfeSeries }, "Séries atualizadas.")}
          >
            Salvar séries
          </Button>
        ) : null}
      </div>

      <div className="flex flex-col gap-3 rounded-md border border-border p-4">
        <Label htmlFor="fiscal-config-environment">Ambiente</Label>
        <div className="flex gap-2">
          <Select
            value={environment}
            onValueChange={(value) => setEnvironment(value as FiscalConfigurationEnvironment)}
            disabled={!canSwitchEnvironment}
          >
            <SelectTrigger id="fiscal-config-environment" className="max-w-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="HOMOLOGACAO">Homologação</SelectItem>
              <SelectItem value="PRODUCAO">Produção</SelectItem>
            </SelectContent>
          </Select>
          {canSwitchEnvironment ? (
            <Button disabled={update.isPending} onClick={() => saveField({ environment }, "Ambiente atualizado.")}>
              Salvar ambiente
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

-- E2E fixtures for Sprint 14 — Frontend, Lote Documentos Fiscais (apps/web/e2e/fiscal.spec.ts).
-- Same mechanism as every prior lote's seed. A CT-e can never come into existence through the UI
-- at all in this environment — it's only auto-created by `DispatchTripHandler` on trip dispatch
-- (D396), and dispatch itself needs `LIBERADA`, already proven unreachable via the UI in the
-- Operação lote (no Checklist module yet). So this seed inserts `ctes` rows directly — a stronger
-- version of the same `categorias_veiculo`-style gap, not a new kind of problem. One CT-e is
-- seeded already `AUTORIZADO` (with `protocolo_sefaz`/`chave_acesso`/`data_hora_autorizacao` set,
-- mirroring exactly what `FiscalInternalTransitions.receive_cte_sefaz_response` would have
-- written) so `cancelar`, Carta de Correção and MDF-e creation have something real to operate on.
-- `configuracoes_fiscais_tenant.certificado_validade` is set in the future so `commands/sign`
-- doesn't 409 `FISCAL_CERTIFICATE_EXPIRED`. Password for both users is "Senha123!" (same bcrypt
-- hash used throughout this session).

BEGIN;

DELETE FROM sessoes_acesso WHERE tenant_id = 'fca10000-0000-0000-0000-000000000001';
DELETE FROM usuarios_papeis WHERE usuario_id IN ('fca10000-0000-0000-0000-000000001a01', 'fca10000-0000-0000-0000-000000001a02');
DELETE FROM papel_permissao WHERE papel_id IN ('fca10000-0000-0000-0000-0000000000a1', 'fca10000-0000-0000-0000-0000000000a2');
DELETE FROM eventos_fiscais WHERE tenant_id = 'fca10000-0000-0000-0000-000000000001';
DELETE FROM cartas_correcao WHERE tenant_id = 'fca10000-0000-0000-0000-000000000001';
DELETE FROM nfe_referenciadas WHERE tenant_id = 'fca10000-0000-0000-0000-000000000001';
DELETE FROM ctes_status_history WHERE tenant_id = 'fca10000-0000-0000-0000-000000000001';
DELETE FROM mdfes_ctes WHERE mdfe_id IN (SELECT id FROM mdfes WHERE tenant_id = 'fca10000-0000-0000-0000-000000000001');
DELETE FROM mdfes_status_history WHERE tenant_id = 'fca10000-0000-0000-0000-000000000001';
DELETE FROM mdfes WHERE tenant_id = 'fca10000-0000-0000-0000-000000000001';
DELETE FROM ctes WHERE tenant_id = 'fca10000-0000-0000-0000-000000000001';
DELETE FROM configuracoes_fiscais_tenant WHERE tenant_id = 'fca10000-0000-0000-0000-000000000001';
-- `cancel_cte`/`close_mdfe` chamam `TripInternalTransitions.record_fiscal_transition`, que grava
-- uma linha em `viagem_status_history` (dimensão FISCAL) na Viagem semeada — precisa ser limpa
-- antes de excluir a própria Viagem, mesmo sem nenhuma Viagem ter sido tocada pela UI diretamente.
DELETE FROM viagem_status_history WHERE viagem_id = 'fca10000-0000-0000-0000-0000000000d1';
DELETE FROM viagens WHERE tenant_id = 'fca10000-0000-0000-0000-000000000001';
DELETE FROM clientes WHERE tenant_id = 'fca10000-0000-0000-0000-000000000001';
DELETE FROM usuarios WHERE tenant_id = 'fca10000-0000-0000-0000-000000000001';
DELETE FROM papeis WHERE tenant_id = 'fca10000-0000-0000-0000-000000000001';
DELETE FROM tenants WHERE id = 'fca10000-0000-0000-0000-000000000001';

INSERT INTO tenants (id, codigo, versao, razao_social, cnpj, status, criado_em, atualizado_em)
VALUES ('fca10000-0000-0000-0000-000000000001', 'E2EFISCAL', 1, 'E2E Fiscal Tenant', '99999999000100', 'ATIVO', now(), now());

INSERT INTO papeis (id, tenant_id, codigo, versao, nome, descricao, criado_em, atualizado_em)
VALUES
  ('fca10000-0000-0000-0000-0000000000a1', 'fca10000-0000-0000-0000-000000000001', 'E2EFISCALADM', 1, 'E2E Fiscal Admin', 'Acesso total a Documentos Fiscais', now(), now()),
  ('fca10000-0000-0000-0000-0000000000a2', 'fca10000-0000-0000-0000-000000000001', 'E2EFISCALVIEWER', 1, 'E2E Fiscal Viewer', 'Só visualiza Configuração Fiscal — sem nenhuma permissão de edição', now(), now());

-- `freight.trip.view` além de `documents.*`: o formulário de criação de MDF-e usa o mesmo picker
-- de Viagens do módulo `freight` (reuso deliberado, não duplicação) para escolher a qual viagem o
-- MDF-e pertence — sem essa permissão o `GET /viagens` do picker retorna 403 silenciosamente.
INSERT INTO papel_permissao (papel_id, permissao_id, criado_em)
SELECT 'fca10000-0000-0000-0000-0000000000a1', id, now() FROM permissoes
WHERE modulo = 'documents' OR codigo IN ('identity_access.role.view', 'freight.trip.view');

INSERT INTO papel_permissao (papel_id, permissao_id, criado_em)
SELECT 'fca10000-0000-0000-0000-0000000000a2', id, now() FROM permissoes
WHERE codigo IN ('documents.fiscal_config.view', 'identity_access.role.view');

INSERT INTO usuarios (id, tenant_id, codigo, versao, nome, email, senha_hash, status, criado_em, atualizado_em)
VALUES
  ('fca10000-0000-0000-0000-000000001a01', 'fca10000-0000-0000-0000-000000000001', 'E2EFISCALADM', 1, 'E2E Fiscal Admin', 'fiscal-admin@e2e-fixture.com', '$2b$12$YyD1R8sQEQKMbsoX2Y9m8OrU59qzoa8TCeQIINO4i0yiVetxHshve', 'ATIVO', now(), now()),
  ('fca10000-0000-0000-0000-000000001a02', 'fca10000-0000-0000-0000-000000000001', 'E2EFISCALVIEWER', 1, 'E2E Fiscal Viewer', 'fiscal-viewer@e2e-fixture.com', '$2b$12$YyD1R8sQEQKMbsoX2Y9m8OrU59qzoa8TCeQIINO4i0yiVetxHshve', 'ATIVO', now(), now());

INSERT INTO usuarios_papeis (usuario_id, papel_id, criado_em)
VALUES
  ('fca10000-0000-0000-0000-000000001a01', 'fca10000-0000-0000-0000-0000000000a1', now()),
  ('fca10000-0000-0000-0000-000000001a02', 'fca10000-0000-0000-0000-0000000000a2', now());

INSERT INTO clientes (id, tenant_id, codigo, versao, razao_social, cnpj_cpf, status, criado_em, atualizado_em)
VALUES ('fca10000-0000-0000-0000-0000000000c1', 'fca10000-0000-0000-0000-000000000001', 'E2EFISCALCLI', 1, 'E2E Fiscal Cliente', '11222333000144', 'ATIVO', now(), now());

INSERT INTO viagens (id, tenant_id, codigo, versao, cliente_id, status_operacional, status_fiscal, status_financeiro, criado_em, atualizado_em)
VALUES ('fca10000-0000-0000-0000-0000000000d1', 'fca10000-0000-0000-0000-000000000001', 'VG-E2EFISCAL-001', 1, 'fca10000-0000-0000-0000-0000000000c1', 'RASCUNHO', 'PENDENTE', 'AGUARDANDO_FATURAMENTO', now(), now());

INSERT INTO configuracoes_fiscais_tenant (id, tenant_id, certificado_arquivo_id, certificado_validade, ambiente, regime_tributario, serie_cte, proximo_numero_cte, serie_mdfe, proximo_numero_mdfe, status)
VALUES ('fca10000-0000-0000-0000-0000000000e1', 'fca10000-0000-0000-0000-000000000001', 'fca10000-0000-0000-0000-0000000000f1', '2035-12-31', 'HOMOLOGACAO', 'SIMPLES_NACIONAL', '1', 3, '1', 1, 'ATIVA');

-- CT-e #1 (RASCUNHO) — dirige a cadeia validar → assinar → transmitir.
INSERT INTO ctes (id, tenant_id, viagem_id, numero, serie, valor_servico, status, criado_em, atualizado_em)
VALUES ('fca10000-0000-0000-0000-000000001c01', 'fca10000-0000-0000-0000-000000000001', 'fca10000-0000-0000-0000-0000000000d1', '1001', '1', 1500.00, 'RASCUNHO', now(), now());

-- CT-e #2 (RASCUNHO) — dirige o ramo separado de inutilizar.
INSERT INTO ctes (id, tenant_id, viagem_id, numero, serie, valor_servico, status, criado_em, atualizado_em)
VALUES ('fca10000-0000-0000-0000-000000001c02', 'fca10000-0000-0000-0000-000000000001', 'fca10000-0000-0000-0000-0000000000d1', '1002', '1', 1500.00, 'RASCUNHO', now(), now());

-- CT-e #3 (AUTORIZADO, semeado diretamente) — dirige cancelar, Carta de Correção e criação de MDF-e.
INSERT INTO ctes (id, tenant_id, viagem_id, numero, serie, chave_acesso, valor_servico, status, protocolo_sefaz, data_hora_autorizacao, criado_em, atualizado_em)
VALUES ('fca10000-0000-0000-0000-000000001c03', 'fca10000-0000-0000-0000-000000000001', 'fca10000-0000-0000-0000-0000000000d1', '1003', '1', '35260800000000000001550010000000031000000031', 2500.00, 'AUTORIZADO', 'SEED-PROTO-0003', now(), now(), now());

COMMIT;

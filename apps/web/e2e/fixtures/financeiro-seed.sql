-- E2E fixtures for Sprint 15 — Lote Financeiro, Parte 2 (Frontend). Mesmo mecanismo de todo Lote
-- anterior. Precisa do conjunto completo: freight+crm+drivers+fleet+maintenance+documents (montar
-- e despachar a viagem, fechar a OS) + financial (todo o resto desta Lote). Dois usuários: um
-- admin completo, e um "financeiro-limitado" (só financial.payable.view) para provar que uma ação
-- sem permissão é barrada pelo backend, não só escondida na UI. `categorias_veiculo` e
-- `formas_pagamento` ainda sem endpoint HTTP (D363/D386) — seed direto via SQL, mesmo padrão já
-- usado em toda Lote anterior. Password é "Senha123!" (mesmo hash bcrypt de toda a sessão).

BEGIN;

DELETE FROM sessoes_acesso WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM usuarios_papeis WHERE usuario_id IN ('f14a0000-0000-0000-0000-000000001a01', 'f14a0000-0000-0000-0000-000000001a02');
DELETE FROM papel_permissao WHERE papel_id IN ('f14a0000-0000-0000-0000-0000000000a1', 'f14a0000-0000-0000-0000-0000000000a2');
DELETE FROM estornos_financeiros WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM contas_receber_status_history WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM contas_receber WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM faturas WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM rateios_despesa WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM aprovacoes_despesa WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM contas_pagar_status_history WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM contas_pagar WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM contas_bancarias WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM aprovacoes_custo WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM itens_ordem_servico WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM ordens_servico_status_history WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM ordens_servico WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM plano_contas WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM centros_custo WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM formas_pagamento WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM checklists_status_history WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM checklists WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM canhotos WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM janelas_entrega WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM entregas WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM eventos_fiscais WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM ctes_status_history WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM ctes WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM configuracoes_fiscais_tenant WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM alocacoes_recurso_viagem WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM viagem_status_history WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM viagens WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM veiculo_impedimentos WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM disponibilidade_veiculo WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM leituras_hodometro WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM veiculos_tracionadores WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM fornecedores WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM motoristas WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM clientes WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM usuarios WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM papeis WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM categorias_veiculo WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000001';
DELETE FROM tenants WHERE id = 'f14a0000-0000-0000-0000-000000000001';

INSERT INTO tenants (id, codigo, versao, razao_social, cnpj, status, criado_em, atualizado_em)
VALUES ('f14a0000-0000-0000-0000-000000000001', 'E2EFIN', 1, 'E2E Financeiro Tenant', '88999000000111', 'ATIVO', now(), now());

INSERT INTO categorias_veiculo (id, tenant_id, codigo, nome, status, criado_em, atualizado_em)
VALUES ('f14a0000-0000-0000-0000-0000000000c1', 'f14a0000-0000-0000-0000-000000000001', 'E2ECAT', 'E2E Categoria', 'ATIVA', now(), now());

INSERT INTO formas_pagamento (id, tenant_id, nome, status)
VALUES ('f14a0000-0000-0000-0000-0000000000f1', 'f14a0000-0000-0000-0000-000000000001', 'PIX', 'ATIVA');

-- Necessária para o CT-e ser criado de verdade no despacho (`reserve_next_cte_number`).
INSERT INTO configuracoes_fiscais_tenant (id, tenant_id, certificado_arquivo_id, certificado_validade, ambiente, regime_tributario, serie_cte, proximo_numero_cte, serie_mdfe, proximo_numero_mdfe, status)
VALUES ('f14a0000-0000-0000-0000-0000000000f2', 'f14a0000-0000-0000-0000-000000000001', 'f14a0000-0000-0000-0000-0000000000f3', '2035-12-31', 'HOMOLOGACAO', 'SIMPLES_NACIONAL', '1', 1, '1', 1, 'ATIVA');

INSERT INTO papeis (id, tenant_id, codigo, versao, nome, descricao, criado_em, atualizado_em)
VALUES
  ('f14a0000-0000-0000-0000-0000000000a1', 'f14a0000-0000-0000-0000-000000000001', 'E2EFINADM', 1, 'E2E Financeiro Admin', 'Acesso total ao ciclo OS->CP e Viagem->Fatura->CR', now(), now()),
  ('f14a0000-0000-0000-0000-0000000000a2', 'f14a0000-0000-0000-0000-000000000001', 'E2EFINLIMITADO', 1, 'E2E Financeiro Limitado', 'Só visualiza Contas a Pagar — prova de bloqueio real de autorização', now(), now());

INSERT INTO papel_permissao (papel_id, permissao_id, criado_em)
SELECT 'f14a0000-0000-0000-0000-0000000000a1', id, now() FROM permissoes
WHERE modulo IN ('freight', 'crm', 'drivers', 'fleet', 'maintenance', 'documents', 'financial')
   OR codigo LIKE 'storage.%'
   OR codigo LIKE 'financial.trip_%.view'
   OR codigo IN ('identity_access.role.view', 'identity_access.user.view');

INSERT INTO papel_permissao (papel_id, permissao_id, criado_em)
SELECT 'f14a0000-0000-0000-0000-0000000000a2', id, now() FROM permissoes
WHERE codigo IN ('financial.payable.view', 'identity_access.role.view');

INSERT INTO usuarios (id, tenant_id, codigo, versao, nome, email, senha_hash, status, criado_em, atualizado_em)
VALUES
  ('f14a0000-0000-0000-0000-000000001a01', 'f14a0000-0000-0000-0000-000000000001', 'E2EFINADM', 1, 'E2E Financeiro Admin', 'financeiro-admin@e2e-fixture.com', '$2b$12$YyD1R8sQEQKMbsoX2Y9m8OrU59qzoa8TCeQIINO4i0yiVetxHshve', 'ATIVO', now(), now()),
  ('f14a0000-0000-0000-0000-000000001a02', 'f14a0000-0000-0000-0000-000000000001', 'E2EFINLIMITADO', 1, 'E2E Financeiro Limitado', 'financeiro-limitado@e2e-fixture.com', '$2b$12$YyD1R8sQEQKMbsoX2Y9m8OrU59qzoa8TCeQIINO4i0yiVetxHshve', 'ATIVO', now(), now());

INSERT INTO usuarios_papeis (usuario_id, papel_id, criado_em)
VALUES
  ('f14a0000-0000-0000-0000-000000001a01', 'f14a0000-0000-0000-0000-0000000000a1', now()),
  ('f14a0000-0000-0000-0000-000000001a02', 'f14a0000-0000-0000-0000-0000000000a2', now());

COMMIT;

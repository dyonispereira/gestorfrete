-- E2E fixtures for Lote 4 — Resultado Gerencial. Tenant próprio (não o da financeiro-seed.sql):
-- as asserções aqui são numéricas e exatas (Σ receita/custo por dimensão), então o tenant precisa
-- nascer vazio, sem risco de outra spec já ter lançado dado nele. Mesmo mecanismo de sempre —
-- precisa do conjunto completo: freight+crm+drivers+fleet+maintenance+documents+financial (montar e
-- despachar a viagem, CT-e até AUTORIZADO, Fatura, Conta a Pagar, Ordem de Serviço) + analytics
-- (visualizar o Resultado Gerencial). Password é "Senha123!" (mesmo hash bcrypt de toda a sessão).

BEGIN;

DELETE FROM sessoes_acesso WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM usuarios_papeis WHERE usuario_id IN ('f14a0000-0000-0000-0000-000000002a01');
DELETE FROM papel_permissao WHERE papel_id IN ('f14a0000-0000-0000-0000-0000000000b1');
DELETE FROM estornos_financeiros WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM contas_receber_status_history WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM contas_receber WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM fatura_viagens WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM faturas WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM rateios_despesa WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM aprovacoes_despesa WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM contas_pagar_status_history WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM contas_pagar WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM contas_bancarias WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM aprovacoes_custo WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM itens_ordem_servico WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM ordens_servico_status_history WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM ordens_servico WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM plano_contas WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM centros_custo WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM formas_pagamento WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM checklists_status_history WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM checklists WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM canhotos WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM janelas_entrega WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM entregas WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM eventos_fiscais WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM ctes_status_history WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM ctes WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM configuracoes_fiscais_tenant WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM alocacoes_recurso_viagem WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM viagem_status_history WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM viagens WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM veiculo_impedimentos WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM disponibilidade_veiculo WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM leituras_hodometro WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM veiculos_tracionadores WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM fornecedores WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM motoristas WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM clientes WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM usuarios WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM papeis WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM categorias_veiculo WHERE tenant_id = 'f14a0000-0000-0000-0000-000000000002';
DELETE FROM tenants WHERE id = 'f14a0000-0000-0000-0000-000000000002';

INSERT INTO tenants (id, codigo, versao, razao_social, cnpj, status, criado_em, atualizado_em)
VALUES ('f14a0000-0000-0000-0000-000000000002', 'E2ERES', 1, 'E2E Resultado Gerencial Tenant', '88999000000222', 'ATIVO', now(), now());

INSERT INTO categorias_veiculo (id, tenant_id, codigo, nome, status, criado_em, atualizado_em)
VALUES ('f14a0000-0000-0000-0000-0000000000c2', 'f14a0000-0000-0000-0000-000000000002', 'E2ECAT2', 'E2E Categoria', 'ATIVA', now(), now());

INSERT INTO formas_pagamento (id, tenant_id, nome, status)
VALUES ('f14a0000-0000-0000-0000-0000000000f4', 'f14a0000-0000-0000-0000-000000000002', 'PIX', 'ATIVA');

-- Necessária para o CT-e ser criado de verdade no despacho (`reserve_next_cte_number`).
INSERT INTO configuracoes_fiscais_tenant (id, tenant_id, certificado_arquivo_id, certificado_validade, ambiente, regime_tributario, serie_cte, proximo_numero_cte, serie_mdfe, proximo_numero_mdfe, status)
VALUES ('f14a0000-0000-0000-0000-0000000000f5', 'f14a0000-0000-0000-0000-000000000002', 'f14a0000-0000-0000-0000-0000000000f6', '2035-12-31', 'HOMOLOGACAO', 'SIMPLES_NACIONAL', '1', 1, '1', 1, 'ATIVA');

INSERT INTO papeis (id, tenant_id, codigo, versao, nome, descricao, criado_em, atualizado_em)
VALUES ('f14a0000-0000-0000-0000-0000000000b1', 'f14a0000-0000-0000-0000-000000000002', 'E2ERESADM', 1, 'E2E Resultado Gerencial Admin', 'Acesso total ao ciclo Viagem->Fatura->CR->OS->CP->Resultado', now(), now());

INSERT INTO papel_permissao (papel_id, permissao_id, criado_em)
SELECT 'f14a0000-0000-0000-0000-0000000000b1', id, now() FROM permissoes
WHERE modulo IN ('freight', 'crm', 'drivers', 'fleet', 'maintenance', 'documents', 'financial', 'analytics')
   OR codigo LIKE 'storage.%'
   OR codigo LIKE 'financial.trip_%.view'
   OR codigo IN ('identity_access.role.view', 'identity_access.user.view');

INSERT INTO usuarios (id, tenant_id, codigo, versao, nome, email, senha_hash, status, criado_em, atualizado_em)
VALUES ('f14a0000-0000-0000-0000-000000002a01', 'f14a0000-0000-0000-0000-000000000002', 'E2ERESADM', 1, 'E2E Resultado Gerencial Admin', 'resultado-admin@e2e-fixture.com', '$2b$12$YyD1R8sQEQKMbsoX2Y9m8OrU59qzoa8TCeQIINO4i0yiVetxHshve', 'ATIVO', now(), now());

INSERT INTO usuarios_papeis (usuario_id, papel_id, criado_em)
VALUES ('f14a0000-0000-0000-0000-000000002a01', 'f14a0000-0000-0000-0000-0000000000b1', now());

COMMIT;

-- E2E fixtures for Sprint 15 — Frontend, Lote Frota e Manutenção, Parte 1 (Checklist).
-- Same mechanism as every prior lote. Unlike `fiscal-seed.sql`, this spec creates EVERYTHING
-- through the UI, including the CT-e — that's the whole point: proving `AGUARDANDO_CHECKLIST →
-- LIBERADA → despacho → CT-e auto-criado` is reachable end to end without any SQL seeding beyond
-- the usual tenant/role/user/categoria bootstrap. Role needs freight+crm+drivers+fleet (build the
-- trip) + maintenance (checklist) + documents (verify the CT-e). `categorias_veiculo` still has no
-- HTTP endpoint (D363). Password is "Senha123!" (same bcrypt hash used throughout this session).

BEGIN;

DELETE FROM sessoes_acesso WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM usuarios_papeis WHERE usuario_id = 'c4ec0000-0000-0000-0000-000000001a01';
DELETE FROM papel_permissao WHERE papel_id = 'c4ec0000-0000-0000-0000-0000000000a1';
DELETE FROM checklists_status_history WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM checklists WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM anexos WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM comentarios WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM canhotos WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM janelas_entrega WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM entregas WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM ocorrencias WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM alocacoes_recurso_viagem WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM viagem_status_history WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM ctes_status_history WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM ctes WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM configuracoes_fiscais_tenant WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM viagens WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM veiculo_impedimentos WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM disponibilidade_veiculo WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM veiculos_tracionadores WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM motoristas WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM clientes WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM usuarios WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM papeis WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM categorias_veiculo WHERE tenant_id = 'c4ec0000-0000-0000-0000-000000000001';
DELETE FROM tenants WHERE id = 'c4ec0000-0000-0000-0000-000000000001';

INSERT INTO tenants (id, codigo, versao, razao_social, cnpj, status, criado_em, atualizado_em)
VALUES ('c4ec0000-0000-0000-0000-000000000001', 'E2ECHECK', 1, 'E2E Checklist Tenant', '55666777000188', 'ATIVO', now(), now());

INSERT INTO categorias_veiculo (id, tenant_id, codigo, nome, status, criado_em, atualizado_em)
VALUES ('c4ec0000-0000-0000-0000-0000000000c1', 'c4ec0000-0000-0000-0000-000000000001', 'E2ECAT', 'E2E Categoria', 'ATIVA', now(), now());

-- Necessária para o CT-e ser criado de verdade no despacho (`reserve_next_cte_number`) — mesmo
-- gap já documentado na Lote Documentos Fiscais: não existe endpoint/onboarding para criar isto.
INSERT INTO configuracoes_fiscais_tenant (id, tenant_id, certificado_arquivo_id, certificado_validade, ambiente, regime_tributario, serie_cte, proximo_numero_cte, serie_mdfe, proximo_numero_mdfe, status)
VALUES ('c4ec0000-0000-0000-0000-0000000000f1', 'c4ec0000-0000-0000-0000-000000000001', 'c4ec0000-0000-0000-0000-0000000000f2', '2035-12-31', 'HOMOLOGACAO', 'SIMPLES_NACIONAL', '1', 1, '1', 1, 'ATIVA');

INSERT INTO papeis (id, tenant_id, codigo, versao, nome, descricao, criado_em, atualizado_em)
VALUES ('c4ec0000-0000-0000-0000-0000000000a1', 'c4ec0000-0000-0000-0000-000000000001', 'E2ECHECKADM', 1, 'E2E Checklist Admin', 'Acesso total ao caminho real até LIBERADA', now(), now());

INSERT INTO papel_permissao (papel_id, permissao_id, criado_em)
SELECT 'c4ec0000-0000-0000-0000-0000000000a1', id, now() FROM permissoes
WHERE modulo IN ('freight', 'crm', 'drivers', 'fleet', 'maintenance', 'documents')
   OR codigo LIKE 'storage.%'
   OR codigo LIKE 'financial.trip_%.view'
   OR codigo = 'identity_access.role.view';

INSERT INTO usuarios (id, tenant_id, codigo, versao, nome, email, senha_hash, status, criado_em, atualizado_em)
VALUES ('c4ec0000-0000-0000-0000-000000001a01', 'c4ec0000-0000-0000-0000-000000000001', 'E2ECHECKADM', 1, 'E2E Checklist Admin', 'checklist-admin@e2e-fixture.com', '$2b$12$YyD1R8sQEQKMbsoX2Y9m8OrU59qzoa8TCeQIINO4i0yiVetxHshve', 'ATIVO', now(), now());

INSERT INTO usuarios_papeis (usuario_id, papel_id, criado_em)
VALUES ('c4ec0000-0000-0000-0000-000000001a01', 'c4ec0000-0000-0000-0000-0000000000a1', now());

COMMIT;

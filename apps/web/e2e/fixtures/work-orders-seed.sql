-- E2E fixtures for Sprint 15 — Frontend, Lote Frota e Manutenção, Parte 2 (Ordens de Serviço).
-- Same mechanism as every prior lote. Role needs fleet (create a vehicle via UI) + maintenance
-- (work orders + checklist, for the Checklist↔OS wiring scenario). `categorias_veiculo` still has
-- no HTTP endpoint (D363). Password is "Senha123!" (same bcrypt hash used throughout this session).

BEGIN;

DELETE FROM sessoes_acesso WHERE tenant_id = '05de0000-0000-0000-0000-000000000001';
DELETE FROM usuarios_papeis WHERE usuario_id = '05de0000-0000-0000-0000-000000001a01';
DELETE FROM papel_permissao WHERE papel_id = '05de0000-0000-0000-0000-0000000000a1';
DELETE FROM checklists_status_history WHERE tenant_id = '05de0000-0000-0000-0000-000000000001';
DELETE FROM checklists WHERE tenant_id = '05de0000-0000-0000-0000-000000000001';
DELETE FROM aprovacoes_custo WHERE tenant_id = '05de0000-0000-0000-0000-000000000001';
DELETE FROM itens_ordem_servico WHERE tenant_id = '05de0000-0000-0000-0000-000000000001';
DELETE FROM ordens_servico_status_history WHERE tenant_id = '05de0000-0000-0000-0000-000000000001';
DELETE FROM ordens_servico WHERE tenant_id = '05de0000-0000-0000-0000-000000000001';
-- Ambas populadas pelos efeitos cross-module conectados na Parte 2 (VehicleAvailabilityProjector
-- + Leitura de Hodômetro origem=ORDEM_SERVICO) — precisam sair antes do veículo, mesma FK real.
DELETE FROM disponibilidade_veiculo WHERE tenant_id = '05de0000-0000-0000-0000-000000000001';
DELETE FROM leituras_hodometro WHERE tenant_id = '05de0000-0000-0000-0000-000000000001';
DELETE FROM veiculos_tracionadores WHERE tenant_id = '05de0000-0000-0000-0000-000000000001';
DELETE FROM usuarios WHERE tenant_id = '05de0000-0000-0000-0000-000000000001';
DELETE FROM papeis WHERE tenant_id = '05de0000-0000-0000-0000-000000000001';
DELETE FROM categorias_veiculo WHERE tenant_id = '05de0000-0000-0000-0000-000000000001';
DELETE FROM tenants WHERE id = '05de0000-0000-0000-0000-000000000001';

INSERT INTO tenants (id, codigo, versao, razao_social, cnpj, status, criado_em, atualizado_em)
VALUES ('05de0000-0000-0000-0000-000000000001', 'E2EOS', 1, 'E2E Ordens de Servico Tenant', '66777888000199', 'ATIVO', now(), now());

INSERT INTO categorias_veiculo (id, tenant_id, codigo, nome, status, criado_em, atualizado_em)
VALUES ('05de0000-0000-0000-0000-0000000000c1', '05de0000-0000-0000-0000-000000000001', 'E2ECAT', 'E2E Categoria', 'ATIVA', now(), now());

INSERT INTO papeis (id, tenant_id, codigo, versao, nome, descricao, criado_em, atualizado_em)
VALUES ('05de0000-0000-0000-0000-0000000000a1', '05de0000-0000-0000-0000-000000000001', 'E2EOSADM', 1, 'E2E OS Admin', 'Acesso total a Ordens de Servico', now(), now());

INSERT INTO papel_permissao (papel_id, permissao_id, criado_em)
SELECT '05de0000-0000-0000-0000-0000000000a1', id, now() FROM permissoes
WHERE modulo IN ('fleet', 'maintenance') OR codigo = 'identity_access.role.view';

INSERT INTO usuarios (id, tenant_id, codigo, versao, nome, email, senha_hash, status, criado_em, atualizado_em)
VALUES ('05de0000-0000-0000-0000-000000001a01', '05de0000-0000-0000-0000-000000000001', 'E2EOSADM', 1, 'E2E OS Admin', 'work-orders-admin@e2e-fixture.com', '$2b$12$YyD1R8sQEQKMbsoX2Y9m8OrU59qzoa8TCeQIINO4i0yiVetxHshve', 'ATIVO', now(), now());

INSERT INTO usuarios_papeis (usuario_id, papel_id, criado_em)
VALUES ('05de0000-0000-0000-0000-000000001a01', '05de0000-0000-0000-0000-0000000000a1', now());

COMMIT;

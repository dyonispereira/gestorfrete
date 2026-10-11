-- E2E fixtures for Lote 2 (GESTORFRETE — PROMPT MESTRE, apps/web/e2e/pricing.spec.ts).
-- Same mechanism as viagens-seed.sql — a Tabela de Frete needs a Categoria de Veículo (fleet) to
-- scope items, and applying it needs a Viagem (freight) + Cliente/Motorista/Veículo (crm/drivers/
-- fleet), so this role carries those modules too, same self-contained pattern as every other Lote
-- spec. Password for the user is "Senha123!" (same bcrypt hash used throughout this session).

BEGIN;

DELETE FROM sessoes_acesso WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM usuarios_papeis WHERE usuario_id = 'f4e19000-0000-0000-0000-000000002a01';
DELETE FROM papel_permissao WHERE papel_id = 'f4e19000-0000-0000-0000-0000000000a2';
DELETE FROM aplicacoes_tabela_preco_viagem WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM itens_tabela_preco WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM tabelas_preco WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM anexos WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM comentarios WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM canhotos WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM janelas_entrega WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM entregas WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM ocorrencias WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM alocacoes_recurso_viagem WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM viagem_status_history WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM viagens WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM veiculos_tracionadores WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM motoristas WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM clientes WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM usuarios WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM papeis WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM categorias_veiculo WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000002';
DELETE FROM tenants WHERE id = 'f4e19000-0000-0000-0000-000000000002';

INSERT INTO tenants (id, codigo, versao, razao_social, cnpj, status, criado_em, atualizado_em)
VALUES ('f4e19000-0000-0000-0000-000000000002', 'E2EPRICING', 1, 'E2E Pricing Tenant', '88888888000280', 'ATIVO', now(), now());

INSERT INTO categorias_veiculo (id, tenant_id, codigo, nome, status, criado_em, atualizado_em)
VALUES ('f4e19000-0000-0000-0000-0000000000c2', 'f4e19000-0000-0000-0000-000000000002', 'E2ECAT', 'E2E Categoria', 'ATIVA', now(), now());

INSERT INTO papeis (id, tenant_id, codigo, versao, nome, descricao, criado_em, atualizado_em)
VALUES ('f4e19000-0000-0000-0000-0000000000a2', 'f4e19000-0000-0000-0000-000000000002', 'E2EPRICINGADM', 1, 'E2E Pricing Admin', 'Acesso total a Comercial/Operação', now(), now());

INSERT INTO papel_permissao (papel_id, permissao_id, criado_em)
SELECT 'f4e19000-0000-0000-0000-0000000000a2', id, now() FROM permissoes
WHERE modulo IN ('freight', 'crm', 'drivers', 'fleet', 'pricing')
   OR codigo LIKE 'storage.%'
   OR codigo LIKE 'financial.trip_%.view'
   OR codigo = 'identity_access.role.view';

INSERT INTO usuarios (id, tenant_id, codigo, versao, nome, email, senha_hash, status, criado_em, atualizado_em)
VALUES ('f4e19000-0000-0000-0000-000000002a01', 'f4e19000-0000-0000-0000-000000000002', 'E2EPRICINGADM', 1, 'E2E Pricing Admin', 'pricing-admin@e2e-fixture.com', '$2b$12$YyD1R8sQEQKMbsoX2Y9m8OrU59qzoa8TCeQIINO4i0yiVetxHshve', 'ATIVO', now(), now());

INSERT INTO usuarios_papeis (usuario_id, papel_id, criado_em)
VALUES ('f4e19000-0000-0000-0000-000000002a01', 'f4e19000-0000-0000-0000-0000000000a2', now());

COMMIT;

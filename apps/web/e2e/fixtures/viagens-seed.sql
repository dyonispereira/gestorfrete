-- E2E fixtures for Sprint 13 — Frontend, Lote Operação (apps/web/e2e/viagens.spec.ts).
-- Same mechanism as identity/cadastros/frota seeds. A Viagem depends on Cliente (Cadastros) and
-- Motorista/Veículo (Frota), so this role also carries crm/drivers/fleet permissions — the spec
-- creates its own cliente/motorista/veículo via UI before creating a Viagem, same self-contained
-- pattern as every other Lote spec. `categorias_veiculo` still has no HTTP endpoint (D363) — seeded
-- directly, same as frota-seed.sql. Password for the user is "Senha123!" (same bcrypt hash used
-- throughout this session).

BEGIN;

DELETE FROM sessoes_acesso WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000001';
DELETE FROM usuarios_papeis WHERE usuario_id = 'f4e19000-0000-0000-0000-000000001a01';
DELETE FROM papel_permissao WHERE papel_id = 'f4e19000-0000-0000-0000-0000000000a1';
DELETE FROM anexos WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000001';
DELETE FROM comentarios WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000001';
DELETE FROM canhotos WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000001';
DELETE FROM janelas_entrega WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000001';
DELETE FROM entregas WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000001';
DELETE FROM ocorrencias WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000001';
DELETE FROM alocacoes_recurso_viagem WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000001';
DELETE FROM viagem_status_history WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000001';
-- `pontos_parada_viagem`/`coletas`/`romaneios` estão em `docs/database/relational/003-operacao.md`
-- mas ainda não foram migrados (Coleta/Romaneio não têm endpoint algum, fora de escopo desta Lote).
DELETE FROM viagens WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000001';
DELETE FROM veiculos_tracionadores WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000001';
DELETE FROM motoristas WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000001';
DELETE FROM clientes WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000001';
DELETE FROM usuarios WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000001';
DELETE FROM papeis WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000001';
DELETE FROM categorias_veiculo WHERE tenant_id = 'f4e19000-0000-0000-0000-000000000001';
DELETE FROM tenants WHERE id = 'f4e19000-0000-0000-0000-000000000001';

INSERT INTO tenants (id, codigo, versao, razao_social, cnpj, status, criado_em, atualizado_em)
VALUES ('f4e19000-0000-0000-0000-000000000001', 'E2EVIAGEM', 1, 'E2E Operação Tenant', '88888888000199', 'ATIVO', now(), now());

INSERT INTO categorias_veiculo (id, tenant_id, codigo, nome, status, criado_em, atualizado_em)
VALUES ('f4e19000-0000-0000-0000-0000000000c1', 'f4e19000-0000-0000-0000-000000000001', 'E2ECAT', 'E2E Categoria', 'ATIVA', now(), now());

INSERT INTO papeis (id, tenant_id, codigo, versao, nome, descricao, criado_em, atualizado_em)
VALUES ('f4e19000-0000-0000-0000-0000000000a1', 'f4e19000-0000-0000-0000-000000000001', 'E2EVIAGEMADM', 1, 'E2E Operação Admin', 'Acesso total a Operação', now(), now());

INSERT INTO papel_permissao (papel_id, permissao_id, criado_em)
SELECT 'f4e19000-0000-0000-0000-0000000000a1', id, now() FROM permissoes
WHERE modulo IN ('freight', 'crm', 'drivers', 'fleet')
   OR codigo LIKE 'storage.%'
   OR codigo LIKE 'financial.trip_%.view'
   OR codigo = 'identity_access.role.view';

INSERT INTO usuarios (id, tenant_id, codigo, versao, nome, email, senha_hash, status, criado_em, atualizado_em)
VALUES ('f4e19000-0000-0000-0000-000000001a01', 'f4e19000-0000-0000-0000-000000000001', 'E2EVIAGEMADM', 1, 'E2E Operação Admin', 'viagens-admin@e2e-fixture.com', '$2b$12$YyD1R8sQEQKMbsoX2Y9m8OrU59qzoa8TCeQIINO4i0yiVetxHshve', 'ATIVO', now(), now());

INSERT INTO usuarios_papeis (usuario_id, papel_id, criado_em)
VALUES ('f4e19000-0000-0000-0000-000000001a01', 'f4e19000-0000-0000-0000-0000000000a1', now());

COMMIT;

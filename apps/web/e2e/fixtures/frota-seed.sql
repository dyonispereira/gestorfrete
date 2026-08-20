-- E2E fixtures for Sprint 12 — Frontend, Lote Frota (apps/web/e2e/frota.spec.ts).
-- Same mechanism as identity/cadastros seeds. `categorias_veiculo` has no HTTP endpoint at all
-- (D363) — seeded directly here, same as the Backend's own integration tests do. Password for the
-- user is "Senha123!" (same bcrypt hash used throughout this session).

BEGIN;

DELETE FROM sessoes_acesso WHERE tenant_id = 'f10ea000-0000-0000-0000-000000000001';
DELETE FROM usuarios_papeis WHERE usuario_id = 'f10ea000-0000-0000-0000-000000001a01';
DELETE FROM papel_permissao WHERE papel_id = 'f10ea000-0000-0000-0000-0000000000a1';
DELETE FROM leituras_hodometro WHERE veiculo_tracionador_id IN (SELECT id FROM veiculos_tracionadores WHERE tenant_id = 'f10ea000-0000-0000-0000-000000000001');
DELETE FROM composicoes_veiculares_implementos WHERE composicao_veicular_id IN (SELECT id FROM composicoes_veiculares WHERE tenant_id = 'f10ea000-0000-0000-0000-000000000001');
DELETE FROM composicoes_veiculares WHERE tenant_id = 'f10ea000-0000-0000-0000-000000000001';
DELETE FROM documentos_veiculo WHERE veiculo_tracionador_id IN (SELECT id FROM veiculos_tracionadores WHERE tenant_id = 'f10ea000-0000-0000-0000-000000000001');
DELETE FROM fichas_tecnicas_veiculo WHERE veiculo_tracionador_id IN (SELECT id FROM veiculos_tracionadores WHERE tenant_id = 'f10ea000-0000-0000-0000-000000000001');
DELETE FROM veiculos_tracionadores WHERE tenant_id = 'f10ea000-0000-0000-0000-000000000001';
DELETE FROM implementos WHERE tenant_id = 'f10ea000-0000-0000-0000-000000000001';
DELETE FROM usuarios WHERE tenant_id = 'f10ea000-0000-0000-0000-000000000001';
DELETE FROM papeis WHERE tenant_id = 'f10ea000-0000-0000-0000-000000000001';
DELETE FROM categorias_veiculo WHERE tenant_id = 'f10ea000-0000-0000-0000-000000000001';
DELETE FROM tenants WHERE id = 'f10ea000-0000-0000-0000-000000000001';

INSERT INTO tenants (id, codigo, versao, razao_social, cnpj, status, criado_em, atualizado_em)
VALUES ('f10ea000-0000-0000-0000-000000000001', 'E2EFROTA', 1, 'E2E Frota Tenant', '77777777000188', 'ATIVO', now(), now());

INSERT INTO categorias_veiculo (id, tenant_id, codigo, nome, status, criado_em, atualizado_em)
VALUES ('f10ea000-0000-0000-0000-0000000000c1', 'f10ea000-0000-0000-0000-000000000001', 'E2ECAT', 'E2E Categoria', 'ATIVA', now(), now());

INSERT INTO papeis (id, tenant_id, codigo, versao, nome, descricao, criado_em, atualizado_em)
VALUES ('f10ea000-0000-0000-0000-0000000000a1', 'f10ea000-0000-0000-0000-000000000001', 'E2EFROTAADM', 1, 'E2E Frota Admin', 'Acesso total a frota', now(), now());

INSERT INTO papel_permissao (papel_id, permissao_id, criado_em)
SELECT 'f10ea000-0000-0000-0000-0000000000a1', id, now() FROM permissoes
WHERE modulo = 'fleet' OR codigo = 'identity_access.role.view';

INSERT INTO usuarios (id, tenant_id, codigo, versao, nome, email, senha_hash, status, criado_em, atualizado_em)
VALUES ('f10ea000-0000-0000-0000-000000001a01', 'f10ea000-0000-0000-0000-000000000001', 'E2EFROTAADM', 1, 'E2E Frota Admin', 'frota-admin@e2e-fixture.com', '$2b$12$YyD1R8sQEQKMbsoX2Y9m8OrU59qzoa8TCeQIINO4i0yiVetxHshve', 'ATIVO', now(), now());

INSERT INTO usuarios_papeis (usuario_id, papel_id, criado_em)
VALUES ('f10ea000-0000-0000-0000-000000001a01', 'f10ea000-0000-0000-0000-0000000000a1', now());

COMMIT;

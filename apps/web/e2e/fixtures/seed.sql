-- E2E fixtures for Sprint 12 — Frontend, Lote Identity (apps/web/e2e/identity.spec.ts).
--
-- No self-service tenant/onboarding endpoint exists yet (modules/onboarding is still empty), so
-- the very first Actor of a tenant can only be seeded directly — the same mechanism validated by
-- hand earlier in this session. Fixed UUIDs (not gen_random_uuid()) so teardown.sql can delete
-- exactly these rows and nothing else. Password for every user below is "Senha123!" (bcrypt hash
-- from core.security.password_hasher.BcryptPasswordHasher, same hash used throughout manual
-- testing this session).
--
-- One Papel per scenario, each holding exactly the permissions that scenario needs — never more:
--   E2E Full Access  — todos os identity_access.*                        (cenário 1)
--   E2E Viewer       — só identity_access.user.view                      (cenário 2: vê a lista, não o botão de criar)
--   E2E No Access    — nenhuma permissão                                 (cenário 3: bloqueado pelo backend)
--   E2E Self Editor  — identity_access.role.view/.edit/permission.view   (cenário 4: concede a si mesmo user.view e usa sem reload;
--                                                                          permission.view é pré-requisito real para listar o catálogo
--                                                                          e montar a matriz — não uma folga do fixture)

BEGIN;

DELETE FROM sessoes_acesso WHERE tenant_id = 'e2e00000-0000-0000-0000-000000000001';
DELETE FROM usuarios_papeis WHERE usuario_id IN (
  'e2e00000-0000-0000-0000-000000001a01',
  'e2e00000-0000-0000-0000-000000001b01',
  'e2e00000-0000-0000-0000-000000001c01',
  'e2e00000-0000-0000-0000-000000001d01'
);
DELETE FROM papel_permissao WHERE papel_id IN (
  'e2e00000-0000-0000-0000-0000000000a1',
  'e2e00000-0000-0000-0000-0000000000b1',
  'e2e00000-0000-0000-0000-0000000000c1',
  'e2e00000-0000-0000-0000-0000000000d1'
);
DELETE FROM usuarios WHERE tenant_id = 'e2e00000-0000-0000-0000-000000000001';
DELETE FROM papeis WHERE tenant_id = 'e2e00000-0000-0000-0000-000000000001';
DELETE FROM tenants WHERE id = 'e2e00000-0000-0000-0000-000000000001';

INSERT INTO tenants (id, codigo, versao, razao_social, cnpj, status, criado_em, atualizado_em)
VALUES ('e2e00000-0000-0000-0000-000000000001', 'E2EIDENT', 1, 'E2E Identity Tenant', '33333333000144', 'ATIVO', now(), now());

INSERT INTO papeis (id, tenant_id, codigo, versao, nome, descricao, criado_em, atualizado_em) VALUES
  ('e2e00000-0000-0000-0000-0000000000a1', 'e2e00000-0000-0000-0000-000000000001', 'E2EFULL', 1, 'E2E Full Access', 'Todas as permissões de identity_access', now(), now()),
  ('e2e00000-0000-0000-0000-0000000000b1', 'e2e00000-0000-0000-0000-000000000001', 'E2EVIEWER', 1, 'E2E Viewer', 'Só visualizar usuários', now(), now()),
  ('e2e00000-0000-0000-0000-0000000000c1', 'e2e00000-0000-0000-0000-000000000001', 'E2ENONE', 1, 'E2E No Access', 'Nenhuma permissão', now(), now()),
  ('e2e00000-0000-0000-0000-0000000000d1', 'e2e00000-0000-0000-0000-000000000001', 'E2ESELF', 1, 'E2E Self Editor', 'Só Papéis, ainda sem ver Usuários', now(), now());

INSERT INTO papel_permissao (papel_id, permissao_id, criado_em)
SELECT 'e2e00000-0000-0000-0000-0000000000a1', id, now() FROM permissoes WHERE codigo LIKE 'identity_access.%';

INSERT INTO papel_permissao (papel_id, permissao_id, criado_em)
SELECT 'e2e00000-0000-0000-0000-0000000000b1', id, now() FROM permissoes WHERE codigo = 'identity_access.user.view';

INSERT INTO papel_permissao (papel_id, permissao_id, criado_em)
SELECT 'e2e00000-0000-0000-0000-0000000000d1', id, now() FROM permissoes
WHERE codigo IN ('identity_access.role.view', 'identity_access.role.edit', 'identity_access.permission.view');

INSERT INTO usuarios (id, tenant_id, codigo, versao, nome, email, senha_hash, status, criado_em, atualizado_em) VALUES
  ('e2e00000-0000-0000-0000-000000001a01', 'e2e00000-0000-0000-0000-000000000001', 'E2EFULLU', 1, 'E2E Full', 'full@e2e-fixture.com', '$2b$12$YyD1R8sQEQKMbsoX2Y9m8OrU59qzoa8TCeQIINO4i0yiVetxHshve', 'ATIVO', now(), now()),
  ('e2e00000-0000-0000-0000-000000001b01', 'e2e00000-0000-0000-0000-000000000001', 'E2EVIEWU', 1, 'E2E Viewer', 'viewer@e2e-fixture.com', '$2b$12$YyD1R8sQEQKMbsoX2Y9m8OrU59qzoa8TCeQIINO4i0yiVetxHshve', 'ATIVO', now(), now()),
  ('e2e00000-0000-0000-0000-000000001c01', 'e2e00000-0000-0000-0000-000000000001', 'E2ENONEU', 1, 'E2E No Access', 'noaccess@e2e-fixture.com', '$2b$12$YyD1R8sQEQKMbsoX2Y9m8OrU59qzoa8TCeQIINO4i0yiVetxHshve', 'ATIVO', now(), now()),
  ('e2e00000-0000-0000-0000-000000001d01', 'e2e00000-0000-0000-0000-000000000001', 'E2ESELFU', 1, 'E2E Self Editor', 'selfeditor@e2e-fixture.com', '$2b$12$YyD1R8sQEQKMbsoX2Y9m8OrU59qzoa8TCeQIINO4i0yiVetxHshve', 'ATIVO', now(), now());

INSERT INTO usuarios_papeis (usuario_id, papel_id, criado_em) VALUES
  ('e2e00000-0000-0000-0000-000000001a01', 'e2e00000-0000-0000-0000-0000000000a1', now()),
  ('e2e00000-0000-0000-0000-000000001b01', 'e2e00000-0000-0000-0000-0000000000b1', now()),
  ('e2e00000-0000-0000-0000-000000001c01', 'e2e00000-0000-0000-0000-0000000000c1', now()),
  ('e2e00000-0000-0000-0000-000000001d01', 'e2e00000-0000-0000-0000-0000000000d1', now());

COMMIT;

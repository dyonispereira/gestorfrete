-- E2E fixtures for Sprint 12 — Frontend, Lote Cadastros (apps/web/e2e/cadastros.spec.ts).
-- Same mechanism as identity's seed.sql — no self-service tenant/onboarding endpoint exists yet.
-- One admin Papel with every crm/maintenance/drivers/identity_access.employee/financial.cost_center
-- permission, PLUS identity_access.role.view — without it `PermissionsProvider` can't even resolve
-- its own Role's permissions (`GET /roles/{id}` itself requires that permission), found the hard
-- way during manual testing this Lote. Password for the user is "Senha123!" (same bcrypt hash used
-- throughout this session).

BEGIN;

DELETE FROM sessoes_acesso WHERE tenant_id = 'cad00000-0000-0000-0000-000000000001';
DELETE FROM usuarios_papeis WHERE usuario_id = 'cad00000-0000-0000-0000-000000001a01';
DELETE FROM papel_permissao WHERE papel_id = 'cad00000-0000-0000-0000-0000000000a1';
DELETE FROM contatos_cliente WHERE cliente_id IN (SELECT id FROM clientes WHERE tenant_id = 'cad00000-0000-0000-0000-000000000001');
DELETE FROM enderecos WHERE entidade_id IN (
  SELECT id FROM clientes WHERE tenant_id = 'cad00000-0000-0000-0000-000000000001'
  UNION SELECT id FROM fornecedores WHERE tenant_id = 'cad00000-0000-0000-0000-000000000001'
);
DELETE FROM documentos_motorista WHERE motorista_id IN (SELECT id FROM motoristas WHERE tenant_id = 'cad00000-0000-0000-0000-000000000001');
DELETE FROM clientes WHERE tenant_id = 'cad00000-0000-0000-0000-000000000001';
DELETE FROM fornecedores WHERE tenant_id = 'cad00000-0000-0000-0000-000000000001';
DELETE FROM motoristas WHERE tenant_id = 'cad00000-0000-0000-0000-000000000001';
DELETE FROM funcionarios WHERE tenant_id = 'cad00000-0000-0000-0000-000000000001';
DELETE FROM centros_custo WHERE tenant_id = 'cad00000-0000-0000-0000-000000000001';
DELETE FROM usuarios WHERE tenant_id = 'cad00000-0000-0000-0000-000000000001';
DELETE FROM papeis WHERE tenant_id = 'cad00000-0000-0000-0000-000000000001';
DELETE FROM tenants WHERE id = 'cad00000-0000-0000-0000-000000000001';

INSERT INTO tenants (id, codigo, versao, razao_social, cnpj, status, criado_em, atualizado_em)
VALUES ('cad00000-0000-0000-0000-000000000001', 'E2ECAD', 1, 'E2E Cadastros Tenant', '44444444000155', 'ATIVO', now(), now());

INSERT INTO papeis (id, tenant_id, codigo, versao, nome, descricao, criado_em, atualizado_em)
VALUES ('cad00000-0000-0000-0000-0000000000a1', 'cad00000-0000-0000-0000-000000000001', 'E2ECADADM', 1, 'E2E Cadastros Admin', 'Acesso total a Cadastros', now(), now());

INSERT INTO papel_permissao (papel_id, permissao_id, criado_em)
SELECT 'cad00000-0000-0000-0000-0000000000a1', id, now() FROM permissoes
WHERE modulo IN ('crm', 'maintenance', 'drivers')
   OR codigo LIKE 'identity_access.employee.%'
   OR codigo LIKE 'financial.cost_center.%'
   OR codigo = 'identity_access.role.view';

INSERT INTO usuarios (id, tenant_id, codigo, versao, nome, email, senha_hash, status, criado_em, atualizado_em)
VALUES ('cad00000-0000-0000-0000-000000001a01', 'cad00000-0000-0000-0000-000000000001', 'E2ECADADM', 1, 'E2E Cadastros Admin', 'cadastros-admin@e2e-fixture.com', '$2b$12$YyD1R8sQEQKMbsoX2Y9m8OrU59qzoa8TCeQIINO4i0yiVetxHshve', 'ATIVO', now(), now());

INSERT INTO usuarios_papeis (usuario_id, papel_id, criado_em)
VALUES ('cad00000-0000-0000-0000-000000001a01', 'cad00000-0000-0000-0000-0000000000a1', now());

COMMIT;

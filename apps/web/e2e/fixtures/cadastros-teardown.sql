-- Mirrors cadastros-seed.sql's delete block.
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
COMMIT;

-- Mirrors frota-seed.sql's delete block.
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
COMMIT;

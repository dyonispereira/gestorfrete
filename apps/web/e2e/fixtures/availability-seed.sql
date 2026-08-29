-- E2E fixtures for Sprint 15 — Lote Frota e Manutenção, Parte 3 (Availability Hardening).
-- Mesmo mecanismo de todo Lote anterior. Precisa do conjunto completo: freight+crm+drivers+fleet
-- (montar e despachar a viagem) + maintenance (checklist + OS, para o cenário de conflito) +
-- documents (CT-e nasce sozinho no despacho, D396). `categorias_veiculo` ainda sem endpoint HTTP
-- (D363). Password é "Senha123!" (mesmo hash bcrypt usado em toda a sessão).

BEGIN;

DELETE FROM sessoes_acesso WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM usuarios_papeis WHERE usuario_id = 'a7a10000-0000-0000-0000-000000001a01';
DELETE FROM papel_permissao WHERE papel_id = 'a7a10000-0000-0000-0000-0000000000a1';
DELETE FROM checklists_status_history WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM checklists WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM aprovacoes_custo WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM itens_ordem_servico WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM ordens_servico_status_history WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM ordens_servico WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM ctes_status_history WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM ctes WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM configuracoes_fiscais_tenant WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM alocacoes_recurso_viagem WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM viagem_status_history WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM viagens WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM veiculo_impedimentos WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM disponibilidade_veiculo WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM leituras_hodometro WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM veiculos_tracionadores WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM motoristas WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM clientes WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM usuarios WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM papeis WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM categorias_veiculo WHERE tenant_id = 'a7a10000-0000-0000-0000-000000000001';
DELETE FROM tenants WHERE id = 'a7a10000-0000-0000-0000-000000000001';

INSERT INTO tenants (id, codigo, versao, razao_social, cnpj, status, criado_em, atualizado_em)
VALUES ('a7a10000-0000-0000-0000-000000000001', 'E2EAVAIL', 1, 'E2E Disponibilidade Tenant', '77888999000177', 'ATIVO', now(), now());

INSERT INTO categorias_veiculo (id, tenant_id, codigo, nome, status, criado_em, atualizado_em)
VALUES ('a7a10000-0000-0000-0000-0000000000c1', 'a7a10000-0000-0000-0000-000000000001', 'E2ECAT', 'E2E Categoria', 'ATIVA', now(), now());

-- Necessária para o CT-e ser criado de verdade no despacho (`reserve_next_cte_number`).
INSERT INTO configuracoes_fiscais_tenant (id, tenant_id, certificado_arquivo_id, certificado_validade, ambiente, regime_tributario, serie_cte, proximo_numero_cte, serie_mdfe, proximo_numero_mdfe, status)
VALUES ('a7a10000-0000-0000-0000-0000000000f1', 'a7a10000-0000-0000-0000-000000000001', 'a7a10000-0000-0000-0000-0000000000f2', '2035-12-31', 'HOMOLOGACAO', 'SIMPLES_NACIONAL', '1', 1, '1', 1, 'ATIVA');

INSERT INTO papeis (id, tenant_id, codigo, versao, nome, descricao, criado_em, atualizado_em)
VALUES ('a7a10000-0000-0000-0000-0000000000a1', 'a7a10000-0000-0000-0000-000000000001', 'E2EAVAILADM', 1, 'E2E Disponibilidade Admin', 'Acesso total ao ciclo Viagem+OS para provar Disponibilidade', now(), now());

INSERT INTO papel_permissao (papel_id, permissao_id, criado_em)
SELECT 'a7a10000-0000-0000-0000-0000000000a1', id, now() FROM permissoes
WHERE modulo IN ('freight', 'crm', 'drivers', 'fleet', 'maintenance', 'documents')
   OR codigo LIKE 'storage.%'
   OR codigo LIKE 'financial.trip_%.view'
   OR codigo = 'identity_access.role.view';

INSERT INTO usuarios (id, tenant_id, codigo, versao, nome, email, senha_hash, status, criado_em, atualizado_em)
VALUES ('a7a10000-0000-0000-0000-000000001a01', 'a7a10000-0000-0000-0000-000000000001', 'E2EAVAILADM', 1, 'E2E Disponibilidade Admin', 'availability-admin@e2e-fixture.com', '$2b$12$YyD1R8sQEQKMbsoX2Y9m8OrU59qzoa8TCeQIINO4i0yiVetxHshve', 'ATIVO', now(), now());

INSERT INTO usuarios_papeis (usuario_id, papel_id, criado_em)
VALUES ('a7a10000-0000-0000-0000-000000001a01', 'a7a10000-0000-0000-0000-0000000000a1', now());

COMMIT;

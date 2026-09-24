-- E2E fixture for V1 Operational Hardening, Parte 7 — "Dia Real da Transportadora". Mesmo
-- mecanismo de todo Lote anterior (tenant/role/user via SQL, D363-style bootstrap técnico
-- explicitamente permitido pelo usuário). Diferente de todos os fixtures anteriores: NÃO semeia
-- `categorias_veiculo` — a Categoria é criada pela própria UI dentro do teste (Parte 5 do mesmo
-- pedido, "Cliente → Motorista → Categoria → Veículo → ..."), prova real do CRUD, não um atalho.
-- Password é "Senha123!" (mesmo hash bcrypt usado em toda a sessão).

BEGIN;

DELETE FROM sessoes_acesso WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM usuarios_papeis WHERE usuario_id = 'da1a0000-0000-0000-0000-000000001a01';
DELETE FROM papel_permissao WHERE papel_id = 'da1a0000-0000-0000-0000-0000000000b1';
DELETE FROM canhotos WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM janelas_entrega WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM entregas WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM ocorrencias WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM itens_carga WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM romaneios WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM coletas WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM checklists_status_history WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM checklists WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM anexos WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM comentarios WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM alocacoes_recurso_viagem WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM viagem_status_history WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM leituras_hodometro WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM ctes_status_history WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM ctes WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM configuracoes_fiscais_tenant WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM viagens WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM veiculo_impedimentos WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM disponibilidade_veiculo WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM veiculos_tracionadores WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM motoristas WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM clientes WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM usuarios WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM papeis WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM categorias_veiculo WHERE tenant_id = 'da1a0000-0000-0000-0000-000000000001';
DELETE FROM tenants WHERE id = 'da1a0000-0000-0000-0000-000000000001';

INSERT INTO tenants (id, codigo, versao, razao_social, cnpj, status, criado_em, atualizado_em)
VALUES ('da1a0000-0000-0000-0000-000000000001', 'E2EDIAREAL', 1, 'E2E Dia Real Tenant', '11222333000144', 'ATIVO', now(), now());

-- Necessária para o CT-e ser criado de verdade no despacho (`reserve_next_cte_number`, D396) —
-- mesmo gap já documentado em todo Lote anterior: não existe endpoint/onboarding para isto.
INSERT INTO configuracoes_fiscais_tenant (id, tenant_id, certificado_arquivo_id, certificado_validade, ambiente, regime_tributario, serie_cte, proximo_numero_cte, serie_mdfe, proximo_numero_mdfe, status)
VALUES ('da1a0000-0000-0000-0000-0000000000f1', 'da1a0000-0000-0000-0000-000000000001', 'da1a0000-0000-0000-0000-0000000000f2', '2035-12-31', 'HOMOLOGACAO', 'SIMPLES_NACIONAL', '1', 1, '1', 1, 'ATIVA');

INSERT INTO papeis (id, tenant_id, codigo, versao, nome, descricao, criado_em, atualizado_em)
VALUES ('da1a0000-0000-0000-0000-0000000000b1', 'da1a0000-0000-0000-0000-000000000001', 'E2EDIAREALADM', 1, 'E2E Dia Real Admin', 'Acesso total ao ciclo operacional completo — Parte 7', now(), now());

INSERT INTO papel_permissao (papel_id, permissao_id, criado_em)
SELECT 'da1a0000-0000-0000-0000-0000000000b1', id, now() FROM permissoes
WHERE modulo IN ('freight', 'crm', 'drivers', 'fleet', 'maintenance', 'documents', 'financial', 'analytics')
   OR codigo LIKE 'storage.%'
   OR codigo LIKE 'financial.trip_%.view'
   OR codigo IN ('identity_access.role.view', 'identity_access.user.view');

INSERT INTO usuarios (id, tenant_id, codigo, versao, nome, email, senha_hash, status, criado_em, atualizado_em)
VALUES ('da1a0000-0000-0000-0000-000000001a01', 'da1a0000-0000-0000-0000-000000000001', 'E2EDIAREALADM', 1, 'E2E Dia Real Admin', 'dia-real-admin@e2e-fixture.com', '$2b$12$YyD1R8sQEQKMbsoX2Y9m8OrU59qzoa8TCeQIINO4i0yiVetxHshve', 'ATIVO', now(), now());

INSERT INTO usuarios_papeis (usuario_id, papel_id, criado_em)
VALUES ('da1a0000-0000-0000-0000-000000001a01', 'da1a0000-0000-0000-0000-0000000000b1', now());

COMMIT;

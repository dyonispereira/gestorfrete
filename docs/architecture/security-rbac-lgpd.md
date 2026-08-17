# Segurança: RBAC, JWT e LGPD

**Nesta etapa de fundação nenhum destes itens está implementado** — nem login, nem verificação de
permissão, nem tratamento de dados pessoais. Este documento registra as decisões e contratos já
definidos para que a implementação futura seja consistente com a fundação.

## JWT (autenticação)

`core/security/ports.py` define o contrato `TokenService` (emitir e validar tokens de acesso). A
configuração já existe em `core/config/settings.py` (`jwt_secret_key`, `jwt_algorithm`,
`jwt_access_token_expire_minutes`), mas nenhuma implementação concreta de emissão/validação de
token, nem endpoint de login, existe ainda — isso pertence ao bounded context `identity_access`
quando ele for implementado.

## RBAC (autorização)

RBAC (Role-Based Access Control) será modelado dentro de `identity_access`: usuários possuem
papéis (roles), papéis possuem permissões. A verificação de permissão deve acontecer na camada
`interfaces/` (via dependency do FastAPI), nunca espalhada dentro de `application/` — isso mantém a
lógica de autorização em um único lugar auditável por bounded context.

Um ponto importante para o modelo multi-tenant: papéis e permissões são **escopados por tenant** —
um usuário pode ter papéis diferentes em diferentes contas, quando a plataforma suportar usuários
vinculados a mais de uma transportadora.

## LGPD (Lei Geral de Proteção de Dados)

Considerações que devem orientar o design de `identity_access`, `drivers` e `documents` quando
forem implementados (motoristas e usuários são titulares de dados pessoais sob a LGPD):

- **Minimização**: coletar apenas os dados pessoais necessários para a operação da transportadora.
- **Finalidade e base legal**: cada dado pessoal armazenado deve ter uma finalidade e base legal
  identificável (execução de contrato, obrigação legal/fiscal para motoristas, etc.).
- **Direito de acesso/exclusão do titular**: o modelo de dados deve permitir localizar e, quando
  legalmente possível, anonimizar/excluir os dados de um titular específico — isso é mais fácil de
  garantir se cada bounded context mantém seus próprios dados pessoais de forma explícita, em vez
  de espalhados sem controle.
- **Auditoria**: o Event-Driven Architecture já registrado em [`event-driven.md`](./event-driven.md)
  cria naturalmente uma trilha de eventos que pode ser aproveitada como base de auditoria de acesso
  e alteração de dados pessoais quando esse requisito for implementado.

Nenhuma dessas práticas é implementada nesta etapa — ficam registradas aqui como restrições de
design a observar quando os bounded contexts relevantes forem construídos.

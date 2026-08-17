# 006 — Data Classification

Classificação de todos os dados do GestorFrete — base direta para a futura
`docs/product/RBAC_MATRIX.md` e para os controles de segurança na modelagem física.

## As classificações

Um mesmo dado pode receber **mais de um rótulo simultaneamente** — não são mutuamente exclusivos.
"Confidencial" descreve quem pode ver; "Fiscal"/"Financeiro" descrevem a natureza; "LGPD"/
"Sensível" descrevem a obrigação legal; "Crítico" descreve o impacto de perda/corrupção.

| Classificação | Significado |
|---|---|
| **Público** | Pode ser exposto sem restrição — inclusive fora do tenant (ex: dados de um CT-e visíveis ao próprio cliente destinatário) |
| **Interno** | Visível dentro do tenant, para quem tem acesso operacional normal; não deve vazar para fora |
| **Confidencial** | Acesso restrito a papéis específicos dentro do tenant, mesmo que outros usuários do mesmo tenant não tenham acesso |
| **Financeiro** | Subcategoria de Confidencial ligada especificamente a valores monetários da operação |
| **Fiscal** | Sujeito a regras regulatórias específicas de formato/retenção/emissão (SEFAZ, ANTT) |
| **LGPD** | Dado pessoal nos termos da Lei Geral de Proteção de Dados — exige base legal, minimização e pode ser objeto de solicitação do titular |
| **Sensível** | Dado pessoal sensível (art. 5º, II da LGPD) — exige tratamento ainda mais restrito que LGPD comum |
| **Crítico** | Perda ou corrupção deste dado tem impacto operacional severo, independente de ser ou não confidencial |

## Classificação por dado (representativa, não exaustiva)

| Dado | Classificações | Observação |
|---|---|---|
| CPF/CNPJ (Cliente, Motorista, Fornecedor) | LGPD (CPF), Confidencial | CNPJ é dado público por natureza (Receita Federal o publica); CPF é LGPD |
| CNH do Motorista (número, digitalização) | LGPD, Confidencial, Crítico | Bloqueia a operação (Motorista `Bloqueado`) se vencida — ver [`../domain/001-cadastros.md`](../domain/001-cadastros.md) |
| Exame toxicológico do Motorista | LGPD, **Sensível**, Confidencial | Dado de saúde — o mais restrito do sistema |
| Endereço (VO usado por Cliente, Motorista, Filial) | LGPD quando associado a pessoa física; Interno quando associado a pessoa jurídica/Filial | |
| Receita/Custo Previsto e Realizado, Margem (Viagem) | Financeiro, Confidencial, Crítico | Ver [`../flows/005-FINANCEIRO.md`](../flows/005-FINANCEIRO.md) |
| CT-e / MDF-e (documento fiscal) | Fiscal, Crítico; **Público** para as partes da operação (cliente, transportadora) | Ver [`../flows/009-FISCAL.md`](../flows/009-FISCAL.md) |
| Posição de Veículo (GPS) | Interno, Crítico | Crítico para operação em tempo real, não para compliance |
| Trilha de Auditoria (`audit`) | Confidencial, Crítico | Acesso tipicamente restrito a Auditor/Administrador SaaS (ver [`../product/PERSONAS.md`](../product/PERSONAS.md)) |
| Comentários internos (D023) | Interno ou Confidencial | Depende da visibilidade escolhida no momento do comentário |
| Credenciais/senha de Usuário | Crítico, Confidencial | Nunca armazenada em texto claro em nenhuma camada — nota de segurança, não apenas classificação de dado |
| Dados cadastrais gerais do Cliente (razão social, contato comercial) | Interno | Não é LGPD quando a Pessoa Jurídica é o titular, mas o Contato do Cliente (pessoa física) sim |
| Platform Reference Data (País/Estado/Município — D046) | **Público** | Nenhuma restrição — é informação pública por natureza |

## Como este documento se conecta ao resto

- **RBAC**: toda classificação "Confidencial"/"Financeiro"/"Sensível" é um sinal direto de que
  `RBAC_MATRIX.md` (próxima etapa) precisa restringir por papel, não apenas por módulo.
- **LGPD**: todo dado marcado "LGPD"/"Sensível" é candidato a aparecer em uma futura rotina de
  exportação/anonimização a pedido do titular (ver
  [`../architecture/security-rbac-lgpd.md`](../architecture/security-rbac-lgpd.md)).
- **Retenção**: dado Fiscal/Financeiro tem prazo mínimo legal — ver
  [`007-DATA_RETENTION.md`](./007-DATA_RETENTION.md).
- **Volume**: classificação de dado não substitui classificação de volume (D049) — um dado pode ser
  simultaneamente "Baixo volume" e "Crítico" (ex: credenciais de Usuário).

## Como este documento cresce

Assim como [`002-MASTER_DATA.md`](./002-MASTER_DATA.md) e
[`003-TRANSACTIONAL_DATA.md`](./003-TRANSACTIONAL_DATA.md), esta tabela não pretende cobrir as
~150 entidades esperadas de uma vez — cresce conforme cada categoria de
[`../domain/`](../domain/) é detalhada, priorizando sempre os dados marcados LGPD/Sensível/Fiscal/
Financeiro primeiro, por serem os de maior risco se esquecidos.

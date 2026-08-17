# UBIQUITOUS_LANGUAGE.md — Dicionário Oficial de Nomenclatura

## Diferença em relação ao GLOSSARY.md

[`../product/GLOSSARY.md`](../product/GLOSSARY.md) **explica o que os termos significam**
(o que é um CT-e, o que é Recapagem). Este documento **define como todos — negócio, documentação e
código — devem nomear as coisas**. Um termo pode estar corretamente definido no GLOSSARY e, mesmo
assim, ter um sinônimo proibido em nomes técnicos (ex: "OS" é uma abreviação aceitável em um botão
de tela, mas nunca em uma classe ou endpoint). Este documento resolve esse tipo de decisão.

Este é o único lugar onde esse tipo de decisão é tomada. Quando [`ENTITY_CATALOG.md`](./ENTITY_CATALOG.md)
catalogar uma entidade nova, o nome usado ali precisa já estar aqui — nunca o
contrário.

## Princípio: duas camadas de nomenclatura

Todo conceito de negócio pode ter até dois nomes oficiais, nunca mais:

- **Negócio/UI** — o termo usado em conversas com o usuário, telas, relatórios. Prioriza a
  linguagem real do setor de transporte (a mesma do [`GLOSSARY.md`](../product/GLOSSARY.md)), mesmo
  quando coloquial (ex: "Cavalo Mecânico").
- **Código/API** — o termo usado em classes, campos, endpoints, eventos. Prioriza precisão e
  formalidade sobre coloquialismo, e é sempre em português (D028), com uma única exceção proposital
  registrada abaixo (`Tenant`).

Quando os dois nomes coincidem (a maioria dos casos), a tabela abaixo mostra o mesmo valor nas duas
colunas. Abreviações (ex: "OS", "CT-e" falado como "cetê") são toleradas em copy curta de UI (botões,
títulos), mas **nunca** em nomes de classe, campo, endpoint ou evento.

## Regras oficiais

| Conceito | Negócio/UI | Código/API | Nunca usar | Nota |
|---|---|---|---|---|
| Entidade principal de transporte | Viagem | `Viagem` | ~~Frete~~ como nome de entidade | "Frete" continua válido como substantivo geral do setor ("tabela de frete", "cotação de frete") — nunca como nome da entidade/classe. |
| Unidade motora da composição | Cavalo Mecânico | `VeiculoTracionador` | ~~Cavalo~~ isolado em nomes técnicos | Ver [`GLOSSARY.md`](../product/GLOSSARY.md), "Cavalo Mecânico". O termo de negócio é coloquial e correto para UI; o código usa o nome tecnicamente mais preciso. |
| Categoria de unidade rebocada | Implemento | `Implemento` | ~~Carreta~~ quando o conceito abranger todos os tipos | "Carreta" continua válido quando se fala especificamente do semirreboque (ver GLOSSARY) — não quando o código/tela trata da categoria em geral. |
| Documento interno de manutenção | Ordem de Serviço | `OrdemServico` | ~~OS~~ em nomes de classe/campo/endpoint | "OS" tolerado em copy curta de UI (ex: botão "Nova OS"), nunca em código. |
| As três dimensões de status da Viagem | Status Operacional / Status Fiscal / Status Financeiro | `status_operacional` / `status_fiscal` / `status_financeiro` | ~~status~~ genérico quando a dimensão importa | Ver [`../product/DECISIONS.md`](../product/DECISIONS.md), D020. Usar "status" sem qualificador é aceitável apenas quando o contexto já deixou claro qual dimensão (raro). |
| Comprovante de entrega | Canhoto | `Canhoto` | ~~Comprovante~~ genérico | Ver [`GLOSSARY.md`](../product/GLOSSARY.md), "Canhoto". |
| Motorista | Motorista | `Motorista` | ~~Driver~~ | Nomenclatura de domínio em português (D028); `driver`/`Driver` só aparece em nomes de pasta já congelados (`apps/api/src/modules/drivers`), nunca em nomes de classe. |
| Item de rodagem | Pneu | `Pneu` | ~~Roda~~ como sinônimo | Pneu e roda/aro são componentes fisicamente distintos; tratar como sinônimos gera erro de cadastro. |
| Verificação estruturada (ver [`../flows/007-CHECKLIST.md`](../flows/007-CHECKLIST.md)) | Checklist | `Checklist` | ~~Lista de Verificação~~ | Termo já consolidado no setor em português aportuguesado; traduzir forçadamente reduz reconhecimento pelo usuário. |
| Identificação individual de pneu | Marca de Fogo | `MarcaDeFogo` | — | Ver [`GLOSSARY.md`](../product/GLOSSARY.md) — sentido de pneu é o primário no GestorFrete; sentido pecuário é secundário (integração GestorPec). |
| Empresa cliente da plataforma | Transportadora | `Tenant` | ~~Empresa~~ isolado, ~~Cliente~~ (ambíguo com Cliente/Embarcador) | **Exceção proposital a D028**: `Tenant` é mantido em inglês no código por ser terminologia consolidada de arquitetura SaaS multi-tenant (ver [`../architecture/multi-tenancy.md`](../architecture/multi-tenancy.md)); "Transportadora" é o termo usado com o usuário. |
| Cliente que contrata o frete | Cliente (Embarcador) | `Cliente` | ~~Embarcador~~ isolado em código | "Embarcador" é o termo técnico do setor, mantido entre parênteses no negócio/UI para reforçar precisão; o código usa a forma curta `Cliente`, já suficientemente inequívoca dentro do bounded context `crm`/`freight`. |

## Como este documento cresce

Cada entidade nova catalogada em [`ENTITY_CATALOG.md`](./ENTITY_CATALOG.md) e detalhada nos
arquivos `NNN-categoria.md` (ver [`README.md`](./README.md)) passa primeiro por aqui **apenas
quando** seu nome não é óbvio/direto (ex: uma tradução
literal sem ambiguidade não precisa de uma linha própria — só entram aqui os casos como os acima,
onde negócio e código divergem, ou onde um sinônimo é especificamente proibido). Não é objetivo
duplicar aqui o que já está trivialmente correto.

## Aplicação em código

- Nomes de eventos: português, passado, PascalCase — já registrado como D013
  (ver [`../product/EVENT_MAP.md`](../product/EVENT_MAP.md)).
- Nomes de entidades/Value Objects: português, PascalCase — D028, com a exceção `Tenant` acima.
- Nomes de bounded contexts (pastas): inglês, snake_case — já congelado, D011
  (ver [`../architecture/ddd.md`](../architecture/ddd.md)); não é linguagem de negócio, é
  nomenclatura estrutural, por isso não segue D028.
- Campos de banco de dados: a definir quando `DATA_DICTIONARY_FUNCTIONAL.md` (próxima etapa, ver
  [`../product/DECISIONS.md`](../product/DECISIONS.md)) especificar a convenção física — este
  documento define o nome conceitual, não a coluna.

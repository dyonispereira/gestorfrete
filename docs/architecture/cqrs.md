# CQRS (Command Query Responsibility Segregation)

## Por que separar leitura de escrita

Em um ERP, os modelos ideais para escrita e para leitura divergem rapidamente. Escrever um frete
exige carregar o agregado inteiro, validar invariantes e garantir consistência. Listar fretes numa
tela de dashboard exige juntar dados de `freight`, `fleet` e `drivers` de forma otimizada para
exibição — carregar agregados completos para isso seria desperdício. CQRS resolve essa tensão
tratando os dois casos como responsabilidades diferentes, em vez de forçar um único modelo a
atender ambos.

## Commands (`application/commands/`)

Um Command representa a **intenção de mudar o estado do sistema** (ex: `DespacharFreteCommand`).
Cada Command tem um handler correspondente que:

1. Carrega o(s) agregado(s) via repositório (`domain/repositories`)
2. Invoca métodos do agregado, que aplicam as regras de negócio e registram Domain Events
3. Persiste via `UnitOfWork`, que também garante a publicação dos eventos registrados

Commands nunca retornam dados de leitura ricos — no máximo um identificador ou confirmação. Se o
chamador precisa dos dados atualizados, ele faz uma Query em seguida.

## Queries (`application/queries/`)

Uma Query é **somente leitura** e nunca altera estado. Diferente de um Command, uma Query pode
contornar o `domain/` inteiramente e ler direto de `infrastructure/persistence` (ou de uma tabela/
view otimizada para leitura) quando isso for mais eficiente — não há necessidade de reconstruir
agregados completos só para exibir dados em uma tela.

## Onde isso se aplica

Nem todo bounded context precisa da separação completa (ex: com um *read model* dedicado). Para
módulos de suporte simples, Commands e Queries podem operar sobre a mesma tabela/repositório. A
separação de pastas (`commands/` vs `queries/`) existe em todos os módulos desde já para manter a
convenção consistente; a decisão de quão sofisticado o lado de leitura precisa ser (ex: projeções
assíncronas alimentadas por eventos) é tomada módulo a módulo, conforme a necessidade real de
performance aparecer — não antecipada sem necessidade.

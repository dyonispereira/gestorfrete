# 005 — Pneus

Entidades do ciclo de vida do pneu do GestorFrete. Template completo de 22 campos (ver
[`README.md`](./README.md)). Ver [`ENTITY_CATALOG.md`](./ENTITY_CATALOG.md) para o índice completo
desta categoria.

---

## Pneu

- **Objetivo**: Representa um pneu individual rastreado por toda sua vida útil — máquina de estados
  canônica em [`../flows/004-PNEUS.md`](../flows/004-PNEUS.md) (D035).
- **Responsabilidades**: Manter o ciclo de vida (`COMPRADO` → ... → `BAIXADO`); acumular Registro
  de Recapagem e Posicionamento de Pneu.
- **O que não faz**: Não decide sozinho quando recapear — é uma decisão do Almoxarife/Analista de
  Frota, informada pela Política de Recapagem.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `maintenance`
- **Principais relacionamentos**: Veículo Tracionador (referenciado, quando `INSTALADO`),
  Fornecedor/recapadora (referenciado); Registro de Recapagem, Posicionamento de Pneu (filhos do
  agregado).
- **Eventos que publica**: `PneuCadastrado`, `PneuInstalado`, `PneuEnviadoParaRecapagem`,
  `PneuSucateado`, `PneuBaixado` (já catalogados em [`../product/EVENT_MAP.md`](../product/EVENT_MAP.md)).
- **Eventos que consome**: Nenhum.
- **Invariantes**: **um pneu nunca pode estar em dois veículos ao mesmo tempo** (exemplo oficial
  registrado para `shared/INVARIANTS.md`); lista completa em `004-PNEUS.md`.
- **Regras de negócio associadas**: D015–D018 (máquina de estados + histórico).
- **Estados**: Ver `004-PNEUS.md` (fonte canônica, D035).
- **Auditoria**: D007.
- **Linha do tempo (Timeline Universal)**: ver `004-PNEUS.md`, Capacidades Transversais.
- **Anexos suportados**: foto do pneu, Marca de Fogo legível (D024).
- **Comentários suportados**: Sim (D023).
- **KPIs relacionados**: custo por pneu/km, número médio de recapagens.
- **Documentos canônicos relacionados**: `004-PNEUS.md`.
- **Evoluções futuras previstas**: leitura automatizada da Marca de Fogo.
- **Dependências obrigatórias**: Veículo Tracionador (quando instalado), Marca de Fogo (Value
  Object, ver `shared/VALUE_OBJECTS.md`, a ser escrito), Fornecedor, Modelo de Pneu.
- **Dependências proibidas**: Financeiro, CT-e, Cliente.
- **Dono da Timeline**: Aggregate Pneu (este próprio) — exemplo oficial usado nesta decisão.
- **Capacidade Offline**: Consulta Offline.

## Registro de Recapagem

- **Objetivo**: Registro histórico (D037) de cada ciclo de recapagem de um Pneu.
- **Responsabilidades**: Guardar data de envio, recapadora, resultado (aprovado/reprovado).
- **O que não faz**: Não é editável — apenas inserido.
- **Aggregate Root**: Não — parte do agregado Pneu; entidade **Histórica** (D037).
- **Bounded Context proprietário**: `maintenance`
- **Principais relacionamentos**: Pneu (N:1); Fornecedor/recapadora (N:1).
- **Eventos que publica**: Nenhum diretamente — refletido pelos eventos do próprio Pneu.
- **Eventos que consome**: Nenhum.
- **Invariantes**: o número sequencial do ciclo de recapagem nunca decresce para o mesmo Pneu.
- **Regras de negócio associadas**: D017/D018/D037.
- **Estados**: Não aplicável.
- **Auditoria**: D007.
- **Linha do tempo**: parte do Pneu.
- **Anexos suportados**: laudo da recapadora (D024).
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: custo médio de recapagem.
- **Documentos canônicos relacionados**: `004-PNEUS.md`.
- **Evoluções futuras previstas**: Nenhuma isolada.
- **Dependências obrigatórias**: Pneu, Fornecedor.
- **Dependências proibidas**: Financeiro, CT-e, Cliente, Viagem.
- **Dono da Timeline**: Aggregate Pneu.
- **Capacidade Offline**: Não.

## Posicionamento de Pneu

- **Objetivo**: Registro histórico (D037) de qual veículo/posição um Pneu ocupou em cada período —
  suporta rodízio e troca entre veículos.
- **Responsabilidades**: Permitir reconstruir, a qualquer momento, onde um Pneu estava instalado.
- **O que não faz**: Não é o mesmo que o status `INSTALADO` do Pneu — esse é o status atual; este é
  o histórico detalhado de posições.
- **Aggregate Root**: Não — parte do agregado Pneu; entidade **Histórica** (D037).
- **Bounded Context proprietário**: `maintenance`
- **Principais relacionamentos**: Pneu (N:1); Veículo Tracionador (N:1).
- **Eventos que publica**: Nenhum diretamente — refletido por `PneuInstalado`.
- **Eventos que consome**: Nenhum.
- **Invariantes**: não pode haver dois Posicionamentos de Pneu simultaneamente `Vigente` para o
  mesmo Pneu — reforça o invariante "um pneu nunca pode estar em dois veículos ao mesmo tempo".
- **Regras de negócio associadas**: D017/D018/D037.
- **Estados**: `Vigente` / `Encerrado`.
- **Auditoria**: D007.
- **Linha do tempo**: parte do Pneu.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: quilometragem rodada por posição (dianteiro/traseiro, etc.).
- **Documentos canônicos relacionados**: `004-PNEUS.md`.
- **Evoluções futuras previstas**: Nenhuma isolada.
- **Dependências obrigatórias**: Pneu, Veículo Tracionador.
- **Dependências proibidas**: Financeiro, CT-e, Cliente, Viagem.
- **Dono da Timeline**: Aggregate Pneu.
- **Capacidade Offline**: Não.

## Modelo de Pneu

- **Objetivo**: Catálogo de modelos/marcas de pneu (medida, fabricante).
- **Responsabilidades**: Ser referenciado por Pneu.
- **O que não faz**: Não guarda o histórico de um pneu específico.
- **Aggregate Root**: Sim — entidade de **Referência** (D036).
- **Bounded Context proprietário**: `maintenance`
- **Principais relacionamentos**: Pneu (referenciado).
- **Eventos que publica**: `ModeloDePneuCadastrado` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: combinação fabricante + medida única por tenant.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Ativo` / `Inativo`.
- **Auditoria**: D007.
- **Linha do tempo**: cadastro, alterações.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: vida útil média por modelo.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: Nenhuma prevista.
- **Dependências obrigatórias**: Nenhuma.
- **Dependências proibidas**: Financeiro, CT-e, Cliente, Viagem.
- **Dono da Timeline**: Aggregate Modelo de Pneu (este próprio).
- **Capacidade Offline**: Consulta Offline.

## Política de Recapagem

- **Objetivo**: Define o número máximo de recapagens permitido por Modelo de Pneu/tenant (ver
  `004-PNEUS.md`, Transições inválidas).
- **Responsabilidades**: Ser consultada antes de autorizar uma nova recapagem.
- **O que não faz**: Não força a sucata sozinha — apenas define o limite que a máquina de estados
  do Pneu respeita.
- **Aggregate Root**: Sim — entidade de **Referência** (D036).
- **Bounded Context proprietário**: `maintenance`
- **Principais relacionamentos**: Modelo de Pneu (N:1, opcional — política pode ser genérica ou por
  modelo).
- **Eventos que publica**: `PoliticaDeRecapagemAtualizada` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: número máximo de recapagens maior ou igual a zero.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Ativa` / `Inativa`.
- **Auditoria**: D007.
- **Linha do tempo**: criação, alterações.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: `004-PNEUS.md`.
- **Evoluções futuras previstas**: política dinâmica sugerida por IA a partir de dados reais de
  desgaste.
- **Dependências obrigatórias**: Nenhuma obrigatória (Modelo de Pneu é opcional).
- **Dependências proibidas**: Financeiro, CT-e, Cliente, Viagem.
- **Dono da Timeline**: Aggregate Política de Recapagem (este próprio).
- **Capacidade Offline**: Consulta Offline.

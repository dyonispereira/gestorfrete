# Product Principles — o DNA do GestorFrete

Estes princípios são o critério de desempate para qualquer decisão de produto ou de UX daqui em
diante. Quando uma feature futura parecer conflitar com um destes princípios, o princípio vence —
ou a exceção é discutida e registrada explicitamente aqui, nunca decidida silenciosamente tela a
tela. Nenhuma tela foi construída ainda; este documento existe para que, quando forem, todas
nasçam consistentes entre si.

## 1. Simplicidade acima de tudo

- **Sempre priorizar simplicidade.** Entre duas soluções que resolvem o mesmo problema, vence a
  mais simples de entender e operar — não a mais completa ou a mais "poderosa". Complexidade
  acumulada é o que torna um ERP inutilizável depois de alguns anos; é mais fácil adicionar
  complexidade quando um caso real exigir do que remover complexidade que ninguém usa.
- **Nunca obrigar mais de 3 cliques para uma operação comum.** Se uma ação do dia a dia (despachar
  um frete, marcar um documento como entregue) exige mais de 3 cliques, o fluxo está errado, não o
  usuário. Isso é um requisito de design de tela, a ser validado a cada nova funcionalidade antes
  de ser considerada pronta.

## 2. Contexto de uso define a plataforma

- **Mobile First nas telas operacionais.** Quem executa a operação no campo — motorista, conferente,
  quem faz a checklist de manutenção — está no celular, muitas vezes com conectividade instável.
  Essas telas são desenhadas para toque, tela pequena e o menor número de campos possível antes de
  qualquer coisa de desktop.
- **Desktop First para painéis administrativos.** Quem gerencia a operação — financeiro, gestão de
  frota, relatórios — está numa mesa, com tela grande e precisa comparar/analisar dados. Painéis
  administrativos são desenhados para densidade de informação em desktop primeiro, responsivos em
  seguida.

## 3. Dados nunca se perdem, nunca desaparecem sem rastro

- **Todo cadastro possuir histórico.** Toda entidade cadastrável (motorista, veículo, cliente,
  tabela de preço) mantém o histórico de alterações relevantes — não apenas o estado atual. Isso
  não é "auditoria" no sentido de compliance; é a capacidade básica de responder "o que mudou e
  quando" sobre qualquer cadastro.
- **Toda exclusão ser lógica (Soft Delete).** Nenhum registro é apagado fisicamente do banco por
  ação de usuário. "Excluir" marca o registro como inativo/removido, preservando a integridade
  referencial e o histórico de tudo que já aconteceu ao redor dele (fretes antigos com aquele
  veículo, por exemplo, continuam íntegros).
- **Todo registro possuir auditoria.** Quem criou, quem alterou, quando e (no futuro) por quê,
  registrado para todo registro de negócio — não apenas para os considerados "sensíveis". Isso é
  também a base técnica para a trilha de auditoria do bounded context `audit` e para os requisitos
  de LGPD descritos em [`../architecture/security-rbac-lgpd.md`](../architecture/security-rbac-lgpd.md).

## 4. Nenhuma ação destrutiva por acidente

- **Nenhuma operação crítica sem confirmação.** Qualquer ação irreversível ou de alto impacto
  (excluir, cancelar um frete em andamento, encerrar um contrato) exige confirmação explícita do
  usuário antes de executar — nunca dispara com um único clique acidental.

## 5. Toda listagem é pesquisável, filtrável, ordenável e exportável

- **Toda tela possuir pesquisa rápida.** Qualquer tela de listagem tem uma busca de texto livre
  sempre visível, sem exigir abrir um painel de filtros avançados para uma busca simples.
- **Todas as tabelas permitirem filtros.** Além da busca rápida, toda tabela de listagem permite
  filtrar por suas colunas relevantes (status, período, responsável, etc.).
- **Todas as tabelas permitirem ordenação.** Toda coluna que faz sentido ordenar (data, valor,
  status) é clicável para ordenar a listagem por ela.
- **Todas as tabelas permitirem exportação.** Toda listagem pode ser exportada (mínimo CSV/Excel),
  não apenas os relatórios formais.
- **Todos os relatórios exportáveis.** Todo relatório do sistema é exportável em formato adequado
  ao seu consumo (PDF para leitura/impressão, Excel/CSV para análise) — nunca uma tela que só pode
  ser vista, nunca levada para fora do sistema.

## 6. Identidade visual

- **Tema claro e escuro.** Toda interface suporta tema claro e escuro nativamente, não como um
  adicional — é uma preferência de uso prolongado (motoristas usando o app em ambientes com luz
  variada, operadores em turnos noturnos).
- **Identidade visual por empresa.** Cada transportadora (tenant) pode personalizar sua identidade
  visual dentro do produto (ao menos logo e cor de destaque) — reforça que o sistema é a ferramenta
  de trabalho *daquela* transportadora, não um software genérico de terceiros, apesar de ser
  multi-tenant por baixo.

## 7. Performance não é opcional

- **Performance como requisito obrigatório.** Performance é um requisito funcional, não uma
  otimização a ser feita depois — uma tela lenta é uma tela que não atende ao princípio de
  simplicidade nem ao de mobile first. Toda feature nova é avaliada também pelo impacto de
  performance antes de ser considerada pronta, com metas objetivas a serem detalhadas em
  [`../product/NFR.md`](./NFR.md) conforme forem definidas.

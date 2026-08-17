# GLOSSARY.md — Glossário do GestorFrete

Este glossário padroniza os termos de negócio do GestorFrete. **O termo aqui definido é o único a
ser usado** em código (nomes de entidades, campos, eventos), telas e documentação — nunca um
sinônimo genérico no lugar dele. Quando um termo novo precisar ser adotado, ele deve ser adicionado
aqui antes de aparecer em qualquer outro lugar do projeto, para evitar que o mesmo conceito acabe
com nomes diferentes em módulos diferentes.

| Termo | Definição | Módulo relacionado |
|---|---|---|
| **Cavalo Mecânico** | Unidade motora (caminhão trator) responsável por tracionar um implemento rodoviário. É o veículo automotor propriamente dito, distinto da carga que ele reboca. | `fleet` |
| **Implemento** | Termo regulatório (categoria de veículo) para qualquer unidade rebocada por um cavalo mecânico — engloba carreta, reboque e semirreboque. Usado quando se fala da categoria em geral, não de um tipo específico. | `fleet` |
| **Carreta** | Sinônimo coloquial de semirreboque: o implemento que carrega a carga, acoplado ao cavalo mecânico pela quinta roda. No sistema, é tratado como um tipo de `Implemento`. | `fleet` |
| **Bitrem** | Composição veicular formada por um cavalo mecânico e dois implementos (semirreboque + reboque), usada para aumentar a capacidade de carga dentro dos limites do CONTRAN. | `fleet` |
| **Rodotrem** | Composição veicular formada por um cavalo mecânico e dois semirreboques conectados por dolly — maior capacidade que o Bitrem, também regida por limites do CONTRAN (comprimento e peso bruto total). | `fleet` |
| **MDF-e** (Manifesto Eletrônico de Documentos Fiscais) | Documento fiscal eletrônico que consolida um ou mais CT-e (ou NF-e) transportados juntos em uma mesma viagem, exigido pela SEFAZ para o transporte de cargas consolidadas. | `documents` |
| **CT-e** (Conhecimento de Transporte Eletrônico) | Documento fiscal eletrônico que formaliza a prestação de um serviço de transporte de carga — emitido pela transportadora para cada frete. | `documents`, `freight` |
| **CIOT** (Código Identificador da Operação de Transporte) | Registro obrigatório junto à ANTT para operações de transporte realizadas por motorista autônomo (TAC), usado como comprovação da operação para fins fiscais e trabalhistas. | `freight`, `drivers` |
| **Manifesto** | Uso informal para se referir ao MDF-e. Não deve ser usado como termo técnico isolado — sempre referenciar como `MDF-e` no código e nas telas, reservando "manifesto" apenas para texto explicativo ao usuário. | `documents` |
| **Ordem de Serviço** | Documento interno que formaliza a execução de um serviço sobre um veículo, tipicamente de manutenção — abre com um problema/solicitação e fecha com o registro do que foi executado e quais peças foram usadas. | `maintenance` |
| **Marca de Fogo** | Numeração única aplicada a cada pneu na entrada em estoque, usada para rastrear o pneu individualmente por todo o ciclo de vida (instalação, rodízio, recapagens, sucata — ver [`../flows/004-PNEUS.md`](../flows/004-PNEUS.md)). O mesmo termo também é usado, secundariamente, para a marca de ferro que identifica a propriedade de um lote de animais quando a carga transportada é gado — relevante na integração com o GestorPec (ver [`VISION.md`](./VISION.md), capítulo 19). O contexto (pneu vs. carga viva) desambigua qual sentido está em uso; nunca usar o termo sem esse contexto. | `maintenance` (pneu); `freight` (carga = animal vivo) |
| **Recapagem** | Processo de renovação da banda de rodagem de um pneu desgastado, estendendo sua vida útil a um custo menor que um pneu novo — um dos eventos registrados no Ciclo do Pneu. | `maintenance` |
| **Ciclo do Pneu** | Rastreamento do histórico completo de um pneu — instalação, rodízios, recapagens sucessivas até o descarte — usado para controle de custo e segurança da frota. | `maintenance` |
| **Coleta** | Ato de retirar a carga na origem/embarcador, abrindo a execução de um frete. | `freight` |
| **Entrega** | Ato de entregar a carga no destino final, encerrando a execução de um frete — dispara a coleta do canhoto. | `freight` |
| **Romaneio** | Lista detalhada dos itens/volumes de uma carga (quantidade, peso, descrição), anexada ao CT-e e usada na conferência física no momento da coleta e da entrega. | `documents`, `freight` |
| **Canhoto** | Comprovante de entrega assinado pelo destinatário — historicamente a via destacável do documento de transporte, hoje também registrado digitalmente. É o gatilho que libera o faturamento do frete. | `documents`, `freight`, `financial` |
| **Haver** | Valor de crédito acumulado por um motorista (ou outro terceiro) a ser recebido da transportadora, apurado a partir dos fretes realizados descontados de adiantamentos. | `financial`, `drivers` |
| **Adiantamento** | Valor entregue ao motorista antes ou durante a viagem para cobrir despesas da rota (combustível, pedágio, alimentação), a ser descontado na apuração do haver. | `financial`, `drivers` |
| **Centro de Custo** | Classificação usada para alocar despesas (combustível, manutenção, pedágio) a uma unidade específica da operação (veículo, filial, departamento), permitindo apurar rentabilidade por unidade. | `financial` |

## Regras de uso deste glossário

- Um termo definido aqui nunca deve ser substituído por um sinônimo genérico no código ou na
  interface (ex: nunca "Reboque Genérico" no lugar de `Implemento`, nunca "Comprovante" no lugar de
  `Canhoto`).
- Quando um bounded context precisar de um termo que ainda não está aqui, o termo deve ser proposto
  para adição neste documento antes de ser usado em código — mantendo `GLOSSARY.md` sempre a fonte
  única de verdade da linguagem ubíqua do produto (ver
  [`../architecture/ddd.md`](../architecture/ddd.md), seção "Ubiquitous Language").
- Este glossário cresce por sprint, junto com os demais documentos de produto — não é objetivo
  esgotar todo o vocabulário do setor de uma vez.

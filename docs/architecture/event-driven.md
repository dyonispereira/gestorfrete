# Event-Driven Architecture

## O problema que isso resolve

Bounded contexts precisam reagir ao que acontece uns nos outros (quando um frete é concluído,
`financial` precisa gerar o repasse ao motorista; `notifications` precisa avisar o cliente). Se
`freight` chamasse `financial` diretamente, os dois módulos ficariam acoplados — mudanças em um
quebrariam o outro, e testar um exigiria subir o outro também. Domain Events resolvem isso: quem
publica o evento não sabe (nem precisa saber) quem vai reagir a ele.

## Domain Events

Um Domain Event (`shared_kernel/domain/domain_event.py`) é um fato imutável que já aconteceu (ex:
`FreteConcluidoEvent`), nomeado no passado. Agregados registram eventos através de
`BaseAggregateRoot.record_event()` enquanto aplicam suas regras de negócio; o `UnitOfWork`
(`shared_kernel/infrastructure/unit_of_work.py`) garante que os eventos só são publicados no
barramento **depois** que a transação de banco é confirmada — nunca antes, para evitar que outros
módulos reajam a uma mudança que acabou sendo revertida.

## RabbitMQ como barramento

`core/messaging/rabbitmq_client.py` fornece a conexão robusta compartilhada com RabbitMQ. Cada
bounded context que publica eventos tem seu próprio `infrastructure/messaging/` com os publishers;
cada bounded context que consome eventos de outros tem seus consumers na mesma pasta. O contrato
abstrato (`EventBus` em `shared_kernel/application/event_bus.py`) existe para que `application/`
dependa de uma interface, não da biblioteca `aio-pika` diretamente.

## Consistência eventual

Comunicação via eventos implica **consistência eventual** entre bounded contexts: depois que um
frete é concluído, pode levar alguns milissegundos até que o repasse financeiro correspondente
seja criado. Isso é uma troca deliberada por desacoplamento e escalabilidade — bounded contexts
podem ser escalados, implantados e (no limite) ter incidentes de forma independente uns dos
outros. Casos que exigem consistência imediata (ex: validar que o veículo de um frete existe *no
momento* da criação do frete) devem ser resolvidos dentro do mesmo bounded context ou via
consulta síncrona explícita, não via eventos.

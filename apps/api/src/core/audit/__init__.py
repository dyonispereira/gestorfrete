"""Escrita da trilha de auditoria (`logs_auditoria`, D007/D037/D109) — infraestrutura transversal
usada por qualquer bounded context que precise provar que uma mudança crítica aconteceu (D344).
Distinto de `core.observability` (logs técnicos operacionais, stdout, não persistidos em banco,
descartáveis) — `logs_auditoria` é o registro de negócio imutável, nunca editado nem apagado.
"""

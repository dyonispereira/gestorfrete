"""Enforcement real de `Idempotency-Key` (D211, `docs/api/IDEMPOTENCY.md`) — V1 Operational
Hardening, Parte 6. Antes desta rodada, só 2 rotas liam o header e nenhuma deduplicava de fato
(D418, gap do Go-Live Audit). Redis-backed, escopo `(tenant_id, Idempotency-Key)`, 24h de retenção.
"""

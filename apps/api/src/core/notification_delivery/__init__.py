"""Mecanismo interno de entrega de notificações (envio efetivo por push/e-mail/
in-app) — infraestrutura transversal, nunca um bounded context de produto
(D336, Sprint 11 Lote 1.1).

Distinto de `notification_center` (`modules/notification_center/`), que é o
bounded context de produto dono das entidades `Notificação`/`Preferência de
Canal de Notificação` (D323) e do contrato já congelado em
`docs/api/086-notifications.md`: `notification_center` decide *o quê* e
*para quem* notificar; este pacote implementa *como* o envio chega ao canal
externo (adapter de push/e-mail/SMS), do mesmo jeito que `core.storage` é o
adapter de MinIO para o bounded context `storage`, nunca um segundo bounded
context concorrente.

Vazio nesta etapa — nenhum adapter concreto existe ainda; esta pasta
substitui o antigo `modules/notifications/` (scaffold da Fase 0, sem código
real, removido na auditoria de `docs/backend/BACKEND_ARCHITECTURE.md`).
"""

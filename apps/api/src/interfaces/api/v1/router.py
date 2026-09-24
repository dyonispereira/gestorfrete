from fastapi import APIRouter

from interfaces.api.v1.search_router import router as search_router
from modules.analytics.interfaces.api.analytical_snapshot_router import router as analytical_snapshot_router
from modules.analytics.interfaces.api.analytics_cube_router import router as analytics_cube_router
from modules.analytics.interfaces.api.consolidated_indicator_router import router as consolidated_indicator_router
from modules.analytics.interfaces.api.management_result_router import router as management_result_router
from modules.analytics.interfaces.api.metric_router import router as metric_router
from modules.ai.interfaces.api.ai_anomaly_router import router as ai_anomaly_router
from modules.ai.interfaces.api.ai_classification_router import router as ai_classification_router
from modules.ai.interfaces.api.ai_feedback_router import router as ai_feedback_router
from modules.ai.interfaces.api.ai_inference_router import router as ai_inference_router
from modules.ai.interfaces.api.ai_model_router import router as ai_model_router
from modules.ai.interfaces.api.ai_prediction_router import router as ai_prediction_router
from modules.ai.interfaces.api.ai_suggestion_router import router as ai_suggestion_router
from modules.ai.interfaces.api.computer_vision_reading_router import router as computer_vision_reading_router
from modules.crm.interfaces.api.client_router import router as client_router
from modules.documents.interfaces.api.ciot_router import router as ciot_router
from modules.documents.interfaces.api.cte_router import router as cte_router
from modules.documents.interfaces.api.fiscal_configuration_router import router as fiscal_configuration_router
from modules.documents.interfaces.api.fiscal_event_router import router as fiscal_event_router
from modules.documents.interfaces.api.mdfe_router import router as mdfe_router
from modules.drivers.interfaces.api.driver_router import router as driver_router
from modules.financial.interfaces.api.accounts_payable_router import router as accounts_payable_router
from modules.financial.interfaces.api.accounts_receivable_router import router as accounts_receivable_router
from modules.financial.interfaces.api.bank_account_router import router as bank_account_router
from modules.financial.interfaces.api.chart_of_accounts_router import router as chart_of_accounts_router
from modules.financial.interfaces.api.cost_center_router import router as cost_center_router
from modules.financial.interfaces.api.financial_reversal_router import router as financial_reversal_router
from modules.financial.interfaces.api.invoice_router import router as invoice_router
from modules.financial.interfaces.api.payment_method_router import router as payment_method_router
from modules.fleet.interfaces.api.implement_router import router as implement_router
from modules.fleet.interfaces.api.vehicle_category_router import router as vehicle_category_router
from modules.freight.interfaces.api.collection_router import router as collection_router
from modules.freight.interfaces.api.delivery_router import router as delivery_router
from modules.freight.interfaces.api.manifest_router import router as manifest_router
from modules.freight.interfaces.api.occurrence_router import router as occurrence_router
from modules.freight.interfaces.api.timeline_router import router as timeline_router
from modules.freight.interfaces.api.trip_attachment_router import router as trip_attachment_router
from modules.freight.interfaces.api.trip_comment_router import router as trip_comment_router
from modules.freight.interfaces.api.trip_financials_router import router as trip_financials_router
from modules.freight.interfaces.api.trip_router import router as trip_router
from modules.fleet.interfaces.api.odometer_reading_router import router as odometer_reading_router
from modules.fleet.interfaces.api.vehicle_availability_router import router as vehicle_availability_router
from modules.fleet.interfaces.api.vehicle_composition_router import router as vehicle_composition_router
from modules.fleet.interfaces.api.vehicle_router import router as vehicle_router
from modules.identity_access.interfaces.api.auth_router import router as auth_router
from modules.identity_access.interfaces.api.employee_router import router as employee_router
from modules.identity_access.interfaces.api.permission_router import router as permission_router
from modules.identity_access.interfaces.api.role_router import router as role_router
from modules.identity_access.interfaces.api.user_router import router as user_router
from modules.integration.interfaces.api.integration_config_router import router as integration_config_router
from modules.integration.interfaces.api.job_router import router as job_router
from modules.integration.interfaces.api.webhook_router import router as webhook_router
from modules.maintenance.interfaces.api.checklist_router import router as checklist_router
from modules.maintenance.interfaces.api.supplier_router import router as supplier_router
from modules.maintenance.interfaces.api.work_order_router import router as work_order_router
from modules.mobile.interfaces.api.driver_auth_router import router as driver_auth_router
from modules.mobile.interfaces.api.driver_delivery_router import router as driver_delivery_router
from modules.mobile.interfaces.api.driver_device_router import router as driver_device_router
from modules.mobile.interfaces.api.driver_occurrence_router import router as driver_occurrence_router
from modules.mobile.interfaces.api.driver_signature_router import router as driver_signature_router
from modules.mobile.interfaces.api.driver_sync_router import router as driver_sync_router
from modules.mobile.interfaces.api.driver_trip_router import router as driver_trip_router
from modules.notification_center.interfaces.api.notification_router import router as notification_router
from modules.reporting.interfaces.api.dashboard_router import router as dashboard_router
from modules.reporting.interfaces.api.export_router import router as export_router
from modules.reporting.interfaces.api.saved_filter_router import router as saved_filter_router
from modules.reporting.interfaces.api.saved_report_router import router as saved_report_router
from modules.reporting.interfaces.api.scheduled_update_router import router as scheduled_update_router
from modules.storage.interfaces.api.file_router import router as file_router
from modules.tenancy.interfaces.api.tenant_router import router as tenant_router
from modules.tracking.interfaces.api.geofence_router import router as geofence_router
from modules.tracking.interfaces.api.geofence_router import speed_limit_router as speed_limit_config_router
from modules.tracking.interfaces.api.heartbeat_router import router as heartbeat_router
from modules.tracking.interfaces.api.location_origin_router import router as location_origin_router
from modules.tracking.interfaces.api.telemetry_reading_router import router as telemetry_reading_router
from modules.tracking.interfaces.api.tracking_equipment_router import router as tracking_equipment_router
from modules.tracking.interfaces.api.tracking_event_router import router as tracking_event_router
from modules.tracking.interfaces.api.tracking_history_router import router as tracking_history_router
from modules.tracking.interfaces.api.tracking_provider_router import router as tracking_provider_router
from modules.tracking.interfaces.api.vehicle_position_router import router as vehicle_position_router

api_router_v1 = APIRouter(prefix="/api/v1")

# Sprint 11, Lote 2 — primeiro bounded context real (D332: implementa exatamente
# 001-authentication.md a 005-permissions.md, já congelados). Cada bounded context futuro
# registra seu próprio router aqui, na ordem em que for implementado.
api_router_v1.include_router(auth_router)
api_router_v1.include_router(tenant_router)
api_router_v1.include_router(user_router)
api_router_v1.include_router(role_router)
api_router_v1.include_router(permission_router)

# Sprint 11, Lote 3 — Cadastros (D353: cada agregado no bounded context real que já o possuía por
# RBAC, nunca um modules/cadastros/ unificado).
api_router_v1.include_router(client_router)
api_router_v1.include_router(supplier_router)
api_router_v1.include_router(driver_router)
api_router_v1.include_router(employee_router)
api_router_v1.include_router(cost_center_router)

# Sprint 11, Lote 4 — Frota (D361-D368). `vehicle_availability_router` é registrado **antes** de
# `vehicle_router`: os dois usam o prefixo `/veiculos` e `GET /veiculos/disponibilidade` (literal)
# precisa ser resolvido antes de `GET /veiculos/{vehicle_id}` (genérico) tentar capturar
# "disponibilidade" como se fosse um UUID — mesmo cuidado de `/drivers/me`, Lote 3.
api_router_v1.include_router(vehicle_availability_router)
api_router_v1.include_router(vehicle_router)
api_router_v1.include_router(vehicle_category_router)
api_router_v1.include_router(implement_router)
api_router_v1.include_router(vehicle_composition_router)
api_router_v1.include_router(odometer_reading_router)

# Sprint 11, Lote 5 — Operação/Viagens (D369-D381). Todos os quatro routers usam o prefixo
# `/viagens`, mas cada sub-recurso tem um número de segmentos de path diferente do de
# `GET /viagens/{trip_id}` (um segmento) — sem colisão possível, diferente do caso
# `/veiculos/disponibilidade` vs `/veiculos/{id}` do Lote 4, então a ordem de registro aqui não
# importa.
api_router_v1.include_router(trip_router)
api_router_v1.include_router(delivery_router)
api_router_v1.include_router(occurrence_router)
api_router_v1.include_router(collection_router)
api_router_v1.include_router(manifest_router)
api_router_v1.include_router(timeline_router)

# Sprint 11, Lote 6 — Financeiro (D384-D394). `trip_financials_router` mora em `freight` (D389:
# ownership segue o domínio, não o tema do lote) mas é registrado aqui, junto ao resto do lote —
# `/viagens/{trip_id}/financeiro` tem mais segmentos que `GET /viagens/{trip_id}` (trip_router),
# então não há colisão de rota possível (mesmo raciocínio do Lote 5).
api_router_v1.include_router(trip_financials_router)
api_router_v1.include_router(chart_of_accounts_router)
api_router_v1.include_router(bank_account_router)
api_router_v1.include_router(accounts_payable_router)
api_router_v1.include_router(accounts_receivable_router)
api_router_v1.include_router(invoice_router)
api_router_v1.include_router(payment_method_router)
api_router_v1.include_router(financial_reversal_router)

# Sprint 11, Lote 7 — Fiscal (D396-D400). Sem colisão de rota: `ctes`/`mdfes`/`ciots`/
# `fiscal_configuration`/`fiscal_event` usam prefixos próprios, nenhum compartilhado com lote
# anterior.
api_router_v1.include_router(cte_router)
api_router_v1.include_router(mdfe_router)
api_router_v1.include_router(ciot_router)
api_router_v1.include_router(fiscal_event_router)
api_router_v1.include_router(fiscal_configuration_router)

# Sprint 11, Lote 8 — Rastreamento (D402-D406). `vehicle_position_router`/`telemetry_reading_router`/
# `tracking_history_router` compartilham o prefixo `/vehicles/{vehicle_id}/tracking`, mas cada um
# tem um sufixo de path diferente (`/positions`/`/telemetry`/`/history`) — sem colisão possível,
# mesmo raciocínio do Lote 5 (`/viagens`). Só leitura nesses três (D286) — nenhum `POST` público de
# dado bruto; `TrackingIngestion` (D402) nunca é exposta por HTTP.
api_router_v1.include_router(tracking_provider_router)
api_router_v1.include_router(tracking_equipment_router)
api_router_v1.include_router(location_origin_router)
api_router_v1.include_router(vehicle_position_router)
api_router_v1.include_router(telemetry_reading_router)
api_router_v1.include_router(heartbeat_router)
api_router_v1.include_router(tracking_event_router)
api_router_v1.include_router(geofence_router)
api_router_v1.include_router(speed_limit_config_router)
api_router_v1.include_router(tracking_history_router)

# Sprint 11, Lote 9 — Mobile/App Motorista (D407-D411). `driver_trip_router`/`driver_occurrence_
# router`/`driver_delivery_router` compartilham o prefixo `/mobile/trips`, cada sufixo de path
# distinto (mesmo raciocínio do Lote 5/8). Comandos de Viagem/Ocorrência/Entrega/Canhoto reutilizam
# as mesmas Application Services de `freight` (D303) — nenhuma segunda implementação de regra de
# negócio nasce aqui.
api_router_v1.include_router(driver_auth_router)
api_router_v1.include_router(driver_device_router)
api_router_v1.include_router(driver_trip_router)
api_router_v1.include_router(driver_occurrence_router)
api_router_v1.include_router(driver_delivery_router)
api_router_v1.include_router(driver_signature_router)
api_router_v1.include_router(driver_sync_router)

# Sprint 11, Lote 10 — Recursos Transversais (D412-D417). BI (062-070) e IA (071-077) explicitamente
# adiados pelo usuário; 084/085 (Relatórios/Exportações) não geram rota própria (D326, reconciliados
# com o Lote 11/BI, também adiado). `trip_attachment_router`/`trip_comment_router` vivem em
# `freight` (dono do recurso pai, D316) mas reaproveitam `shared.collaboration.Attachment`/`Comment`
# já existentes desde o Lote 5 (D371) — só a camada HTTP nasce aqui. `webhook_router`/`job_router`
# `webhook_router` é registrado **antes** de `integration_config_router`: os dois compartilham o
# prefixo `/integrations`, e `/integrations/webhooks` (path literal) precisa ser resolvido antes de
# `/integrations/{config_id}` (genérico) tentar capturar "webhooks" como se fosse um UUID — mesmo
# cuidado de `/veiculos/disponibilidade` (Lote 4) e `/drivers/me` (Lote 3). `job_router` usa o
# prefixo próprio `/jobs` (`089-jobs.md`), sem colisão possível.
api_router_v1.include_router(file_router)
api_router_v1.include_router(trip_attachment_router)
api_router_v1.include_router(trip_comment_router)
api_router_v1.include_router(search_router)
api_router_v1.include_router(notification_router)
api_router_v1.include_router(webhook_router)
api_router_v1.include_router(job_router)
api_router_v1.include_router(integration_config_router)

# Sprint 11, Lote 11 — BI (D418-D422). `analytics` lê os módulos operacionais (D090/D149); nenhum
# módulo operacional importa `analytics`/`reporting` (D421, novo contrato do import-linter).
# Prefixos próprios (`/analytics/*`, `/reporting/*`), nenhuma colisão possível com lote anterior;
# `dashboard_router` já resolve `/reporting/dashboards/{id}/commands/share` corretamente por ter
# mais segmentos que `/reporting/dashboards/{id}` (mesmo raciocínio do Lote 5/8/9), sem exigir
# ordem especial de registro.
api_router_v1.include_router(metric_router)
api_router_v1.include_router(consolidated_indicator_router)
api_router_v1.include_router(analytical_snapshot_router)
api_router_v1.include_router(analytics_cube_router)
api_router_v1.include_router(dashboard_router)
api_router_v1.include_router(saved_filter_router)
api_router_v1.include_router(saved_report_router)
api_router_v1.include_router(export_router)
api_router_v1.include_router(scheduled_update_router)

# Lote 4 — Resultado Gerencial. Mesma direção D090/D149 acima: `analytics` lê `freight`/
# `financial`/`maintenance`/`fleet`/`drivers`/`crm` diretamente, nunca escreve de volta. Prefixo
# próprio (`/analytics/resultado-gerencial/*`), sem colisão com os routers de BI acima.
api_router_v1.include_router(management_result_router)

# Sprint 11, Lote 12 — IA (D423-D426). `ai` nunca escreve em módulo operacional (D161/D426, novo
# contrato do import-linter); `AIInferenceEngine` nunca alcançável por HTTP. Prefixos próprios
# (`/ai/*`), nenhuma colisão possível com lote anterior.
api_router_v1.include_router(ai_model_router)
api_router_v1.include_router(ai_inference_router)
api_router_v1.include_router(ai_suggestion_router)
api_router_v1.include_router(ai_prediction_router)
api_router_v1.include_router(ai_classification_router)
api_router_v1.include_router(ai_anomaly_router)
api_router_v1.include_router(computer_vision_reading_router)
api_router_v1.include_router(ai_feedback_router)

# Sprint 15 — Manutenção/Checklist (`domain/004-manutencao.md` reconciliação, D101/D102).
# `checklist_router` chama `freight.TripInternalTransitions.await_checklist`/`.approve_checklist`
# (já existentes, D376) para fechar `AGUARDANDO_CHECKLIST→LIBERADA` de verdade — nenhuma alteração
# em `freight`. Prefixo próprio (`/checklists/*`), nenhuma colisão possível com lote anterior.
api_router_v1.include_router(checklist_router)

# Sprint 15, Parte 2 — Manutenção/Ordens de Serviço (`003-MANUTENCAO.md`). DDL já congelada em
# `relational/005-manutencao.md` antes desta Lote — só o núcleo (OS/Item/Aprovação de Custo) é
# implementado aqui; Estoque/Solicitação de Peça/Plano Preventivo ficam para depois. Prefixo
# próprio (`/ordens-servico/*`), nenhuma colisão possível com lote anterior.
api_router_v1.include_router(work_order_router)

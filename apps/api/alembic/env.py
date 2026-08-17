import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from core.config.settings import get_settings
from core.database.orm_base import Base

# Sprint 11, Lote 2 — primeiro bounded context real. Cada módulo importa seus próprios modelos só
# para que `Base.metadata` os conheça (nenhum uso direto das classes aqui) — sem este import,
# `alembic revision --autogenerate` não veria as tabelas de `tenancy`/`identity_access`/`core.audit`.
from core.audit import models as _audit_models  # noqa: F401
from modules.ai.infrastructure.persistence.models import ai_anomaly_model as _ai_anomaly_model  # noqa: F401
from modules.ai.infrastructure.persistence.models import (  # noqa: F401
    ai_classification_model as _ai_classification_model,
)
from modules.ai.infrastructure.persistence.models import ai_feedback_model as _ai_feedback_model  # noqa: F401
from modules.ai.infrastructure.persistence.models import ai_inference_model as _ai_inference_model  # noqa: F401
from modules.ai.infrastructure.persistence.models import ai_model_model as _ai_model_model  # noqa: F401
from modules.ai.infrastructure.persistence.models import ai_prediction_model as _ai_prediction_model  # noqa: F401
from modules.ai.infrastructure.persistence.models import ai_suggestion_model as _ai_suggestion_model  # noqa: F401
from modules.ai.infrastructure.persistence.models import (  # noqa: F401
    computer_vision_reading_model as _computer_vision_reading_model,
)
from modules.analytics.infrastructure.persistence.models import (  # noqa: F401
    analytical_snapshot_model as _analytical_snapshot_model,
)
from modules.analytics.infrastructure.persistence.models import (  # noqa: F401
    analytics_cube_model as _analytics_cube_model,
)
from modules.analytics.infrastructure.persistence.models import (  # noqa: F401
    consolidated_indicator_model as _consolidated_indicator_model,
)
from modules.analytics.infrastructure.persistence.models import metric_model as _metric_model  # noqa: F401
from modules.crm.infrastructure.persistence.models import client_model as _client_model  # noqa: F401
from modules.crm.infrastructure.persistence.models import (  # noqa: F401
    client_contact_model as _client_contact_model,
)
from modules.documents.infrastructure.persistence.models import ciot_model as _ciot_model  # noqa: F401
from modules.documents.infrastructure.persistence.models import (  # noqa: F401
    correction_letter_model as _correction_letter_model,
)
from modules.documents.infrastructure.persistence.models import cte_model as _cte_model  # noqa: F401
from modules.documents.infrastructure.persistence.models import (  # noqa: F401
    fiscal_configuration_model as _fiscal_configuration_model,
)
from modules.documents.infrastructure.persistence.models import (  # noqa: F401
    fiscal_event_model as _fiscal_event_model,
)
from modules.documents.infrastructure.persistence.models import mdfe_model as _mdfe_model  # noqa: F401
from modules.documents.infrastructure.persistence.models import (  # noqa: F401
    referenced_nfe_model as _referenced_nfe_model,
)
from modules.drivers.infrastructure.persistence.models import driver_model as _driver_model  # noqa: F401
from modules.financial.infrastructure.persistence.models import (  # noqa: F401
    accounts_payable_model as _accounts_payable_model,
)
from modules.financial.infrastructure.persistence.models import (  # noqa: F401
    accounts_receivable_model as _accounts_receivable_model,
)
from modules.financial.infrastructure.persistence.models import (  # noqa: F401
    bank_account_model as _bank_account_model,
)
from modules.financial.infrastructure.persistence.models import (  # noqa: F401
    chart_of_accounts_model as _chart_of_accounts_model,
)
from modules.financial.infrastructure.persistence.models import (  # noqa: F401
    cost_center_model as _cost_center_model,
)
from modules.financial.infrastructure.persistence.models import (  # noqa: F401
    financial_reversal_model as _financial_reversal_model,
)
from modules.financial.infrastructure.persistence.models import (  # noqa: F401
    invoice_model as _invoice_model,
)
from modules.financial.infrastructure.persistence.models import (  # noqa: F401
    payment_method_model as _payment_method_model,
)
from modules.freight.infrastructure.persistence.models import delivery_model as _delivery_model  # noqa: F401
from modules.freight.infrastructure.persistence.models import (  # noqa: F401
    occurrence_model as _occurrence_model,
)
from modules.freight.infrastructure.persistence.models import (  # noqa: F401
    proof_of_delivery_model as _proof_of_delivery_model,
)
from modules.freight.infrastructure.persistence.models import (  # noqa: F401
    trip_allocation_model as _trip_allocation_model,
)
from modules.freight.infrastructure.persistence.models import trip_model as _trip_model  # noqa: F401
from modules.freight.infrastructure.persistence.models import (  # noqa: F401
    trip_status_history_model as _trip_status_history_model,
)
from modules.fleet.infrastructure.persistence.models import implement_model as _implement_model  # noqa: F401
from modules.fleet.infrastructure.persistence.models import (  # noqa: F401
    odometer_reading_model as _odometer_reading_model,
)
from modules.fleet.infrastructure.persistence.models import vehicle_model as _vehicle_model  # noqa: F401
from modules.fleet.infrastructure.persistence.models import (  # noqa: F401
    vehicle_availability_model as _vehicle_availability_model,
)
from modules.fleet.infrastructure.persistence.models import (  # noqa: F401
    vehicle_category_model as _vehicle_category_model,
)
from modules.fleet.infrastructure.persistence.models import (  # noqa: F401
    vehicle_composition_model as _vehicle_composition_model,
)
from modules.fleet.infrastructure.persistence.models import (  # noqa: F401
    vehicle_document_model as _vehicle_document_model,
)
from modules.fleet.infrastructure.persistence.models import (  # noqa: F401
    vehicle_technical_sheet_model as _vehicle_technical_sheet_model,
)
from modules.identity_access.infrastructure.persistence.models import (  # noqa: F401
    identity_models as _identity_models,
)
from modules.integration.infrastructure.persistence.models import (  # noqa: F401
    integration_config_model as _integration_config_model,
)
from modules.integration.infrastructure.persistence.models import (  # noqa: F401
    job_execution_model as _job_execution_model,
)
from modules.integration.infrastructure.persistence.models import webhook_model as _webhook_model  # noqa: F401
from modules.maintenance.infrastructure.persistence.models import supplier_model as _supplier_model  # noqa: F401
from modules.mobile.infrastructure.persistence.models import (  # noqa: F401
    digital_signature_model as _digital_signature_model,
)
from modules.mobile.infrastructure.persistence.models import mobile_device_model as _mobile_device_model  # noqa: F401
from modules.mobile.infrastructure.persistence.models import (  # noqa: F401
    mobile_session_model as _mobile_session_model,
)
from modules.mobile.infrastructure.persistence.models import (  # noqa: F401
    sync_queue_item_model as _sync_queue_item_model,
)
from modules.mobile.infrastructure.persistence.models import sync_record_model as _sync_record_model  # noqa: F401
from modules.notification_center.infrastructure.persistence.models import (  # noqa: F401
    channel_preference_model as _channel_preference_model,
)
from modules.notification_center.infrastructure.persistence.models import (  # noqa: F401
    notification_model as _notification_model,
)
from modules.reporting.infrastructure.persistence.models import dashboard_model as _dashboard_model  # noqa: F401
from modules.reporting.infrastructure.persistence.models import export_model as _export_model  # noqa: F401
from modules.reporting.infrastructure.persistence.models import (  # noqa: F401
    saved_filter_model as _saved_filter_model,
)
from modules.reporting.infrastructure.persistence.models import (  # noqa: F401
    saved_report_model as _saved_report_model,
)
from modules.reporting.infrastructure.persistence.models import (  # noqa: F401
    scheduled_update_model as _scheduled_update_model,
)
from modules.storage.infrastructure.persistence.models import file_model as _file_model  # noqa: F401
from modules.tenancy.infrastructure.persistence.models import tenant_model as _tenant_model  # noqa: F401
from modules.tracking.infrastructure.persistence.models import geofence_model as _geofence_model  # noqa: F401
from modules.tracking.infrastructure.persistence.models import heartbeat_model as _heartbeat_model  # noqa: F401
from modules.tracking.infrastructure.persistence.models import (  # noqa: F401
    location_origin_model as _location_origin_model,
)
from modules.tracking.infrastructure.persistence.models import (  # noqa: F401
    speed_limit_config_model as _speed_limit_config_model,
)
from modules.tracking.infrastructure.persistence.models import (  # noqa: F401
    telemetry_reading_model as _telemetry_reading_model,
)
from modules.tracking.infrastructure.persistence.models import (  # noqa: F401
    tracking_equipment_model as _tracking_equipment_model,
)
from modules.tracking.infrastructure.persistence.models import (  # noqa: F401
    tracking_event_model as _tracking_event_model,
)
from modules.tracking.infrastructure.persistence.models import (  # noqa: F401
    tracking_provider_model as _tracking_provider_model,
)
from modules.tracking.infrastructure.persistence.models import (  # noqa: F401
    vehicle_position_model as _vehicle_position_model,
)
from shared.addresses.infrastructure.persistence.models import address_model as _address_model  # noqa: F401
from shared.collaboration.infrastructure.persistence.models import (  # noqa: F401
    attachment_model as _attachment_model,
)
from shared.collaboration.infrastructure.persistence.models import comment_model as _comment_model  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(get_settings().database_url)

    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

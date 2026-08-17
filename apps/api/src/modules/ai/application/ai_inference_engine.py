from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from core.multitenancy.context import get_current_tenant_id
from modules.ai.domain.entities.ai_anomaly import AIAnomaly
from modules.ai.domain.entities.ai_classification import AIClassification
from modules.ai.domain.entities.ai_inference import AIInference
from modules.ai.domain.entities.ai_model import AIModel
from modules.ai.domain.entities.ai_prediction import AIPrediction
from modules.ai.domain.entities.ai_suggestion import AISuggestion
from modules.ai.domain.entities.computer_vision_reading import ComputerVisionReading
from modules.ai.domain.gateways.ai_model_gateway import AIModelGateway
from modules.ai.domain.value_objects.classification_type import ClassificationType
from modules.ai.domain.value_objects.inference_origin import InferenceOrigin
from modules.ai.domain.value_objects.inference_status import InferenceStatus
from modules.ai.domain.value_objects.reading_type import ReadingType
from modules.ai.infrastructure.gateways.fake_ai_model_gateway import FakeAIModelGateway
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_anomaly_repository import (
    SqlAlchemyAIAnomalyRepository,
)
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_classification_repository import (
    SqlAlchemyAIClassificationRepository,
)
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_inference_repository import (
    SqlAlchemyAIInferenceRepository,
)
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_model_repository import (
    SqlAlchemyAIModelRepository,
)
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_prediction_repository import (
    SqlAlchemyAIPredictionRepository,
)
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_suggestion_repository import (
    SqlAlchemyAISuggestionRepository,
)
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_computer_vision_reading_repository import (
    SqlAlchemyComputerVisionReadingRepository,
)

# D424 — limiar fixo de confiança abaixo do qual uma Leitura por Visão Computacional exige revisão
# humana. `dictionary/012-ia.md` descreve isso como "Parâmetro do Tenant" configurável
# (`010-administracao.md`) — não construído nesta fundação (fora do escopo dos 10 audits pedidos);
# um limiar fixo é a simplificação mínima que ainda prova o fluxo completo (audit 4).
HUMAN_REVIEW_CONFIDENCE_THRESHOLD = Decimal("80.00")


class AIInferenceEngine:
    """D424 — mesma família de `TripInternalTransitions`/`AnalyticsCalculationEngine`: nunca
    alcançável por HTTP. Único lugar que chama `AIModelGateway.run()` e cria, na mesma transação, a
    `Inferência de IA` técnica + exatamente uma saída de negócio referenciando `inference_id`.
    D161/D164 mecanizados aqui: nenhum método escreve em `modules.freight`/`modules.fleet`/
    `modules.financial`/`modules.maintenance` — `entidade_alvo_tipo`/`entidade_alvo_id` (ou
    `leitura_origem_tipo`/`id`) são sempre referências polimórficas sem FK física, nunca resolvidas
    contra o módulo dono (D161 — IA não precisa saber se a entidade existe para opinar sobre ela)."""

    def __init__(self, gateway: AIModelGateway | None = None) -> None:
        self._gateway = gateway or FakeAIModelGateway()

    async def _run_inference(
        self, uow: SQLAlchemyUnitOfWork, *, model_id: uuid.UUID, input: dict[str, Any],
        origem: InferenceOrigin, now: datetime,
    ) -> tuple[AIModel, AIInference]:
        model_repo = SqlAlchemyAIModelRepository(uow.session)
        inference_repo = SqlAlchemyAIInferenceRepository(uow.session)

        model = await model_repo.get_by_id(model_id)
        if model is None:
            raise NotFoundError("AI_MODEL_NOT_FOUND", "Modelo de IA não encontrado.")

        result = await self._gateway.run(model=model, input=input)
        inference = AIInference.execute(
            tenant_id=get_current_tenant_id(), modelo_ia_id=model.id, modelo_ia_versao=model.versao,
            entrada=input, saida=result.output, nivel_confianca=result.confidence_level, custo=result.cost,
            origem=origem, status=InferenceStatus.SUCESSO, now=now,
        )
        await inference_repo.add(inference)
        return model, inference

    async def run_suggestion(
        self, *, model_id: uuid.UUID, input: dict[str, Any], origem: InferenceOrigin, categoria: str,
        entidade_alvo_tipo: str, entidade_alvo_id: uuid.UUID, recomendacao: str, justificativa: str,
        now: datetime,
    ) -> AISuggestion:
        async with SQLAlchemyUnitOfWork() as uow:
            _, inference = await self._run_inference(uow, model_id=model_id, input=input, origem=origem, now=now)
            repo = SqlAlchemyAISuggestionRepository(uow.session)
            suggestion = AISuggestion.create(
                tenant_id=get_current_tenant_id(), inferencia_ia_id=inference.id, categoria=categoria,
                entidade_alvo_tipo=entidade_alvo_tipo, entidade_alvo_id=entidade_alvo_id,
                recomendacao=recomendacao, justificativa=justificativa,
                nivel_confianca=inference.nivel_confianca or Decimal("0"),
            )
            await repo.add(suggestion)
            await uow.commit()
        return suggestion

    async def run_prediction(
        self, *, model_id: uuid.UUID, input: dict[str, Any], origem: InferenceOrigin, categoria: str,
        entidade_alvo_tipo: str, entidade_alvo_id: uuid.UUID, valor_previsto: Decimal,
        data_hora_validade_fim: datetime, now: datetime,
    ) -> AIPrediction:
        async with SQLAlchemyUnitOfWork() as uow:
            _, inference = await self._run_inference(uow, model_id=model_id, input=input, origem=origem, now=now)
            repo = SqlAlchemyAIPredictionRepository(uow.session)
            prediction = AIPrediction.create(
                tenant_id=get_current_tenant_id(), inferencia_ia_id=inference.id, categoria=categoria,
                entidade_alvo_tipo=entidade_alvo_tipo, entidade_alvo_id=entidade_alvo_id,
                valor_previsto=valor_previsto, nivel_confianca=inference.nivel_confianca or Decimal("0"),
                data_hora_validade_fim=data_hora_validade_fim,
            )
            await repo.add(prediction)
            await uow.commit()
        return prediction

    async def run_classification(
        self, *, model_id: uuid.UUID, input: dict[str, Any], origem: InferenceOrigin,
        tipo_classificacao: ClassificationType, entidade_alvo_tipo: str, entidade_alvo_id: uuid.UUID,
        rotulo: str, now: datetime,
    ) -> AIClassification:
        async with SQLAlchemyUnitOfWork() as uow:
            _, inference = await self._run_inference(uow, model_id=model_id, input=input, origem=origem, now=now)
            repo = SqlAlchemyAIClassificationRepository(uow.session)
            classification = AIClassification.create(
                tenant_id=get_current_tenant_id(), inferencia_ia_id=inference.id,
                tipo_classificacao=tipo_classificacao, entidade_alvo_tipo=entidade_alvo_tipo,
                entidade_alvo_id=entidade_alvo_id, rotulo=rotulo,
                nivel_confianca=inference.nivel_confianca or Decimal("0"), now=now,
            )
            await repo.add(classification)
            await uow.commit()
        return classification

    async def run_anomaly_detection(
        self, *, model_id: uuid.UUID, input: dict[str, Any], origem: InferenceOrigin,
        leitura_origem_tipo: str, leitura_origem_id: uuid.UUID, now: datetime,
    ) -> AIAnomaly:
        async with SQLAlchemyUnitOfWork() as uow:
            _, inference = await self._run_inference(uow, model_id=model_id, input=input, origem=origem, now=now)
            repo = SqlAlchemyAIAnomalyRepository(uow.session)
            anomaly = AIAnomaly.create(
                tenant_id=get_current_tenant_id(), inferencia_ia_id=inference.id,
                leitura_origem_tipo=leitura_origem_tipo, leitura_origem_id=leitura_origem_id,
                nivel_confianca=inference.nivel_confianca or Decimal("0"),
            )
            await repo.add(anomaly)
            await uow.commit()
        return anomaly

    async def run_computer_vision(
        self, *, model_id: uuid.UUID, input: dict[str, Any], origem: InferenceOrigin,
        arquivo_origem_id: uuid.UUID, tipo_leitura: ReadingType, regiao_analisada: dict[str, Any] | None,
        now: datetime,
    ) -> ComputerVisionReading:
        """D107 — `arquivo_origem_id` é sempre referência a `storage`, nunca resolvido/substituído
        aqui; `resultado_extraido` é o `output` bruto do gateway, sempre uma proposta (D161)."""

        async with SQLAlchemyUnitOfWork() as uow:
            _, inference = await self._run_inference(uow, model_id=model_id, input=input, origem=origem, now=now)
            repo = SqlAlchemyComputerVisionReadingRepository(uow.session)
            confidence = inference.nivel_confianca or Decimal("0")
            reading = ComputerVisionReading.create(
                tenant_id=get_current_tenant_id(), inferencia_ia_id=inference.id,
                arquivo_origem_id=arquivo_origem_id, tipo_leitura=tipo_leitura,
                regiao_analisada=regiao_analisada, resultado_extraido=inference.saida or {},
                nivel_confianca=confidence,
                revisao_humana_necessaria=confidence < HUMAN_REVIEW_CONFIDENCE_THRESHOLD,
            )
            await repo.add(reading)
            await uow.commit()
        return reading

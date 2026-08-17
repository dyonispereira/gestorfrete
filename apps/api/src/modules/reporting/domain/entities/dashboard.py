from __future__ import annotations

import uuid
from typing import Any

from modules.reporting.domain.value_objects.dashboard_sharing import DashboardSharing
from shared_kernel.domain.base_entity import BaseEntity


class Dashboard(BaseEntity[uuid.UUID]):
    """`dashboards_personalizados` (D152) — nunca guarda valor de KPI, só configuração/referência.
    Nenhuma coluna numérica de indicador existe nesta entidade nem na tabela física. Sem nenhuma
    coluna de auditoria na DDL congelada — `DashboardResponse` omite `audit` (D422, mesmo
    tratamento de `IntegrationConfig`/`Webhook`, Lote 10). `DELETE` reaproveita `status=ARQUIVADO`
    como soft delete (D422) — não existe `excluido_em`."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        usuario_id: uuid.UUID,
        nome: str,
        layout: dict[str, Any],
        widgets: list[dict[str, Any]],
        filtros: dict[str, Any] | None,
        permissoes_compartilhamento: DashboardSharing,
        preferencias: dict[str, Any] | None,
        status: str,
    ) -> None:
        super().__init__(id)
        self.usuario_id = usuario_id
        self.nome = nome
        self.layout = layout
        self.widgets = widgets
        self.filtros = filtros
        self.permissoes_compartilhamento = permissoes_compartilhamento
        self.preferencias = preferencias
        self.status = status

    @classmethod
    def create(
        cls, *, usuario_id: uuid.UUID, nome: str, layout: dict[str, Any], widgets: list[dict[str, Any]],
        filtros: dict[str, Any] | None, preferencias: dict[str, Any] | None,
    ) -> "Dashboard":
        return cls(
            id=uuid.uuid4(), usuario_id=usuario_id, nome=nome, layout=layout, widgets=widgets, filtros=filtros,
            permissoes_compartilhamento=DashboardSharing.PRIVADO, preferencias=preferencias, status="ATIVO",
        )

    def update(
        self, *, nome: str | None, layout: dict[str, Any] | None, widgets: list[dict[str, Any]] | None,
        filtros: dict[str, Any] | None, preferencias: dict[str, Any] | None, status: str | None,
    ) -> None:
        if nome is not None:
            self.nome = nome
        if layout is not None:
            self.layout = layout
        if widgets is not None:
            self.widgets = widgets
        if filtros is not None:
            self.filtros = filtros
        if preferencias is not None:
            self.preferencias = preferencias
        if status is not None:
            self.status = status

    def share(self, *, sharing: DashboardSharing) -> None:
        self.permissoes_compartilhamento = sharing

    def archive(self) -> None:
        """D422 — `DELETE` = soft delete via `status=ARQUIVADO`, nunca `excluido_em` (coluna
        inexistente)."""

        self.status = "ARQUIVADO"

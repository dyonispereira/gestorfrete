from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TripFinancialsViewDTO:
    """D262/D268/D389 — mesmos campos de `Trip.financials`/`Trip.snapshots`, reagrupados. Máscara
    por permissão (D267-style) já aplicada aqui: um campo `None` significa "sem permissão para ver
    este grupo", indistinguível de "valor genuinamente ausente" — mesmo padrão de
    `maintenance.work_order.view_cost`."""

    financial_status: str
    predicted_revenue: Decimal | None
    predicted_cost: Decimal | None
    predicted_margin: Decimal | None
    actual_revenue: Decimal | None
    actual_cost: Decimal | None
    actual_margin: Decimal | None
    financial_deviation: Decimal | None

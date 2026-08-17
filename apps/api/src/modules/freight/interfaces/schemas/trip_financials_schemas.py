from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from modules.freight.application.dtos.trip_financials_view_dto import TripFinancialsViewDTO


class TripFinancialsViewResponse(BaseModel):
    financial_status: str
    predicted_revenue: Decimal | None
    predicted_cost: Decimal | None
    predicted_margin: Decimal | None
    actual_revenue: Decimal | None
    actual_cost: Decimal | None
    actual_margin: Decimal | None
    financial_deviation: Decimal | None

    @staticmethod
    def from_dto(dto: TripFinancialsViewDTO) -> "TripFinancialsViewResponse":
        return TripFinancialsViewResponse(
            financial_status=dto.financial_status,
            predicted_revenue=dto.predicted_revenue,
            predicted_cost=dto.predicted_cost,
            predicted_margin=dto.predicted_margin,
            actual_revenue=dto.actual_revenue,
            actual_cost=dto.actual_cost,
            actual_margin=dto.actual_margin,
            financial_deviation=dto.financial_deviation,
        )

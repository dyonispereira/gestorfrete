from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError, ValidationError
from modules.fleet.application.dtos.vehicle_technical_sheet_dto import VehicleTechnicalSheetDTO
from modules.fleet.domain.entities.vehicle_technical_sheet import VehicleTechnicalSheet
from modules.fleet.domain.value_objects.fuel_type import FuelType
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_technical_sheet_repository import (
    SqlAlchemyVehicleTechnicalSheetRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpsertVehicleTechnicalSheetCommand(Command):
    """`PATCH /veiculos/{id}/technical-sheet` só escreve em `fichas_tecnicas_veiculo` —
    `manufacturer`/`model`/`manufacture_year`/`category_id` (que vivem em
    `veiculos_tracionadores`) são só expostos juntos na leitura (`020-vehicles.md`'s corpo de
    `PATCH` não os inclui), editados via `PATCH /veiculos/{id}` normal."""

    actor: AuthenticatedActor
    vehicle_id: uuid.UUID
    chassi: str | None
    motor: str | None
    eixos: int | None
    tara: Decimal | None
    capacidade_carga: Decimal | None
    pbt: Decimal | None
    rntrc_proprietario: str | None
    combustivel: FuelType | None


class UpsertVehicleTechnicalSheetHandler(CommandHandler[UpsertVehicleTechnicalSheetCommand, VehicleTechnicalSheetDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpsertVehicleTechnicalSheetCommand) -> VehicleTechnicalSheetDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            vehicle_repo = SqlAlchemyVehicleRepository(uow.session)
            sheet_repo = SqlAlchemyVehicleTechnicalSheetRepository(uow.session)

            vehicle = await vehicle_repo.get_by_id(command.vehicle_id)
            if vehicle is None:
                raise NotFoundError("FLEET_VEHICLE_NOT_FOUND", "Veículo não encontrado.")

            if command.chassi is not None and await sheet_repo.exists_with_chassi(command.chassi):
                raise ConflictError("FLEET_CHASSIS_ALREADY_EXISTS", "Já existe uma Ficha Técnica com este chassi.")

            sheet = await sheet_repo.get_by_vehicle_id(command.vehicle_id)
            if sheet is None:
                if command.chassi is None or command.eixos is None or command.tara is None or command.capacidade_carga is None or command.pbt is None or command.combustivel is None:
                    raise ValidationError(
                        "FLEET_TECHNICAL_SHEET_INCOMPLETE",
                        "chassis, axles, tare_weight, load_capacity, gross_vehicle_weight e fuel_type são obrigatórios na primeira gravação.",
                    )
                sheet = VehicleTechnicalSheet.create(
                    veiculo_tracionador_id=command.vehicle_id,
                    chassi=command.chassi,
                    motor=command.motor,
                    eixos=command.eixos,
                    tara=command.tara,
                    capacidade_carga=command.capacidade_carga,
                    pbt=command.pbt,
                    rntrc_proprietario=command.rntrc_proprietario,
                    combustivel=command.combustivel,
                )
            else:
                sheet.update(
                    chassi=command.chassi,
                    motor=command.motor,
                    eixos=command.eixos,
                    tara=command.tara,
                    capacidade_carga=command.capacidade_carga,
                    pbt=command.pbt,
                    rntrc_proprietario=command.rntrc_proprietario,
                    combustivel=command.combustivel,
                )
            await sheet_repo.add(sheet)

            # D082 — dado permanente: qualquer alteração aqui gera auditoria reforçada, mesmo
            # rigor de uma ação sensível, nunca uma edição silenciosa.
            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="fichas_tecnicas_veiculo",
                entidade_id=sheet.id,
                acao="ALTERACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                motivo="Alteração de dado permanente (D082) — ficha técnica do veículo.",
            )

            await uow.commit()

        return VehicleTechnicalSheetDTO.from_entity_and_vehicle(
            sheet,
            manufacturer=vehicle.fabricante,
            model=vehicle.modelo,
            manufacture_year=vehicle.ano_fabricacao,
            category_id=vehicle.categoria_veiculo_id,
        )

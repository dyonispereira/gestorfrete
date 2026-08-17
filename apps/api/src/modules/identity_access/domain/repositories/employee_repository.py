from __future__ import annotations

import uuid
from abc import abstractmethod
from datetime import datetime

from modules.identity_access.domain.entities.employee import Employee
from shared_kernel.domain.repository import Repository


class EmployeeRepository(Repository[Employee, uuid.UUID]):
    @abstractmethod
    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        status: str | None,
        search: str | None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> tuple[list[Employee], int]: ...

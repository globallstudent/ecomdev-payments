from typing import Any

from fastapi import APIRouter, status

from app.api.deps import PaymentServiceDep
from app.schemas.v1.common import ErrorOut
from app.schemas.v1.payment import PaymentCreate, PaymentRead

router = APIRouter(prefix="/payments", tags=["payments"])

NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut, "description": "Ученик не найден или удалён"}}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND,
    summary="Внести оплату",
)
async def create_payment(data: PaymentCreate, service: PaymentServiceDep) -> PaymentRead:
    return PaymentRead.model_validate(await service.create(data))

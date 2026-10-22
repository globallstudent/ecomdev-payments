from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.v1.common import Money, MoneyOut


class PaymentCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"student_id": 2, "amount": "500000", "paid_on": "2026-10-20"}]},
    )

    student_id: Annotated[int, Field(gt=0)]
    amount: Money
    paid_on: date | None = Field(default=None, description="Дата оплаты; по умолчанию сегодня (APP_TIMEZONE)")


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    amount: MoneyOut
    paid_on: date
    created_at: datetime

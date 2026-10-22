from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Payment


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, **values: Any) -> Payment:
        payment = Payment(**values)
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def list_for_student(self, student_id: int) -> list[Payment]:
        stmt = (
            select(Payment).where(Payment.student_id == student_id).order_by(Payment.paid_on.desc(), Payment.id.desc())
        )
        return list(await self.session.scalars(stmt))

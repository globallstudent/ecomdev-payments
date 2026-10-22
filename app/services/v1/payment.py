from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import NotFoundError
from app.models import Payment
from app.repositories.payment import PaymentRepository
from app.repositories.student import StudentRepository
from app.schemas.v1.payment import PaymentCreate
from app.services.v1.student import ENTITY as STUDENT


class PaymentService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.students = StudentRepository(session)
        self.payments = PaymentRepository(session)

    async def create(self, data: PaymentCreate) -> Payment:
        if not await self.students.exists(data.student_id):
            raise NotFoundError(STUDENT, data.student_id)
        payment = await self.payments.add(
            student_id=data.student_id,
            amount=data.amount,
            paid_on=data.paid_on or self.settings.today(),
        )
        await self.session.commit()
        return payment

    async def list_for_student(self, student_id: int) -> list[Payment]:
        if not await self.students.exists(student_id):
            raise NotFoundError(STUDENT, student_id)
        return await self.payments.list_for_student(student_id)

from datetime import date
from decimal import Decimal
from typing import NamedTuple

from sqlalchemy import ColumnElement, Row, Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Payment, Student


class MonthTotals(NamedTuple):
    students_total: int
    expected_total: Decimal
    paid_total: Decimal


class DebtorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _balances(start: date, end: date) -> tuple[Select, ColumnElement[Decimal]]:
        paid = func.coalesce(func.sum(Payment.amount), 0).label("paid")
        stmt = (
            select(Student.id, Student.name, Student.phone, Student.group_name, Student.monthly_fee, paid)
            .outerjoin(
                Payment,
                and_(Payment.student_id == Student.id, Payment.paid_on >= start, Payment.paid_on < end),
            )
            .where(Student.deleted_at.is_(None))
            .group_by(Student.id)
        )
        return stmt, paid

    async def list_debtors(self, start: date, end: date) -> list[Row]:
        stmt, paid = self._balances(start, end)
        stmt = stmt.having(paid < Student.monthly_fee).order_by((Student.monthly_fee - paid).desc(), Student.name)
        return list(await self.session.execute(stmt))

    async def list_balances(self, start: date, end: date) -> list[Row]:
        stmt, _ = self._balances(start, end)
        return list(await self.session.execute(stmt.order_by(Student.name)))

    async def month_totals(self, start: date, end: date) -> MonthTotals:
        active = Student.deleted_at.is_(None)
        students_total = select(func.count()).select_from(Student).where(active).scalar_subquery()
        expected_total = select(func.coalesce(func.sum(Student.monthly_fee), 0)).where(active).scalar_subquery()
        paid_total = (
            select(func.coalesce(func.sum(Payment.amount), 0))
            .join(Student, Student.id == Payment.student_id)
            .where(active, Payment.paid_on >= start, Payment.paid_on < end)
            .scalar_subquery()
        )
        row = (await self.session.execute(select(students_total, expected_total, paid_total))).one()
        return MonthTotals(int(row[0]), Decimal(row[1]), Decimal(row[2]))

from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.dates import format_month, month_bounds, parse_month
from app.repositories.debtor import DebtorRepository
from app.schemas.v1.debtor import DebtorRead, DebtorsReport, StudentBalance


class DebtorService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.settings = settings
        self.debtors = DebtorRepository(session)

    def resolve_month(self, month: str | None) -> date:
        return parse_month(month) if month else self.settings.today().replace(day=1)

    async def report(self, month: str | None = None) -> DebtorsReport:
        first_day = self.resolve_month(month)
        start, end = month_bounds(first_day)
        rows = await self.debtors.list_debtors(start, end)
        totals = await self.debtors.month_totals(start, end)
        items = [
            DebtorRead(
                student_id=row.id,
                name=row.name,
                phone=row.phone,
                group=row.group_name,
                monthly_fee=row.monthly_fee,
                paid=Decimal(row.paid),
            )
            for row in rows
        ]
        return DebtorsReport(
            month=format_month(first_day),
            count=len(items),
            total_debt=sum((item.monthly_fee - item.paid for item in items), Decimal(0)),
            students_total=totals.students_total,
            expected_total=totals.expected_total,
            paid_total=totals.paid_total,
            items=items,
        )

    async def balances(self, month: str | None = None) -> list[StudentBalance]:
        start, end = month_bounds(self.resolve_month(month))
        return [
            StudentBalance(
                student_id=row.id,
                name=row.name,
                phone=row.phone,
                group=row.group_name,
                monthly_fee=row.monthly_fee,
                paid=Decimal(row.paid),
            )
            for row in await self.debtors.list_balances(start, end)
        ]

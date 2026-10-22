from decimal import Decimal

from pydantic import BaseModel, computed_field

from app.schemas.v1.common import MoneyOut


class DebtorRead(BaseModel):
    student_id: int
    name: str
    phone: str
    group: str
    monthly_fee: MoneyOut
    paid: MoneyOut

    @computed_field
    @property
    def debt(self) -> MoneyOut:
        return self.monthly_fee - self.paid


class DebtorsReport(BaseModel):
    month: str
    count: int
    total_debt: MoneyOut
    students_total: int
    expected_total: MoneyOut
    paid_total: MoneyOut
    items: list[DebtorRead]


class StudentBalance(BaseModel):
    """One active student's position for a month (used by the web page's payment form)."""

    student_id: int
    name: str
    phone: str
    group: str
    monthly_fee: Decimal
    paid: Decimal

    @property
    def debt(self) -> Decimal:
        return max(self.monthly_fee - self.paid, Decimal(0))

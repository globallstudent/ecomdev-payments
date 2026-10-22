from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.payment import Payment


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (CheckConstraint("monthly_fee > 0", name="monthly_fee_positive"),)
    __mapper_args__ = {"eager_defaults": True}  # noqa: RUF012

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(32))
    group_name: Mapped[str] = mapped_column(String(100))
    monthly_fee: Mapped[Decimal]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None]

    payments: Mapped[list[Payment]] = relationship(back_populates="student", lazy="raise")

    def __str__(self) -> str:
        return self.name

    def __admin_repr__(self, request: object) -> str:
        return f"{self.name} · {self.group_name}"

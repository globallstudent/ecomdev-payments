import asyncio
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.database import make_engine
from app.core.dates import month_label_ru, shift_month
from app.models import Student
from app.schemas.v1.payment import PaymentCreate
from app.schemas.v1.student import StudentCreate
from app.services.v1.payment import PaymentService
from app.services.v1.student import StudentService

type Day = int | str

STUDENTS: list[tuple[str, str, str, int, list[tuple[Day, int]]]] = [
    ("Vali Karimov", "+998 90 123 45 67", "Python-1", 600_000, [("prev_last", 600_000)]),
    ("Ali Valiyev", "+998 93 555 12 40", "Python-1", 800_000, [(5, 300_000)]),
    ("Dilshod Rahimov", "+998 97 700 21 05", "Frontend-2", 500_000, [("next_first", 500_000)]),
    ("Madina Yusupova", "+998 99 410 33 18", "English B1", 450_000, [(12, 150_000)]),
    ("Sardor Aliyev", "+998 90 882 64 71", "Python-1", 600_000, [(3, 400_000)]),
    ("Nodira Qodirova", "+998 93 217 90 02", "English B1", 450_000, [(8, 200_000), (15, 150_000)]),
    ("Gulnora Saidova", "+998 91 345 67 89", "Frontend-2", 700_000, [(1, 400_000), ("last", 300_000)]),
    ("Jasur Tursunov", "+998 95 600 70 80", "English B1", 450_000, [(10, 450_000)]),
]


def resolve_day(first_day: date, day: Day) -> date:
    match day:
        case "prev_last":
            return first_day - timedelta(days=1)
        case "next_first":
            return shift_month(first_day, 1)
        case "last":
            return shift_month(first_day, 1) - timedelta(days=1)
        case int():
            return first_day.replace(day=day)
    raise ValueError(day)


async def seed() -> None:
    settings = get_settings()
    engine, sessionmaker = make_engine(settings.database_url)
    first_day = settings.today().replace(day=1)
    try:
        async with sessionmaker() as session:
            existing = await session.scalar(select(func.count()).select_from(Student))
            if existing:
                print(f"В базе уже есть ученики ({existing}) — демо-данные не добавлены.")
                return
            students = StudentService(session)
            payments = PaymentService(session, settings)
            for name, phone, group, fee, plan in STUDENTS:
                student = await students.create(
                    StudentCreate(name=name, phone=phone, group=group, monthly_fee=Decimal(fee))
                )
                for day, amount in plan:
                    await payments.create(
                        PaymentCreate(
                            student_id=student.id, amount=Decimal(amount), paid_on=resolve_day(first_day, day)
                        )
                    )
        print(f"Готово: {len(STUDENTS)} учеников и их оплаты за {month_label_ru(first_day).lower()}.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())

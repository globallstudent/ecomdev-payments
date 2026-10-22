from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import DebtorServiceDep
from app.core.dates import MONTH_PATTERN
from app.schemas.v1.debtor import DebtorsReport

router = APIRouter(prefix="/debtors", tags=["debtors"])


@router.get("", summary="Должники за месяц")
async def get_debtors(
    service: DebtorServiceDep,
    month: Annotated[
        str | None,
        Query(pattern=MONTH_PATTERN, description="Месяц YYYY-MM; по умолчанию текущий", examples=["2026-10"]),
    ] = None,
) -> DebtorsReport:
    """Ученики, которые за месяц заплатили меньше своей месячной суммы, и сколько они должны.

    Оплата относится к месяцу своей даты (`paid_on`). Удалённые ученики не учитываются.
    """
    return await service.report(month)

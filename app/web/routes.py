from collections import Counter
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Header, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import DebtorServiceDep, SettingsDep
from app.core.dates import MONTH_NAMES_RU, format_month, is_month, month_label_ru, parse_month, shift_month
from app.web.formatting import format_money, initials, search_key, students_word

router = APIRouter(include_in_schema=False)

WEB_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=WEB_DIR / "templates")
templates.env.filters.update(money=format_money, initials=initials, search_key=search_key, students_word=students_word)


@router.get("/", response_class=HTMLResponse)
async def debtors_page(
    request: Request,
    service: DebtorServiceDep,
    settings: SettingsDep,
    month: str | None = None,
    x_partial: Annotated[str | None, Header()] = None,
) -> HTMLResponse:
    # a broken ?month= in a shared link falls back to the current month instead of an error page
    report = await service.report(month if month and is_month(month) else None)
    balances = await service.balances(report.month)
    first_day = parse_month(report.month)
    today = settings.today()

    context = {
        "report": report,
        "month_label": month_label_ru(first_day),
        "month_name": MONTH_NAMES_RU[first_day.month - 1],
        "prev_month": format_month(shift_month(first_day, -1)),
        "next_month": format_month(shift_month(first_day, 1)),
        "groups": sorted(Counter(item.group for item in report.items).items()),
        "paid_percent": round(report.paid_total / report.expected_total * 100) if report.expected_total else 0,
        "page_data": {
            "month": report.month,
            "month_label": month_label_ru(first_day),
            "today": today.isoformat(),
            "students": [
                {
                    "id": b.student_id,
                    "name": b.name,
                    "group": b.group,
                    "phone": b.phone,
                    "fee": float(b.monthly_fee),
                    "paid": float(b.paid),
                }
                for b in balances
            ],
        },
    }
    # X-Partial: the page's own JS asks for just the swappable part after a month switch or a payment
    template = "_app.html" if x_partial else "debtors.html"
    response = templates.TemplateResponse(request, template, context)
    response.headers["Vary"] = "X-Partial"
    return response


@router.get("/favicon.ico")
async def favicon() -> FileResponse:
    return FileResponse(WEB_DIR / "static" / "favicon.svg", media_type="image/svg+xml")

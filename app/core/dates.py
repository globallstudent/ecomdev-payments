import re
from datetime import date

MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"
_MONTH_RE = re.compile(MONTH_PATTERN)

MONTH_NAMES_RU = (
    "январь",
    "февраль",
    "март",
    "апрель",
    "май",
    "июнь",
    "июль",
    "август",
    "сентябрь",
    "октябрь",
    "ноябрь",
    "декабрь",
)


def is_month(value: str) -> bool:
    return bool(_MONTH_RE.fullmatch(value))


def parse_month(value: str) -> date:
    """'2026-10' -> date(2026, 10, 1). The caller validates the format first."""
    year, month = value.split("-")
    return date(int(year), int(month), 1)


def format_month(first_day: date) -> str:
    return f"{first_day.year:04d}-{first_day.month:02d}"


def shift_month(first_day: date, months: int) -> date:
    index = first_day.year * 12 + first_day.month - 1 + months
    return date(index // 12, index % 12 + 1, 1)


def month_bounds(first_day: date) -> tuple[date, date]:
    """Half-open range [first day, first day of next month): no last-day arithmetic, December rolls over."""
    return first_day, shift_month(first_day, 1)


def month_label_ru(first_day: date) -> str:
    return f"{MONTH_NAMES_RU[first_day.month - 1].capitalize()} {first_day.year}"

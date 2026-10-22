from datetime import date
from decimal import Decimal

import pytest

from app.core.dates import format_month, is_month, month_bounds, month_label_ru, parse_month, shift_month
from app.web.formatting import NBSP, format_money, initials, search_key, students_word


@pytest.mark.parametrize(
    ("first_day", "months", "expected"),
    [
        (date(2026, 10, 1), 1, date(2026, 11, 1)),
        (date(2026, 12, 1), 1, date(2027, 1, 1)),
        (date(2026, 1, 1), -1, date(2025, 12, 1)),
        (date(2026, 3, 1), -14, date(2025, 1, 1)),
    ],
)
def test_shift_month(first_day: date, months: int, expected: date) -> None:
    assert shift_month(first_day, months) == expected


def test_month_bounds_are_half_open_and_roll_over_december() -> None:
    assert month_bounds(date(2026, 12, 1)) == (date(2026, 12, 1), date(2027, 1, 1))


@pytest.mark.parametrize("value", ["2026-01", "2026-12", "1999-09"])
def test_valid_months(value: str) -> None:
    assert is_month(value)
    assert format_month(parse_month(value)) == value


@pytest.mark.parametrize("value", ["2026-13", "2026-00", "2026-1", "26-10", "abc", "2026-10-01", ""])
def test_invalid_months(value: str) -> None:
    assert not is_month(value)


def test_month_label_ru() -> None:
    assert month_label_ru(date(2026, 10, 1)) == "Октябрь 2026"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("2200000.00"), f"2{NBSP}200{NBSP}000"),
        (Decimal("1500.5"), f"1{NBSP}500,50"),
        (Decimal(0), "0"),
        (450000, f"450{NBSP}000"),
    ],
)
def test_format_money(value: Decimal | int, expected: str) -> None:
    assert format_money(value) == expected


@pytest.mark.parametrize(("count", "word"), [(1, "ученика"), (8, "учеников"), (11, "учеников"), (21, "ученика")])
def test_students_word(count: int, word: str) -> None:
    assert students_word(count) == word


def test_initials_and_search_key() -> None:
    assert initials("Ali Valiyev") == "AV"
    assert search_key("Ali Valiyev", "+998 (93) 555-12-40") == "alivaliyev998935551240"

from decimal import Decimal

NBSP = " "


def format_money(value: Decimal | float) -> str:
    """2200000 -> '2 200 000', 1500.5 -> '1 500,50' (Russian grouping, no currency sign)."""
    amount = Decimal(value).quantize(Decimal("0.01"))
    text = f"{amount:,.2f}".replace(",", NBSP).replace(".", ",")
    return text.removesuffix(",00")


def students_word(count: int) -> str:
    """Genitive after «из»: из 1 ученика, из 8 учеников."""
    return "ученика" if count % 10 == 1 and count % 100 != 11 else "учеников"


def initials(name: str) -> str:
    return "".join(part[0] for part in name.split()[:2]).upper()


def search_key(*parts: str) -> str:
    return "".join(ch for ch in " ".join(parts).lower() if ch.isalnum())

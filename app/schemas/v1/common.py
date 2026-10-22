from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, PlainSerializer, StringConstraints

from app.core.dates import MONTH_PATTERN

# request side: positive, at most 2 decimal places, fits NUMERIC(12,2)
Money = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]

# response side: always a string with two decimals ("500000.00"), exact and stable
MoneyOut = Annotated[Decimal, PlainSerializer(lambda value: f"{value:.2f}", return_type=str)]

YearMonth = Annotated[str, StringConstraints(pattern=MONTH_PATTERN)]


class ErrorOut(BaseModel):
    detail: str

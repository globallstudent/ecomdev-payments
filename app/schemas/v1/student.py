from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.schemas.v1.common import Money, MoneyOut

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
Phone = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\+?[0-9 ()\-]{7,20}$")]
Group = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class StudentCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"name": "Ali Valiyev", "phone": "+998 93 555 12 40", "group": "Python-1", "monthly_fee": "800000"}
            ]
        },
    )

    name: Name
    phone: Phone
    group: Group
    monthly_fee: Money


class StudentUpdate(BaseModel):
    """PATCH: send only the fields to change; explicit null is rejected."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"monthly_fee": "850000"}]})

    name: Name | None = None
    phone: Phone | None = None
    group: Group | None = None
    monthly_fee: Money | None = None

    @field_validator("name", "phone", "group", "monthly_fee")
    @classmethod
    def reject_null(cls, value: Any) -> Any:
        if value is None:
            msg = "поле не может быть null"
            raise ValueError(msg)
        return value


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    group: str = Field(validation_alias="group_name")
    monthly_fee: MoneyOut
    created_at: datetime

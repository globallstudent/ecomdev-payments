from datetime import UTC, datetime
from typing import Any

from sqlalchemy import update
from starlette.requests import Request
from starlette_admin import DateField, DateTimeField, DecimalField, IntegerField, PhoneField, StringField, row_action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.fields import HasOne

from app.models import Student


class StudentView(ModelView):
    fields = [
        IntegerField("id", label="ID"),
        StringField("name", label="Имя", required=True),
        PhoneField("phone", label="Телефон", required=True),
        StringField("group_name", label="Группа", required=True),
        DecimalField("monthly_fee", label="Оплата в месяц", required=True),
        DateTimeField("created_at", label="Создан"),
        DateTimeField("deleted_at", label="Удалён"),
    ]
    exclude_fields_from_create = ["id", "created_at", "deleted_at"]
    exclude_fields_from_edit = ["id", "created_at", "deleted_at"]
    searchable_fields = ["name", "phone", "group_name"]
    sortable_fields = ["id", "name", "group_name", "monthly_fee", "created_at", "deleted_at"]
    fields_default_sort = [("deleted_at", False), ("name", False)]

    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        result = await request.state.session.execute(
            update(Student)
            .where(Student.id.in_([int(pk) for pk in pks]), Student.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC))
        )
        return result.rowcount

    @row_action(
        name="restore",
        text="Восстановить",
        confirmation="Вернуть ученика в списки и расчёт долгов?",
        icon_class="fa fa-rotate-left",
        submit_btn_text="Восстановить",
    )
    async def restore(self, request: Request, pk: Any) -> str:
        student = await self.find_by_pk(request, pk)
        student.deleted_at = None
        return "Ученик восстановлен"

    async def is_row_action_allowed_for_obj(self, request: Request, name: str, obj: Any) -> bool:
        if name == "restore":
            return obj.deleted_at is not None
        return await super().is_row_action_allowed_for_obj(request, name, obj)


class PaymentView(ModelView):
    fields = [
        IntegerField("id", label="ID"),
        HasOne("student", key="student", label="Ученик", required=True),
        DecimalField("amount", label="Сумма", required=True),
        DateField("paid_on", label="Дата оплаты", required=True),
        DateTimeField("created_at", label="Внесена"),
    ]
    exclude_fields_from_create = ["id", "created_at"]
    sortable_fields = ["id", "amount", "paid_on", "created_at"]
    fields_default_sort = [("paid_on", True)]

    def can_edit(self, request: Request) -> bool:  # noqa: ARG002
        return False

    def can_delete(self, request: Request) -> bool:  # noqa: ARG002
        return False

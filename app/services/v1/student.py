from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import Student
from app.repositories.student import StudentRepository
from app.schemas.v1.student import StudentCreate, StudentUpdate

ENTITY = "Ученик"


def _to_columns(values: dict[str, Any]) -> dict[str, Any]:
    if "group" in values:
        values["group_name"] = values.pop("group")
    return values


class StudentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.students = StudentRepository(session)

    async def create(self, data: StudentCreate) -> Student:
        student = await self.students.add(**_to_columns(data.model_dump()))
        await self.session.commit()
        return student

    async def list_students(self, *, group: str | None, limit: int, offset: int) -> list[Student]:
        return await self.students.list_students(group=group, limit=limit, offset=offset)

    async def list_all(self) -> list[Student]:
        return await self.students.list_students()

    async def get(self, student_id: int) -> Student:
        student = await self.students.get(student_id)
        if student is None:
            raise NotFoundError(ENTITY, student_id)
        return student

    async def update(self, student_id: int, data: StudentUpdate) -> Student:
        student = await self.get(student_id)
        values = _to_columns(data.model_dump(exclude_unset=True))
        if values:
            await self.students.update(student, **values)
            await self.session.commit()
        return student

    async def delete(self, student_id: int) -> None:
        student = await self.get(student_id)
        await self.students.soft_delete(student)
        await self.session.commit()

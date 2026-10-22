from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Select, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Student


class StudentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _active() -> Select[Student]:
        return select(Student).where(Student.deleted_at.is_(None))

    async def list_students(
        self, *, group: str | None = None, limit: int | None = None, offset: int = 0
    ) -> list[Student]:
        stmt = self._active().order_by(Student.id).offset(offset)
        if group is not None:
            stmt = stmt.where(Student.group_name == group)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(await self.session.scalars(stmt))

    async def get(self, student_id: int) -> Student | None:
        return await self.session.scalar(self._active().where(Student.id == student_id))

    async def exists(self, student_id: int) -> bool:
        stmt = select(literal(True)).where(Student.id == student_id, Student.deleted_at.is_(None))
        return bool(await self.session.scalar(stmt))

    async def add(self, **values: Any) -> Student:
        student = Student(**values)
        self.session.add(student)
        await self.session.flush()
        return student

    async def update(self, student: Student, **values: Any) -> Student:
        for field, value in values.items():
            setattr(student, field, value)
        await self.session.flush()
        return student

    async def soft_delete(self, student: Student) -> None:
        student.deleted_at = datetime.now(UTC)
        await self.session.flush()

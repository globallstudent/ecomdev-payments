from typing import Annotated, Any

from fastapi import APIRouter, Path, Query, status

from app.api.deps import PaymentServiceDep, StudentServiceDep
from app.schemas.v1.common import ErrorOut
from app.schemas.v1.payment import PaymentRead
from app.schemas.v1.student import StudentCreate, StudentRead, StudentUpdate

router = APIRouter(prefix="/students", tags=["students"])

StudentId = Annotated[int, Path(ge=1)]
NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorOut, "description": "Ученик не найден или удалён"}}


@router.post("", status_code=status.HTTP_201_CREATED, summary="Создать ученика")
async def create_student(data: StudentCreate, service: StudentServiceDep) -> StudentRead:
    return StudentRead.model_validate(await service.create(data))


@router.get("", summary="Список учеников")
async def list_students(
    service: StudentServiceDep,
    group: Annotated[str | None, Query(description="Точное название группы")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[StudentRead]:
    students = await service.list_students(group=group, limit=limit, offset=offset)
    return [StudentRead.model_validate(student) for student in students]


@router.get("/{student_id}", responses=NOT_FOUND, summary="Ученик по id")
async def get_student(student_id: StudentId, service: StudentServiceDep) -> StudentRead:
    return StudentRead.model_validate(await service.get(student_id))


@router.patch("/{student_id}", responses=NOT_FOUND, summary="Изменить ученика")
async def update_student(student_id: StudentId, data: StudentUpdate, service: StudentServiceDep) -> StudentRead:
    return StudentRead.model_validate(await service.update(student_id, data))


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
    summary="Удалить ученика (мягкое удаление, оплаты сохраняются)",
)
async def delete_student(student_id: StudentId, service: StudentServiceDep) -> None:
    await service.delete(student_id)


@router.get("/{student_id}/payments", responses=NOT_FOUND, summary="Оплаты ученика")
async def list_student_payments(student_id: StudentId, service: PaymentServiceDep) -> list[PaymentRead]:
    return [PaymentRead.model_validate(payment) for payment in await service.list_for_student(student_id)]

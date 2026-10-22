from typing import Any

import pytest
from fastapi import FastAPI
from httpx2 import AsyncClient
from sqlalchemy import func, select

from app.models import Payment, Student
from tests.factories import create_student, pay


async def test_create_returns_student_with_group_and_money_as_string(client: AsyncClient) -> None:
    student = await create_student(client, name="  Ali Valiyev ", monthly_fee="800000")

    assert student["id"] > 0
    assert student["name"] == "Ali Valiyev"
    assert student["group"] == "Python-1"
    assert student["monthly_fee"] == "800000.00"
    assert "deleted_at" not in student


@pytest.mark.parametrize(
    "payload",
    [
        {"phone": "+998 90 123 45 67", "group": "A", "monthly_fee": "1"},
        {"name": "A", "phone": "+998 90 123 45 67", "group": "A", "monthly_fee": "1", "extra": 1},
        {"name": "A", "phone": "call me", "group": "A", "monthly_fee": "1"},
        {"name": "A", "phone": "+998 90 123 45 67", "group": "A", "monthly_fee": "0"},
        {"name": "A", "phone": "+998 90 123 45 67", "group": "A", "monthly_fee": "-100"},
        {"name": "A", "phone": "+998 90 123 45 67", "group": "A", "monthly_fee": "10.555"},
        {"name": "   ", "phone": "+998 90 123 45 67", "group": "A", "monthly_fee": "1"},
    ],
    ids=["missing-name", "extra-field", "bad-phone", "zero-fee", "negative-fee", "three-decimals", "blank-name"],
)
async def test_create_rejects_invalid_payload(client: AsyncClient, payload: dict[str, Any]) -> None:
    response = await client.post("/api/v1/students", json=payload)

    assert response.status_code == 422


async def test_list_filters_by_group_and_paginates(client: AsyncClient) -> None:
    for index in range(3):
        await create_student(client, name=f"Python {index}", group="Python-1")
    await create_student(client, name="English", group="English B1")

    python = (await client.get("/api/v1/students", params={"group": "Python-1"})).json()
    page = (await client.get("/api/v1/students", params={"limit": 2, "offset": 1})).json()

    assert [s["name"] for s in python] == ["Python 0", "Python 1", "Python 2"]
    assert [s["name"] for s in page] == ["Python 1", "Python 2"]


async def test_get_unknown_student_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/students/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Ученик 999 не найден"}


async def test_patch_changes_only_sent_fields(client: AsyncClient) -> None:
    student = await create_student(client, monthly_fee="800000")

    response = await client.patch(
        f"/api/v1/students/{student['id']}", json={"group": "Python-2", "monthly_fee": "850000"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["group"] == "Python-2"
    assert body["monthly_fee"] == "850000.00"
    assert body["name"] == student["name"]


@pytest.mark.parametrize("payload", [{"name": None}, {"monthly_fee": None}, {"unknown": "x"}, {"monthly_fee": "0"}])
async def test_patch_rejects_null_unknown_and_invalid(client: AsyncClient, payload: dict[str, Any]) -> None:
    student = await create_student(client)

    response = await client.patch(f"/api/v1/students/{student['id']}", json=payload)

    assert response.status_code == 422


async def test_delete_is_soft_and_keeps_payment_history(client: AsyncClient, app: FastAPI) -> None:
    student = await create_student(client)
    await pay(client, student["id"], "300000", "2026-10-05")

    assert (await client.delete(f"/api/v1/students/{student['id']}")).status_code == 204
    assert (await client.get(f"/api/v1/students/{student['id']}")).status_code == 404
    assert (await client.get(f"/api/v1/students/{student['id']}/payments")).status_code == 404
    assert (await client.delete(f"/api/v1/students/{student['id']}")).status_code == 404
    assert (await client.get("/api/v1/students")).json() == []
    payment = await client.post("/api/v1/payments", json={"student_id": student["id"], "amount": "1"})
    assert payment.status_code == 404

    async with app.state.sessionmaker() as session:
        row = await session.get(Student, student["id"])
        payments = await session.scalar(select(func.count()).select_from(Payment))
    assert row is not None
    assert row.deleted_at is not None
    assert payments == 1

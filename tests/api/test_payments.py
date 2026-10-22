import json
from typing import Any

import pytest
from httpx2 import AsyncClient

from app.core.config import Settings
from tests.factories import create_student, pay


async def test_create_payment_and_list_newest_first(client: AsyncClient) -> None:
    student = await create_student(client)
    first = await pay(client, student["id"], "300000", "2026-10-05")
    second = await pay(client, student["id"], "200000.50", "2026-10-20")

    response = await client.get(f"/api/v1/students/{student['id']}/payments")

    assert first["amount"] == "300000.00"
    assert second["amount"] == "200000.50"
    assert response.status_code == 200
    assert [p["id"] for p in response.json()] == [second["id"], first["id"]]


async def test_paid_on_defaults_to_today_in_app_timezone(client: AsyncClient, settings: Settings) -> None:
    student = await create_student(client)

    payment = await pay(client, student["id"], "1000")

    assert payment["paid_on"] == settings.today().isoformat()


async def test_payment_for_unknown_student_returns_404(client: AsyncClient) -> None:
    response = await client.post("/api/v1/payments", json={"student_id": 404, "amount": "1000"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Ученик 404 не найден"}


@pytest.mark.parametrize(
    "payload",
    [
        {"amount": "0"},
        {"amount": "-500"},
        {"amount": "10.123"},
        {"amount": "abc"},
        {"amount": "1000", "paid_on": "2026-13-01"},
        {"amount": "1000", "note": "extra"},
    ],
    ids=["zero", "negative", "three-decimals", "not-a-number", "bad-date", "extra-field"],
)
async def test_invalid_payment_returns_422(client: AsyncClient, payload: dict[str, Any]) -> None:
    student = await create_student(client)

    response = await client.post("/api/v1/payments", json={"student_id": student["id"], **payload})

    assert response.status_code == 422


async def test_json_body_requires_content_type(client: AsyncClient) -> None:
    student = await create_student(client)

    response = await client.post("/api/v1/payments", content=json.dumps({"student_id": student["id"], "amount": "1"}))

    assert response.status_code == 422


async def test_payments_of_unknown_student_return_404(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/students/12345/payments")).status_code == 404

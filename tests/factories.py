from typing import Any

from httpx2 import AsyncClient

OCTOBER = "2026-10"

SAMPLE: list[tuple[str, str, str, list[tuple[str, str]]]] = [
    ("Vali Karimov", "Python-1", "600000", [("2026-09-30", "600000")]),
    ("Ali Valiyev", "Python-1", "800000", [("2026-10-05", "300000")]),
    ("Dilshod Rahimov", "Frontend-2", "500000", [("2026-11-01", "500000")]),
    ("Madina Yusupova", "English B1", "450000", [("2026-10-12", "150000")]),
    ("Sardor Aliyev", "Python-1", "600000", [("2026-10-03", "400000")]),
    ("Nodira Qodirova", "English B1", "450000", [("2026-10-08", "200000"), ("2026-10-15", "150000")]),
    ("Gulnora Saidova", "Frontend-2", "700000", [("2026-10-01", "400000"), ("2026-10-31", "300000")]),
    ("Jasur Tursunov", "English B1", "450000", [("2026-10-10", "450000")]),
]


async def create_student(
    client: AsyncClient,
    name: str = "Ali Valiyev",
    group: str = "Python-1",
    monthly_fee: str = "800000",
    phone: str = "+998 93 555 12 40",
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/students", json={"name": name, "phone": phone, "group": group, "monthly_fee": monthly_fee}
    )
    assert response.status_code == 201, response.text
    return response.json()


async def pay(client: AsyncClient, student_id: int, amount: str, paid_on: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"student_id": student_id, "amount": amount}
    if paid_on is not None:
        payload["paid_on"] = paid_on
    response = await client.post("/api/v1/payments", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def seed_october(client: AsyncClient) -> dict[str, int]:
    ids: dict[str, int] = {}
    for index, (name, group, fee, payments) in enumerate(SAMPLE):
        student = await create_student(
            client, name=name, group=group, monthly_fee=fee, phone=f"+998 90 000 00 {index:02d}"
        )
        ids[name] = student["id"]
        for paid_on, amount in payments:
            await pay(client, student["id"], amount, paid_on)
    return ids

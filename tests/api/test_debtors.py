import pytest
from httpx2 import AsyncClient

from app.core.config import Settings
from app.core.dates import format_month
from tests.factories import OCTOBER, create_student, pay, seed_october


async def test_october_report(client: AsyncClient) -> None:
    ids = await seed_october(client)

    response = await client.get("/api/v1/debtors", params={"month": OCTOBER})

    assert response.status_code == 200
    report = response.json()
    assert report["month"] == OCTOBER
    assert report["count"] == 6
    assert report["total_debt"] == "2200000.00"
    assert report["students_total"] == 8
    assert report["expected_total"] == "4550000.00"
    assert report["paid_total"] == "2350000.00"
    assert [(item["name"], item["debt"]) for item in report["items"]] == [
        ("Vali Karimov", "600000.00"),
        ("Ali Valiyev", "500000.00"),
        ("Dilshod Rahimov", "500000.00"),
        ("Madina Yusupova", "300000.00"),
        ("Sardor Aliyev", "200000.00"),
        ("Nodira Qodirova", "100000.00"),
    ]
    assert report["items"][1] == {
        "student_id": ids["Ali Valiyev"],
        "name": "Ali Valiyev",
        "phone": "+998 90 000 00 01",
        "group": "Python-1",
        "monthly_fee": "800000.00",
        "paid": "300000.00",
        "debt": "500000.00",
    }


async def test_only_payments_inside_the_month_count(client: AsyncClient) -> None:
    await seed_october(client)

    names = {item["name"]: item for item in (await client.get("/api/v1/debtors?month=2026-10")).json()["items"]}

    assert names["Vali Karimov"]["paid"] == "0.00"
    assert names["Dilshod Rahimov"]["paid"] == "0.00"
    assert "Gulnora Saidova" not in names
    assert "Jasur Tursunov" not in names


async def test_december_rolls_into_january(client: AsyncClient) -> None:
    student = await create_student(client, monthly_fee="100")
    await pay(client, student["id"], "60", "2026-12-31")
    await pay(client, student["id"], "70", "2027-01-01")

    december = (await client.get("/api/v1/debtors?month=2026-12")).json()
    january = (await client.get("/api/v1/debtors?month=2027-01")).json()

    assert december["items"][0]["debt"] == "40.00"
    assert january["items"][0]["debt"] == "30.00"


async def test_overpayment_is_not_a_debt(client: AsyncClient) -> None:
    student = await create_student(client, monthly_fee="100")
    await pay(client, student["id"], "150", "2026-10-02")

    report = (await client.get("/api/v1/debtors?month=2026-10")).json()

    assert report["count"] == 0
    assert report["total_debt"] == "0.00"
    assert report["paid_total"] == "150.00"


async def test_student_without_payments_owes_full_fee(client: AsyncClient) -> None:
    await create_student(client, monthly_fee="450000")

    item = (await client.get("/api/v1/debtors?month=2026-10")).json()["items"][0]

    assert (item["paid"], item["debt"]) == ("0.00", "450000.00")


async def test_empty_database(client: AsyncClient) -> None:
    report = (await client.get("/api/v1/debtors?month=2026-10")).json()

    assert report == {
        "month": "2026-10",
        "count": 0,
        "total_debt": "0.00",
        "students_total": 0,
        "expected_total": "0.00",
        "paid_total": "0.00",
        "items": [],
    }


async def test_soft_deleted_student_is_not_counted(client: AsyncClient) -> None:
    ids = await seed_october(client)
    await client.delete(f"/api/v1/students/{ids['Vali Karimov']}")

    report = (await client.get("/api/v1/debtors?month=2026-10")).json()

    assert report["count"] == 5
    assert report["students_total"] == 7
    assert report["total_debt"] == "1600000.00"


async def test_default_month_is_current_month_in_app_timezone(client: AsyncClient, settings: Settings) -> None:
    report = (await client.get("/api/v1/debtors")).json()

    assert report["month"] == format_month(settings.today())


@pytest.mark.parametrize("month", ["2026-13", "2026-00", "2026-1", "26-10", "abc", "2026-10-01"])
async def test_invalid_month_returns_422(client: AsyncClient, month: str) -> None:
    assert (await client.get("/api/v1/debtors", params={"month": month})).status_code == 422


async def test_spec_path_alias_returns_the_same_report(client: AsyncClient) -> None:
    await seed_october(client)

    canonical = await client.get("/api/v1/debtors?month=2026-10")
    alias = await client.get("/debtors?month=2026-10")

    assert alias.status_code == 200
    assert alias.json() == canonical.json()
    assert "/debtors" not in (await client.get("/openapi.json")).json()["paths"]

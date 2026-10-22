from fastapi import FastAPI
from httpx2 import AsyncClient
from starlette.requests import Request

from app.admin.views import StudentView
from app.core.config import Settings
from app.core.dates import month_label_ru
from app.models import Student
from app.web.formatting import NBSP
from tests.factories import create_student, seed_october


async def test_page_renders_debtors_for_month(client: AsyncClient) -> None:
    await seed_october(client)

    response = await client.get("/", params={"month": "2026-10"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    assert "Октябрь 2026" in html
    assert f"2{NBSP}200{NBSP}000" in html
    assert "Vali Karimov" in html
    assert "Gulnora Saidova" not in html.split('id="page-data"')[0]
    assert 'href="?month=2026-09"' in html
    assert 'href="?month=2026-11"' in html


async def test_partial_request_returns_only_the_swappable_part(client: AsyncClient) -> None:
    await seed_october(client)

    response = await client.get("/?month=2026-10", headers={"X-Partial": "1"})

    assert response.status_code == 200
    assert "<html" not in response.text
    assert 'id="page-data"' in response.text
    assert response.headers["vary"] == "X-Partial"


async def test_broken_month_falls_back_to_current_month(client: AsyncClient, settings: Settings) -> None:
    response = await client.get("/?month=2026-13")

    assert response.status_code == 200
    assert month_label_ru(settings.today().replace(day=1)) in response.text


async def test_empty_states(client: AsyncClient) -> None:
    assert "Пока нет учеников" in (await client.get("/")).text

    student = await create_student(client, monthly_fee="100")
    await client.post("/api/v1/payments", json={"student_id": student["id"], "amount": "100", "paid_on": "2026-10-03"})

    assert "За октябрь все оплатили" in (await client.get("/?month=2026-10")).text


async def test_static_assets_are_served(client: AsyncClient) -> None:
    assert (await client.get("/static/app.css")).status_code == 200
    assert (await client.get("/static/app.js")).status_code == 200
    favicon = await client.get("/favicon.ico")
    assert favicon.status_code == 200
    assert favicon.headers["content-type"] == "image/svg+xml"


async def test_admin_pages_render(client: AsyncClient) -> None:
    await create_student(client)

    for path in ("/admin/", "/admin/student/list", "/admin/payment/list"):
        assert (await client.get(path, follow_redirects=True)).status_code == 200


async def test_admin_delete_is_soft(client: AsyncClient, app: FastAPI) -> None:
    student = await create_student(client)

    async with app.state.sessionmaker() as session:
        request = Request({"type": "http", "headers": []})
        request.state.session = session
        affected = await StudentView(Student).delete(request, [str(student["id"])])
        await session.commit()

    async with app.state.sessionmaker() as session:
        row = await session.get(Student, student["id"])

    assert affected == 1
    assert row is not None
    assert row.deleted_at is not None
    assert (await client.get(f"/api/v1/students/{student['id']}")).status_code == 404

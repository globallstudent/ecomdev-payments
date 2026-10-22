# Training Center Payments

Students, payments and monthly debtors: a REST API, a phone-friendly debtors page with a payment form, and an admin panel.

**Stack:** Python 3.14, FastAPI, SQLAlchemy 2.1 (async, psycopg 3), PostgreSQL 18, Alembic, Jinja2 + vanilla JS, starlette-admin, uv, pytest + testcontainers.

## Run with Docker

Requires Docker with Compose v2.

```bash
git clone https://github.com/globallstudent/ecomdev-payments.git && cd ecomdev-payments
cp .env.example .env
docker compose up --build -d                  # PostgreSQL + app; migrations run on start
docker compose exec app python -m app.seed    # optional: 8 demo students with payments for the current month
```

| URL | |
|---|---|
| http://localhost:8000 | Debtors page + payment form |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/admin | Admin panel (students, payments) |

Ports in use? Change `APP_HOST_PORT` (default 8000) or `DB_HOST_PORT` (default 5434) in `.env`.
Stop: `docker compose down`. Stop and delete data: `docker compose down -v`.

## Run locally (without Docker for the app)

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/); it installs Python 3.14 itself.

```bash
cp .env.example .env
uv sync
docker compose up -d db          # database only, on localhost:5434
uv run alembic upgrade head
uv run python -m app.seed
uv run fastapi dev               # http://localhost:8000, auto-reload
```

## Tests

```bash
uv run pytest                    # starts a throwaway PostgreSQL 18 container — Docker must be running
uv run ruff check . && uv run ruff format --check .
uv run ty check
```

74 tests against real PostgreSQL (schema built by the Alembic migrations): API contract, debtor math (month boundaries, December → January, overpayment, soft delete, empty DB), validation, page, admin.

## API

| Method | Path | Result |
|---|---|---|
| POST | `/api/v1/students` | 201 created |
| GET | `/api/v1/students?group=&limit=&offset=` | list |
| GET | `/api/v1/students/{id}` | student, 404 |
| PATCH | `/api/v1/students/{id}` | update sent fields, 404 |
| DELETE | `/api/v1/students/{id}` | 204 soft delete, 404 |
| POST | `/api/v1/payments` | 201 created, 404 if student missing |
| GET | `/api/v1/students/{id}/payments` | student's payments, newest first |
| GET | `/api/v1/debtors?month=YYYY-MM` | debtors for the month |
| GET | `/debtors?month=YYYY-MM` | same handler at the path given in the task |

```bash
curl -X POST localhost:8000/api/v1/students -H 'Content-Type: application/json' \
  -d '{"name": "Ali Valiyev", "phone": "+998 93 555 12 40", "group": "Python-1", "monthly_fee": "800000"}'

curl -X POST localhost:8000/api/v1/payments -H 'Content-Type: application/json' \
  -d '{"student_id": 1, "amount": "300000", "paid_on": "2026-10-05"}'

curl 'localhost:8000/debtors?month=2026-10'
```

```json
{
  "month": "2026-10",
  "count": 6,
  "total_debt": "2200000.00",
  "students_total": 8,
  "expected_total": "4550000.00",
  "paid_total": "2350000.00",
  "items": [
    {"student_id": 1, "name": "Vali Karimov", "phone": "+998 90 123 45 67", "group": "Python-1",
     "monthly_fee": "600000.00", "paid": "0.00", "debt": "600000.00"}
  ]
}
```

- `Content-Type: application/json` is required for JSON bodies (FastAPI returns 422 without it).
- Money: `NUMERIC(12,2)` in the DB, `Decimal` in code, returned as strings with 2 decimals. Input accepts a number or a string, max 2 decimals, must be > 0.
- `paid_on` is optional and defaults to today in `APP_TIMEZONE` (Asia/Tashkent).
- `month` is optional and defaults to the current month. Invalid format → 422.

## How debtors are calculated

- A payment counts toward the month of its `paid_on` date.
- For month M, payments dated in `[first day of M, first day of M+1)` are summed per student.
- Debtor: paid < `monthly_fee`. `debt = monthly_fee − paid`. Sorted by debt, then name.
- One SQL query: `LEFT JOIN payments` with the date filter in `ON` (in `WHERE` it would drop students who paid nothing), `GROUP BY`, `HAVING`.
- The API and the page use the same service, so their numbers always match.

## Deleting students

`DELETE` is a soft delete: it sets `deleted_at`. The student disappears from lists and debtors and can't receive payments (404); their payment history stays. The payments foreign key is `ON DELETE RESTRICT`. In the admin panel, Delete is soft too, and Restore brings the student back.

## Debtors page

- Desktop: table with group tabs and search; payment opens in a side panel.
- Phone: two-line list; payment opens full screen.
- Paying a debtor takes two taps: row → «Принять». Amount is prefilled with the remaining debt; quick options for full/half amount and today/yesterday/custom date.
- Before submitting, the form shows the debt after payment; after submitting, the list and totals refresh.
- Month switcher updates the URL (`/?month=2026-10`), so a month can be shared as a link.
- Server-rendered (Jinja2); a small vanilla JS file switches months and posts payments to `POST /api/v1/payments`. No build step. UI text is Russian.

## Project structure

```
app/
  main.py            create_app(): API, page, static files, admin
  core/              settings, DB session, errors, month helpers
  models/            Student, Payment
  repositories/      SQL only
  schemas/v1/        API request/response models
  services/v1/       business rules and transactions
  api/v1/routes/     HTTP layer: students, payments, debtors
  web/               debtors page: templates, CSS, JS
  admin/             starlette-admin views
  seed.py            demo data
migrations/          Alembic migrations
tests/               api/, web/, date and formatting helpers
```

Dependencies point down: routes → services → repositories → models. Services commit; repositories only flush.

## What I would improve with another week

1. Authentication and roles (cashier, admin) — everything is open now.
2. A "paid for month" field separate from the payment date, with overpayments and prepayments carried to later months.
3. History of monthly fees and enrollment/leave dates — today a fee change affects past months, a new student owes for months before joining, and a deleted student disappears from past reports.
4. Correcting mistaken payments: reversal entries with an audit log instead of no correction at all.
5. Debt reminders (Telegram bot or SMS) and CI on GitHub Actions: ruff, ty, pytest, and a Playwright e2e test of the page.

## Not done / limitations

- Option A (Telegram bot) was not built; option B (web page) was.
- Payments can't be cancelled or edited via the API or the admin panel.
- No authentication.
- The admin panel is a staff tool: its forms skip API validation (amount > 0 is still enforced by a DB CHECK constraint) and allow a payment for a deleted student.
- The Golos Text font loads from Google Fonts; offline, the page falls back to the system font.
- Migrations run on container start — fine for one instance; use a separate migration step for multiple replicas.

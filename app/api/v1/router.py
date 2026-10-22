from fastapi import APIRouter

from app.api.v1.routes import debtors, payments, students

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(students.router)
api_router.include_router(payments.router)
api_router.include_router(debtors.router)

from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings
from app.core.database import SessionDep
from app.services.v1.debtor import DebtorService
from app.services.v1.payment import PaymentService
from app.services.v1.student import StudentService


def get_app_settings(request: Request) -> Settings:
    # settings of the app handling this request (a test app gets its own), not the global cache
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(get_app_settings)]


def get_student_service(session: SessionDep) -> StudentService:
    return StudentService(session)


def get_payment_service(session: SessionDep, settings: SettingsDep) -> PaymentService:
    return PaymentService(session, settings)


def get_debtor_service(session: SessionDep, settings: SettingsDep) -> DebtorService:
    return DebtorService(session, settings)


StudentServiceDep = Annotated[StudentService, Depends(get_student_service)]
PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
DebtorServiceDep = Annotated[DebtorService, Depends(get_debtor_service)]

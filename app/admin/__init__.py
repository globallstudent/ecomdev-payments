from sqlalchemy.ext.asyncio import AsyncEngine
from starlette_admin import I18nConfig
from starlette_admin.contrib.sqla import Admin

from app.admin.views import PaymentView, StudentView
from app.core.config import Settings
from app.models import Payment, Student


def build_admin(engine: AsyncEngine, settings: Settings) -> Admin:
    admin = Admin(
        engine,
        title="Учёт оплат · админка",
        base_url="/admin",
        favicon_url="/static/favicon.svg",
        i18n_config=I18nConfig(default_locale="ru"),
        secret_key=settings.secret_key,
    )
    admin.add_view(StudentView(Student, icon="fa fa-user-graduate", menu_label="Ученики", display_name="Ученик"))
    admin.add_view(PaymentView(Payment, icon="fa fa-money-bill", menu_label="Оплаты", display_name="Оплата"))
    return admin

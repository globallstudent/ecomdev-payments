from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import SessionDep

router = APIRouter(tags=["health"])


@router.get("/health", include_in_schema=False)
async def health(session: SessionDep) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ok"}

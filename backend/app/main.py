from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from app.config import settings
import app.models  # noqa: F401 — register all models for Base.metadata
from app.database import init_db, async_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Auto-seed if database is empty
    async with async_session() as session:
        from app.models.base import ChartOfAccounts
        result = await session.execute(select(func.count()).select_from(ChartOfAccounts))
        if result.scalar() == 0:
            from app.mock.seed import run_seed
            await run_seed()
    yield


app = FastAPI(
    title="FinMate API",
    description="AI 财务助理 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.api.dashboard import router as dashboard_router
from app.api.reconciliation import router as reconciliation_router
from app.api.tax import router as tax_router
from app.api.reports import router as reports_router
from app.api.cost_alloc import router as cost_alloc_router
from app.api.ai_chat import router as ai_chat_router

app.include_router(dashboard_router)
app.include_router(reconciliation_router)
app.include_router(tax_router)
app.include_router(reports_router)
app.include_router(cost_alloc_router)
app.include_router(ai_chat_router)


@app.get("/api/v1/health")
async def health_check():
    return {"code": 200, "data": {"status": "healthy"}, "message": "ok"}

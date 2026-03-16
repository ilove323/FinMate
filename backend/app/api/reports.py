from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.response import success
from app.services import report_service as svc

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

# NOTE: Specific routes MUST be declared before the wildcard /{report_type}
# to avoid FastAPI matching "drill-down" as a report_type.


@router.post("/generate")
async def generate_reports(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.generate_reports(db, body["period"])
    await db.commit()
    return success(data)


@router.get("/drill-down")
async def drill_down(
    report_type: str = Query(...), line_no: str = Query(...),
    period: str = Query(...), level: int = Query(1),
    db: AsyncSession = Depends(get_db),
):
    data = await svc.drill_down(db, report_type, line_no, period, level)
    return success(data)


@router.get("/indicators")
async def get_indicators(period: str = Query(...), db: AsyncSession = Depends(get_db)):
    data = await svc.get_indicators(db, period)
    return success(data)


@router.get("/trend")
async def get_trend(
    report_type: str = Query(...), line_no: str = Query(...),
    periods: str = Query(..., description="Comma-separated periods"),
    db: AsyncSession = Depends(get_db),
):
    period_list = [p.strip() for p in periods.split(",")]
    data = await svc.get_trend(db, report_type, line_no, period_list)
    return success(data)


@router.get("/{report_type}")
async def get_report(report_type: str, period: str = Query(...), db: AsyncSession = Depends(get_db)):
    data = await svc.get_report(db, report_type, period)
    return success(data)

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.response import success
from app.services import cost_alloc_service as svc

router = APIRouter(prefix="/api/v1/cost-alloc", tags=["cost-allocation"])


@router.get("/centers")
async def get_centers(db: AsyncSession = Depends(get_db)):
    data = await svc.get_centers(db)
    return success(data)


@router.get("/pools")
async def get_pools(period: str | None = None, db: AsyncSession = Depends(get_db)):
    data = await svc.get_pools(db, period)
    return success(data)


@router.get("/rules")
async def get_rules(db: AsyncSession = Depends(get_db)):
    data = await svc.get_rules(db)
    return success(data)


@router.post("/rules")
async def create_rule(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.create_rule(db, body)
    await db.commit()
    return success(data)


@router.put("/rules/{rule_id}")
async def update_rule(rule_id: int, body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.update_rule(db, rule_id, body)
    await db.commit()
    return success(data)


@router.post("/calculate")
async def calculate(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.calculate(db, body["period"])
    await db.commit()
    return success(data)


@router.post("/simulate")
async def simulate(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.simulate(db, body["period"], body.get("rules"))
    return success(data)


@router.get("/results")
async def get_results(period: str = Query(...), db: AsyncSession = Depends(get_db)):
    data = await svc.get_results(db, period)
    return success(data)


@router.get("/voucher")
async def get_voucher(period: str = Query(...), db: AsyncSession = Depends(get_db)):
    data = await svc.get_voucher(db, period)
    return success(data)

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.response import success
from app.services import tax_service as svc

router = APIRouter(prefix="/api/v1/tax", tags=["tax"])


@router.get("/mappings")
async def get_mappings(form_type: str | None = None, db: AsyncSession = Depends(get_db)):
    data = await svc.get_mappings(db, form_type)
    return success(data)


@router.put("/mappings/{mapping_id}")
async def update_mapping(mapping_id: int, body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.update_mapping(db, mapping_id, body["tax_line_no"], body["data_source"])
    await db.commit()
    return success(data)


@router.get("/filing/{form_type}")
async def get_filing(form_type: str, period: str = Query(...), db: AsyncSession = Depends(get_db)):
    data = await svc.get_filing(db, form_type, period)
    return success(data)


@router.post("/filing/generate")
async def generate_filing(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.generate_filing(db, body["form_type"], body["period"])
    await db.commit()
    return success(data)


@router.put("/filing/adjust")
async def adjust_line(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.adjust_line(db, body["line_id"], body["adjusted_value"], body.get("reason", ""))
    await db.commit()
    return success(data)


@router.get("/estimate")
async def get_estimate(period: str = Query(...), db: AsyncSession = Depends(get_db)):
    data = await svc.get_estimate(db, period)
    return success(data)


@router.get("/validation/{form_type}")
async def get_validation(form_type: str, period: str = Query(...), db: AsyncSession = Depends(get_db)):
    data = await svc.get_validation(db, form_type, period)
    return success(data)

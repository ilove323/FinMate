from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.response import success
from app.services import reconciliation_service as svc

router = APIRouter(prefix="/api/v1/reconciliation", tags=["reconciliation"])


@router.get("/transactions")
async def get_transactions(
    period: str | None = None, status: str | None = None,
    min_amount: float | None = None, max_amount: float | None = None,
    counterparty: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    data = await svc.get_transactions(db, period, status, min_amount, max_amount, counterparty, page, page_size)
    return success(data)


@router.get("/book-entries")
async def get_book_entries(
    period: str | None = None, account_code: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    data = await svc.get_book_entries(db, period, account_code, page, page_size)
    return success(data)


@router.get("/status")
async def get_status(period: str | None = None, db: AsyncSession = Depends(get_db)):
    data = await svc.get_reconciliation_status(db, period)
    return success(data)


@router.post("/match")
async def auto_match(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.run_auto_match(db, body["period"])
    await db.commit()
    return success(data)


@router.post("/manual-match")
async def manual_match(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.manual_match(db, body["bank_ids"], body["book_ids"])
    await db.commit()
    return success(data)


@router.post("/exclude")
async def exclude(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.exclude_transaction(db, body["transaction_id"], body.get("reason", ""))
    await db.commit()
    return success(data)


@router.get("/unmatched")
async def get_unmatched(period: str = Query(...), db: AsyncSession = Depends(get_db)):
    data = await svc.get_unmatched(db, period)
    return success(data)

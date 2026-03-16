"""Bank reconciliation service — three-tier matching engine."""

import uuid
from decimal import Decimal
from difflib import SequenceMatcher

from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BookEntry
from app.models.reconciliation import BankTransaction, ReconciliationRecord, ReconciliationRule


async def get_transactions(
    session: AsyncSession, period: str | None = None,
    status: str | None = None, min_amount: float | None = None,
    max_amount: float | None = None, counterparty: str | None = None,
    page: int = 1, page_size: int = 20,
) -> dict:
    query = select(BankTransaction)
    count_query = select(func.count()).select_from(BankTransaction)

    conditions = []
    if period:
        conditions.append(func.strftime("%Y-%m", BankTransaction.transaction_date) == period)
    if status:
        conditions.append(BankTransaction.matched_status == status)
    if min_amount is not None:
        conditions.append(func.abs(BankTransaction.amount) >= min_amount)
    if max_amount is not None:
        conditions.append(func.abs(BankTransaction.amount) <= max_amount)
    if counterparty:
        conditions.append(BankTransaction.counterparty.contains(counterparty))

    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    total = (await session.execute(count_query)).scalar()
    query = query.order_by(BankTransaction.transaction_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    rows = (await session.execute(query)).scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_txn_to_dict(t) for t in rows],
    }


async def get_book_entries(
    session: AsyncSession, period: str | None = None,
    account_code: str | None = None, page: int = 1, page_size: int = 20,
) -> dict:
    query = select(BookEntry)
    count_query = select(func.count()).select_from(BookEntry)

    conditions = []
    if period:
        conditions.append(func.strftime("%Y-%m", BookEntry.entry_date) == period)
    if account_code:
        conditions.append(BookEntry.account_code.startswith(account_code))

    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    total = (await session.execute(count_query)).scalar()
    query = query.order_by(BookEntry.entry_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    rows = (await session.execute(query)).scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_entry_to_dict(e) for e in rows],
    }


async def get_reconciliation_status(session: AsyncSession, period: str | None = None) -> dict:
    conditions = []
    if period:
        conditions.append(func.strftime("%Y-%m", BankTransaction.transaction_date) == period)

    base = select(func.count()).select_from(BankTransaction)
    if conditions:
        base = base.where(and_(*conditions))

    total = (await session.execute(base)).scalar()
    matched_q = base.where(BankTransaction.matched_status.in_(["matched", "confirmed"]))
    matched = (await session.execute(matched_q)).scalar()

    unmatched_amt_q = select(func.sum(func.abs(BankTransaction.amount))).where(
        BankTransaction.matched_status == "unmatched"
    )
    if conditions:
        unmatched_amt_q = unmatched_amt_q.where(and_(*conditions))
    unmatched_amount = (await session.execute(unmatched_amt_q)).scalar() or 0

    return {
        "total_transactions": total,
        "matched_count": matched,
        "unmatched_count": total - matched,
        "match_rate": round(matched / total * 100, 1) if total > 0 else 0,
        "unmatched_amount": float(unmatched_amount),
    }


async def run_auto_match(session: AsyncSession, period: str) -> dict:
    """Three-tier matching: exact → fuzzy → smart."""
    # Get unmatched transactions and book entries for the period
    bank_q = select(BankTransaction).where(
        and_(
            func.strftime("%Y-%m", BankTransaction.transaction_date) == period,
            BankTransaction.matched_status == "unmatched",
        )
    )
    bank_txns = list((await session.execute(bank_q)).scalars().all())

    book_q = select(BookEntry).where(
        and_(
            func.strftime("%Y-%m", BookEntry.entry_date) == period,
            BookEntry.account_code.startswith("1002"),  # Bank accounts only
        )
    )
    book_entries = list((await session.execute(book_q)).scalars().all())

    matched_bank_ids = set()
    matched_book_ids = set()
    details = []

    # L1: Exact match — same amount, same date
    for txn in bank_txns:
        if txn.id in matched_bank_ids:
            continue
        for entry in book_entries:
            if entry.id in matched_book_ids:
                continue
            amount_match = (txn.amount > 0 and entry.direction == "debit" and entry.amount == txn.amount) or \
                           (txn.amount < 0 and entry.direction == "credit" and entry.amount == abs(txn.amount))
            date_match = txn.transaction_date == entry.entry_date
            if amount_match and date_match:
                group_id = str(uuid.uuid4())[:8]
                session.add(ReconciliationRecord(
                    match_group_id=group_id, bank_transaction_id=txn.id,
                    book_entry_id=entry.id, match_type="exact",
                    confidence_score=1.0, is_confirmed=False, match_rule="金额+日期精确匹配",
                ))
                txn.matched_status = "matched"
                matched_bank_ids.add(txn.id)
                matched_book_ids.add(entry.id)
                details.append({"type": "exact", "bank_id": txn.id, "book_id": entry.id, "confidence": 1.0})
                break

    # L2: Fuzzy match — same amount, date within 3 days, summary similarity > 0.3
    for txn in bank_txns:
        if txn.id in matched_bank_ids:
            continue
        for entry in book_entries:
            if entry.id in matched_book_ids:
                continue
            amount_match = (txn.amount > 0 and entry.direction == "debit" and entry.amount == txn.amount) or \
                           (txn.amount < 0 and entry.direction == "credit" and entry.amount == abs(txn.amount))
            if not amount_match:
                continue
            day_diff = abs((txn.transaction_date - entry.entry_date).days)
            if day_diff > 3:
                continue
            sim = SequenceMatcher(None, txn.summary, entry.summary).ratio()
            if sim < 0.3:
                continue
            confidence = 0.7 + 0.1 * sim + 0.1 * (1 - day_diff / 3)
            group_id = str(uuid.uuid4())[:8]
            session.add(ReconciliationRecord(
                match_group_id=group_id, bank_transaction_id=txn.id,
                book_entry_id=entry.id, match_type="fuzzy",
                confidence_score=round(confidence, 2), is_confirmed=False,
                match_rule=f"模糊匹配: 日期差{day_diff}天, 摘要相似度{sim:.0%}",
            ))
            txn.matched_status = "matched"
            matched_bank_ids.add(txn.id)
            matched_book_ids.add(entry.id)
            details.append({"type": "fuzzy", "bank_id": txn.id, "book_id": entry.id, "confidence": round(confidence, 2)})
            break

    # L3: Smart match — one-to-many (sum of book entries matches bank amount)
    for txn in bank_txns:
        if txn.id in matched_bank_ids:
            continue
        target_amt = abs(txn.amount)
        direction = "debit" if txn.amount > 0 else "credit"
        candidates = [e for e in book_entries if e.id not in matched_book_ids and e.direction == direction]
        # Try pairs
        for i, e1 in enumerate(candidates):
            for e2 in candidates[i + 1:]:
                if e1.amount + e2.amount == target_amt:
                    group_id = str(uuid.uuid4())[:8]
                    for e in [e1, e2]:
                        session.add(ReconciliationRecord(
                            match_group_id=group_id, bank_transaction_id=txn.id,
                            book_entry_id=e.id, match_type="smart",
                            confidence_score=0.6, is_confirmed=False,
                            match_rule="智能匹配: 多笔合计匹配",
                        ))
                        matched_book_ids.add(e.id)
                    txn.matched_status = "matched"
                    matched_bank_ids.add(txn.id)
                    details.append({"type": "smart", "bank_id": txn.id, "book_ids": [e1.id, e2.id], "confidence": 0.6})
                    break
            if txn.id in matched_bank_ids:
                break

    await session.flush()

    return {
        "matched": len(matched_bank_ids),
        "unmatched": len(bank_txns) - len(matched_bank_ids),
        "details": details,
    }


async def manual_match(session: AsyncSession, bank_ids: list[int], book_ids: list[int]) -> dict:
    group_id = str(uuid.uuid4())[:8]
    for bid in bank_ids:
        for eid in book_ids:
            session.add(ReconciliationRecord(
                match_group_id=group_id, bank_transaction_id=bid,
                book_entry_id=eid, match_type="manual",
                confidence_score=1.0, is_confirmed=True, match_rule="手动匹配",
            ))
        await session.execute(
            update(BankTransaction).where(BankTransaction.id == bid).values(matched_status="confirmed")
        )
    await session.flush()
    return {"match_group_id": group_id}


async def exclude_transaction(session: AsyncSession, transaction_id: int, reason: str) -> dict:
    await session.execute(
        update(BankTransaction).where(BankTransaction.id == transaction_id).values(matched_status="excluded")
    )
    await session.flush()
    return {"transaction_id": transaction_id, "status": "excluded", "reason": reason}


async def get_unmatched(session: AsyncSession, period: str) -> dict:
    bank_q = select(BankTransaction).where(
        and_(
            func.strftime("%Y-%m", BankTransaction.transaction_date) == period,
            BankTransaction.matched_status == "unmatched",
        )
    )
    unmatched_bank = (await session.execute(bank_q)).scalars().all()

    # Find book entries not in any reconciliation record for this period
    matched_book_ids_q = select(ReconciliationRecord.book_entry_id)
    matched_book_ids = [r for r in (await session.execute(matched_book_ids_q)).scalars().all()]

    book_q = select(BookEntry).where(
        and_(
            func.strftime("%Y-%m", BookEntry.entry_date) == period,
            BookEntry.account_code.startswith("1002"),
            BookEntry.id.notin_(matched_book_ids) if matched_book_ids else True,
        )
    )
    unmatched_book = (await session.execute(book_q)).scalars().all()

    return {
        "bank_only": [_txn_to_dict(t) for t in unmatched_bank],
        "book_only": [_entry_to_dict(e) for e in unmatched_book],
    }


def _txn_to_dict(t: BankTransaction) -> dict:
    return {
        "id": t.id, "account_no": t.account_no,
        "transaction_date": str(t.transaction_date), "amount": float(t.amount),
        "counterparty": t.counterparty, "summary": t.summary,
        "serial_no": t.serial_no, "currency": t.currency,
        "matched_status": t.matched_status,
    }


def _entry_to_dict(e: BookEntry) -> dict:
    return {
        "id": e.id, "entry_date": str(e.entry_date), "amount": float(e.amount),
        "account_code": e.account_code, "account_name": e.account_name,
        "voucher_no": e.voucher_no, "summary": e.summary,
        "auxiliary": e.auxiliary, "direction": e.direction,
    }

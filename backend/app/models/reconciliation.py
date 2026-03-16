from decimal import Decimal

from sqlalchemy import String, Integer, Date, Numeric, Boolean, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_no: Mapped[str] = mapped_column(String(30))
    transaction_date: Mapped[str] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    counterparty: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(String(500), default="")
    serial_no: Mapped[str] = mapped_column(String(50), unique=True)
    currency: Mapped[str] = mapped_column(String(10), default="CNY")
    matched_status: Mapped[str] = mapped_column(String(20), default="unmatched")  # unmatched/matched/confirmed/excluded


class ReconciliationRecord(Base):
    __tablename__ = "reconciliation_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_group_id: Mapped[str] = mapped_column(String(50), index=True)
    bank_transaction_id: Mapped[int] = mapped_column(Integer, index=True)
    book_entry_id: Mapped[int] = mapped_column(Integer, index=True)
    match_type: Mapped[str] = mapped_column(String(20))  # exact/fuzzy/smart/manual
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    match_rule: Mapped[str] = mapped_column(String(200), default="")


class ReconciliationRule(Base):
    __tablename__ = "reconciliation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    match_fields: Mapped[dict] = mapped_column(JSON)
    tolerance_days: Mapped[int] = mapped_column(Integer, default=0)
    tolerance_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    priority: Mapped[int] = mapped_column(Integer, default=0)

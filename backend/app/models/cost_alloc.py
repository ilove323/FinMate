from decimal import Decimal

from sqlalchemy import String, Integer, Date, Numeric, Float, Boolean, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CostCenter(Base):
    __tablename__ = "cost_centers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    center_type: Mapped[str] = mapped_column(String(20))  # department/project/product_line
    parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    headcount: Mapped[int] = mapped_column(Integer, default=0)
    area: Mapped[float] = mapped_column(Float, default=0.0)
    revenue_ratio: Mapped[float] = mapped_column(Float, default=0.0)


class CostPool(Base):
    __tablename__ = "cost_pools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    cost_type: Mapped[str] = mapped_column(String(20))  # rent/utilities/it/management/other
    account_code: Mapped[str] = mapped_column(String(20))
    period: Mapped[str] = mapped_column(String(7), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    is_allocated: Mapped[bool] = mapped_column(Boolean, default=False)


class AllocationRule(Base):
    __tablename__ = "allocation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    cost_pool_id: Mapped[int] = mapped_column(Integer, index=True)
    allocation_basis: Mapped[str] = mapped_column(String(20))  # headcount/area/revenue/hours/custom
    condition_expr: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[int] = mapped_column(Integer, default=0)
    effective_from: Mapped[str] = mapped_column(Date)
    effective_to: Mapped[str | None] = mapped_column(Date, nullable=True)


class AllocationResult(Base):
    __tablename__ = "allocation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_id: Mapped[int] = mapped_column(Integer, index=True)
    cost_pool_id: Mapped[int] = mapped_column(Integer, index=True)
    cost_center_id: Mapped[int] = mapped_column(Integer, index=True)
    period: Mapped[str] = mapped_column(String(7), index=True)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    allocation_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    calculation_detail: Mapped[str] = mapped_column(Text, default="")


class AllocationVoucher(Base):
    __tablename__ = "allocation_vouchers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period: Mapped[str] = mapped_column(String(7), index=True)
    voucher_no: Mapped[str] = mapped_column(String(50))
    entries: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(10), default="draft")  # draft/confirmed

"""Cost allocation service with IF-THEN rule engine."""

import json
from decimal import Decimal

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cost_alloc import (
    CostCenter, CostPool, AllocationRule, AllocationResult, AllocationVoucher,
)


async def get_centers(session: AsyncSession) -> list[dict]:
    rows = (await session.execute(select(CostCenter).order_by(CostCenter.code))).scalars().all()
    return [_center_to_dict(c) for c in rows]


async def get_pools(session: AsyncSession, period: str | None = None) -> list[dict]:
    query = select(CostPool)
    if period:
        query = query.where(CostPool.period == period)
    rows = (await session.execute(query.order_by(CostPool.name))).scalars().all()
    return [_pool_to_dict(p) for p in rows]


async def get_rules(session: AsyncSession) -> list[dict]:
    rows = (await session.execute(
        select(AllocationRule).order_by(AllocationRule.priority)
    )).scalars().all()
    return [_rule_to_dict(r) for r in rows]


async def create_rule(session: AsyncSession, data: dict) -> dict:
    rule = AllocationRule(**data)
    session.add(rule)
    await session.flush()
    return _rule_to_dict(rule)


async def update_rule(session: AsyncSession, rule_id: int, data: dict) -> dict:
    await session.execute(
        update(AllocationRule).where(AllocationRule.id == rule_id).values(**data)
    )
    await session.flush()
    return {"id": rule_id, "updated": True}


async def calculate(session: AsyncSession, period: str, save: bool = True) -> dict:
    """Execute cost allocation based on rules."""
    pools = (await session.execute(
        select(CostPool).where(CostPool.period == period)
    )).scalars().all()

    centers = (await session.execute(select(CostCenter))).scalars().all()
    rules = (await session.execute(
        select(AllocationRule).order_by(AllocationRule.priority)
    )).scalars().all()

    # Delete existing results for this period if saving
    if save:
        existing = (await session.execute(
            select(AllocationResult).where(AllocationResult.period == period)
        )).scalars().all()
        for item in existing:
            await session.delete(item)

    total_headcount = sum(c.headcount for c in centers)
    total_area = sum(c.area for c in centers)
    total_revenue = sum(c.revenue_ratio for c in centers)

    results = []
    sankey_nodes = set()
    sankey_links = []

    for pool in pools:
        # Find matching rule
        matched_rule = None
        for rule in rules:
            if rule.condition_expr and pool.cost_type in rule.condition_expr:
                matched_rule = rule
                break

        if not matched_rule:
            continue

        basis = matched_rule.allocation_basis
        for center in centers:
            if basis == "headcount":
                ratio = center.headcount / total_headcount if total_headcount else 0
            elif basis == "area":
                ratio = center.area / total_area if total_area else 0
            elif basis == "revenue":
                ratio = center.revenue_ratio / total_revenue if total_revenue else 0
            else:
                ratio = 1.0 / len(centers)

            allocated = (pool.amount * Decimal(str(ratio))).quantize(Decimal("0.01"))

            result_data = {
                "rule_id": matched_rule.id,
                "cost_pool_id": pool.id,
                "cost_center_id": center.id,
                "period": period,
                "allocated_amount": allocated,
                "allocation_ratio": round(ratio, 4),
                "calculation_detail": json.dumps({
                    "pool": pool.name, "center": center.name,
                    "basis": basis, "ratio": round(ratio, 4),
                    "pool_amount": float(pool.amount),
                }, ensure_ascii=False),
            }

            if save:
                session.add(AllocationResult(**result_data))

            results.append({
                **result_data,
                "allocated_amount": float(allocated),
                "pool_name": pool.name,
                "center_name": center.name,
            })

            sankey_nodes.add(pool.name)
            sankey_nodes.add(center.name)
            sankey_links.append({
                "source": pool.name, "target": center.name,
                "value": float(allocated),
            })

    if save:
        for pool in pools:
            pool.is_allocated = True
        await session.flush()

    return {
        "period": period,
        "total_allocated": sum(r["allocated_amount"] for r in results),
        "results": results,
        "sankey": {
            "nodes": [{"name": n} for n in sankey_nodes],
            "links": sankey_links,
        },
    }


async def simulate(session: AsyncSession, period: str, rules: list[dict] | None = None) -> dict:
    """Simulate allocation without saving."""
    return await calculate(session, period, save=False)


async def get_results(session: AsyncSession, period: str) -> dict:
    rows = (await session.execute(
        select(AllocationResult).where(AllocationResult.period == period)
    )).scalars().all()

    centers = {c.id: c.name for c in (await session.execute(select(CostCenter))).scalars().all()}
    pools = {p.id: p.name for p in (await session.execute(
        select(CostPool).where(CostPool.period == period)
    )).scalars().all()}

    results = []
    sankey_nodes = set()
    sankey_links = []

    for r in rows:
        pool_name = pools.get(r.cost_pool_id, "")
        center_name = centers.get(r.cost_center_id, "")
        results.append({
            "pool_name": pool_name, "center_name": center_name,
            "allocated_amount": float(r.allocated_amount),
            "allocation_ratio": r.allocation_ratio,
        })
        sankey_nodes.add(pool_name)
        sankey_nodes.add(center_name)
        sankey_links.append({"source": pool_name, "target": center_name, "value": float(r.allocated_amount)})

    return {
        "period": period,
        "results": results,
        "sankey": {"nodes": [{"name": n} for n in sankey_nodes], "links": sankey_links},
    }


async def get_voucher(session: AsyncSession, period: str) -> dict:
    voucher = (await session.execute(
        select(AllocationVoucher).where(AllocationVoucher.period == period)
    )).scalars().first()

    if not voucher:
        # Generate voucher from results
        results = (await session.execute(
            select(AllocationResult).where(AllocationResult.period == period)
        )).scalars().all()

        centers = {c.id: c for c in (await session.execute(select(CostCenter))).scalars().all()}
        pools = {p.id: p for p in (await session.execute(
            select(CostPool).where(CostPool.period == period)
        )).scalars().all()}

        entries = []
        for r in results:
            pool = pools.get(r.cost_pool_id)
            center = centers.get(r.cost_center_id)
            if pool and center:
                entries.append({
                    "debit_account": f"4001-{center.code}",
                    "debit_name": f"生产成本-{center.name}",
                    "credit_account": pool.account_code,
                    "credit_name": pool.name,
                    "amount": float(r.allocated_amount),
                    "cost_center": center.name,
                })

        return {
            "period": period, "voucher_no": f"FP-{period}-001",
            "entries": entries, "status": "draft",
        }

    return {
        "period": period, "voucher_no": voucher.voucher_no,
        "entries": voucher.entries, "status": voucher.status,
    }


def _center_to_dict(c: CostCenter) -> dict:
    return {
        "id": c.id, "code": c.code, "name": c.name,
        "center_type": c.center_type, "parent_id": c.parent_id,
        "headcount": c.headcount, "area": c.area, "revenue_ratio": c.revenue_ratio,
    }


def _pool_to_dict(p: CostPool) -> dict:
    return {
        "id": p.id, "name": p.name, "cost_type": p.cost_type,
        "account_code": p.account_code, "period": p.period,
        "amount": float(p.amount), "is_allocated": p.is_allocated,
    }


def _rule_to_dict(r: AllocationRule) -> dict:
    return {
        "id": r.id, "name": r.name, "cost_pool_id": r.cost_pool_id,
        "allocation_basis": r.allocation_basis, "condition_expr": r.condition_expr,
        "priority": r.priority, "effective_from": str(r.effective_from),
        "effective_to": str(r.effective_to) if r.effective_to else None,
    }

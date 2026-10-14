from __future__ import annotations
import hashlib
import secrets
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import ApiKey, UsageRecord
from backend.utils.ids import short_id

COST_PER_1K = 0.002

def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()

async def create_key(session: AsyncSession, name: str, budget_usd: float = 10.0) -> dict:
    raw = secrets.token_urlsafe(24)
    row = ApiKey(id=short_id(), name=name.strip()[:120], key_prefix=raw[:8], budget_usd=float(budget_usd))
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return {"id": row.id, "name": row.name, "api_key": raw, "key_prefix": row.key_prefix, "budget_usd": row.budget_usd}

async def list_keys(session: AsyncSession) -> list[ApiKey]:
    return list((await session.execute(select(ApiKey).order_by(ApiKey.created_at.desc()))).scalars())

async def resolve_key(session: AsyncSession, api_key: str) -> ApiKey | None:
    prefix = api_key[:8]
    for row in await list_keys(session):
        if row.key_prefix == prefix:
            return row
    return None

async def record_usage(
    session: AsyncSession,
    key_id: str,
    *,
    prompt_tokens: int,
    completion_tokens: int,
    model: str = "mock",
    note: str = "",
) -> dict:
    key = await session.get(ApiKey, key_id)
    if not key:
        raise ValueError("key not found")
    total = int(prompt_tokens) + int(completion_tokens)
    cost = round((total / 1000.0) * COST_PER_1K, 6)
    rec = UsageRecord(
        id=short_id(),
        key_id=key_id,
        model=model[:64],
        prompt_tokens=int(prompt_tokens),
        completion_tokens=int(completion_tokens),
        cost_usd=cost,
        note=note.strip()[:500],
    )
    key.spent_usd = round(key.spent_usd + cost, 6)
    alert = False
    if key.spent_usd >= key.budget_usd and not key.alert_sent:
        key.alert_sent = True
        alert = True
    session.add(rec)
    await session.commit()
    return {"record_id": rec.id, "cost_usd": cost, "spent_usd": key.spent_usd, "budget_usd": key.budget_usd, "alert": alert}

async def dashboard(session: AsyncSession) -> dict:
    keys = await list_keys(session)
    by_model = (
        await session.execute(
            select(UsageRecord.model, func.sum(UsageRecord.cost_usd), func.sum(UsageRecord.prompt_tokens + UsageRecord.completion_tokens))
            .group_by(UsageRecord.model)
        )
    ).all()
    alerts = [{"key_id": k.id, "name": k.name, "spent_usd": k.spent_usd, "budget_usd": k.budget_usd} for k in keys if k.spent_usd >= k.budget_usd]
    return {
        "total_spent": round(sum(k.spent_usd for k in keys), 4),
        "keys": len(keys),
        "by_model": [{"model": m, "cost_usd": float(c or 0), "tokens": int(t or 0)} for m, c, t in by_model],
        "alerts": alerts,
    }

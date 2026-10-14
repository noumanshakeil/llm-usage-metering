from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db import get_db
from backend.services import metering as svc

class KeyIn(BaseModel):
    name: str = Field(min_length=2)
    budget_usd: float = Field(default=10.0, gt=0)

class UsageIn(BaseModel):
    key_id: str
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    model: str = "mock"
    note: str = ""

router = APIRouter()

@router.get("/keys")
async def keys(db: AsyncSession = Depends(get_db)):
    rows = await svc.list_keys(db)
    return {"keys": [{"id": k.id, "name": k.name, "key_prefix": k.key_prefix, "budget_usd": k.budget_usd, "spent_usd": k.spent_usd, "alert_sent": k.alert_sent} for k in rows]}

@router.post("/keys")
async def create_key(payload: KeyIn, db: AsyncSession = Depends(get_db)):
    return await svc.create_key(db, payload.name, payload.budget_usd)

@router.post("/usage")
async def usage(payload: UsageIn, db: AsyncSession = Depends(get_db)):
    try:
        return await svc.record_usage(db, payload.key_id, prompt_tokens=payload.prompt_tokens, completion_tokens=payload.completion_tokens, model=payload.model, note=payload.note)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc

@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)):
    return await svc.dashboard(db)

@router.get("/alerts")
async def alerts(db: AsyncSession = Depends(get_db)):
    dash = await svc.dashboard(db)
    return {"alerts": dash["alerts"]}

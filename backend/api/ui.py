from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db import get_db
from backend.services import metering as svc

router = APIRouter()
templates = Jinja2Templates(directory="backend/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    return templates.TemplateResponse("index.html", {"request": request, "title": "LLM Usage Metering", "keys": await svc.list_keys(db), "dashboard": await svc.dashboard(db), "created": None})

@router.post("/ui/keys")
async def ui_key(name: str = Form(...), budget_usd: float = Form(10.0), db: AsyncSession = Depends(get_db)):
    created = await svc.create_key(db, name, budget_usd)
    return templates.TemplateResponse("index.html", {"request": request, "title": "LLM Usage Metering", "keys": await svc.list_keys(db), "dashboard": await svc.dashboard(db), "created": created})

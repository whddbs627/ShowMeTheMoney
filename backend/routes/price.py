from fastapi import APIRouter
from backend.engine import engine

router = APIRouter(tags=["price"])


@router.get("/price")
async def get_price():
    status = engine.get_status()
    return {"coins": status.get("coins", [])}

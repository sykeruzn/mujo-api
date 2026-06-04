from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import date
import calendar

from api.auth import verify_token
from api.services.supabase_client import get_supabase

router = APIRouter(prefix="/habits", tags=["habits"])

@router.get("/")
async def get_habits(user_id: str = Depends(verify_token)):
    """Return all habits for the user."""
    db = get_supabase()
    result = (
        db.table("habits")
        .select("*")
        .eq("user_id", user_id)
        .order("sort_order")
        .execute()
    )
    return result.data

@router.get("/completions")
async def get_completions(year: int, month: int, user_id: str = Depends(verify_token)):
    """Return all completions for a given month (YYYY-MM)."""
    # Dynamically get the last day of the requested month
    _, last_day = calendar.monthrange(year, month)

    month_str = f"{year}-{month:02d}"
    db = get_supabase()
    result = (
        db.table("habit_completions")
        .select("habit_id, date")
        .eq("user_id", user_id)
        .gte("date", f"{month_str}-01")
        .lte("date", f"{month_str}-{last_day}") # <-- 3. Pass the dynamic last_day here
        .execute()
    )
    return result.data

class ToggleBody(BaseModel):
    habit_id: str
    date: date
    completed: bool   # true = mark done, false = unmark

@router.post("/toggle")
async def toggle_completion(body: ToggleBody, user_id: str = Depends(verify_token)):
    """Mark or unmark a habit as completed for a given date."""
    db = get_supabase()
    if body.completed:
        db.table("habit_completions").upsert({
            "user_id": user_id,
            "habit_id": body.habit_id,
            "date": str(body.date),
        }).execute()
    else:
        db.table("habit_completions").delete().eq("habit_id", body.habit_id).eq("date", str(body.date)).execute()
    return {"ok": True}
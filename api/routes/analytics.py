from fastapi import APIRouter, Depends
from api.auth import verify_token
from api.services.supabase_client import get_supabase

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/moods-by-month")
async def moods_by_month(year: int, month: int, user_id: str = Depends(verify_token)):
    """
    Returns an array of { day: int, dominant_mood: str } for the given month.
    """
    month_str = f"{year}-{month:02d}"
    db = get_supabase()
    result = (
        db.table("journal_entries")
        .select("dominant_mood, created_at")
        .eq("user_id", user_id)
        .gte("created_at", f"{month_str}-01T00:00:00")
        .lt("created_at",  f"{year}-{month+1:02d}-01T00:00:00" if month < 12 else f"{year+1}-01-01T00:00:00")
        .order("created_at")
        .execute()
    )
    # One entry per day — take the last entry for each calendar day
    day_map: dict = {}
    for row in result.data:
        day = int(row["created_at"][8:10])
        day_map[day] = row["dominant_mood"]

    return [{"day": d, "dominant_mood": m} for d, m in sorted(day_map.items())]

@router.get("/distribution")
async def emotion_distribution(months: int = 3, user_id: str = Depends(verify_token)):
    """
    Returns percentage distribution across all 7 emotions for the last N months.
    """
    from datetime import datetime, timedelta
    cutoff = (datetime.utcnow() - timedelta(days=months * 30)).isoformat()
    db = get_supabase()
    result = (
        db.table("journal_entries")
        .select("dominant_mood")
        .eq("user_id", user_id)
        .gte("created_at", cutoff)
        .execute()
    )
    moods = [row["dominant_mood"] for row in result.data]
    total = len(moods) or 1
    counts: dict = {}
    for m in moods:
        counts[m] = counts.get(m, 0) + 1

    return {
        emotion: round((counts.get(emotion, 0) / total) * 100)
        for emotion in ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]
    }
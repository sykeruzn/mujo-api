from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.auth import verify_token
from api.services.supabase_client import get_supabase
from api.services.hf_emotion import analyze_emotion

router = APIRouter(prefix="/journal", tags=["journal"])

class JournalEntryCreate(BaseModel):
    entry_text: str

@router.post("/analyze")
async def analyze_and_save(body: JournalEntryCreate, user_id: str = Depends(verify_token)):
    """Analyze text with HuggingFace, save entry, return scores."""
    if len(body.entry_text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Entry too short")

    scores = await analyze_emotion(body.entry_text)
    dominant = scores.pop("dominant")

    db = get_supabase()
    result = db.table("journal_entries").insert({
        "user_id": user_id,
        "entry_text": body.entry_text,
        "score_anger":    scores.get("anger", 0),
        "score_disgust":  scores.get("disgust", 0),
        "score_fear":     scores.get("fear", 0),
        "score_joy":      scores.get("joy", 0),
        "score_neutral":  scores.get("neutral", 0),
        "score_sadness":  scores.get("sadness", 0),
        "score_surprise": scores.get("surprise", 0),
        "dominant_mood":  dominant,
    }).execute()

    return {
        "id": result.data[0]["id"],
        "scores": scores,
        "dominant": dominant,
        "created_at": result.data[0]["created_at"],
    }

@router.get("/entries")
async def get_entries(limit: int = 10, user_id: str = Depends(verify_token)):
    """Fetch recent journal entries for the current user."""
    db = get_supabase()
    result = (
        db.table("journal_entries")
        .select("id, entry_text, dominant_mood, score_joy, score_sadness, score_anger, score_fear, score_disgust, score_neutral, score_surprise, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data
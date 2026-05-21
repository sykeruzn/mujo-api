from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
from api.auth import verify_token
from api.services.supabase_client import get_supabase
from api.services.hf_emotion import analyze_emotion

router = APIRouter(prefix="/journal", tags=["journal"])

class JournalEntryCreate(BaseModel):
    entry_text: str

class JournalEntryUpdate(BaseModel):
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
async def get_entries(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    mood: Optional[str] = Query(default=None),
    user_id: str = Depends(verify_token),
):
    """Fetch journal entries for the current user with optional pagination and mood filter."""
    db = get_supabase()
    query = (
        db.table("journal_entries")
        .select("id, entry_text, dominant_mood, score_joy, score_sadness, score_anger, score_fear, score_disgust, score_neutral, score_surprise, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
    )

    if mood:
        query = query.eq("dominant_mood", mood)

    result = query.range(offset, offset + limit - 1).execute()
    return result.data

@router.put("/entries/{entry_id}")
async def update_entry(
    entry_id: str,
    body: JournalEntryUpdate,
    user_id: str = Depends(verify_token),
):
    """Update the text of an existing journal entry and re-analyze emotion scores."""
    if len(body.entry_text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Entry too short")

    db = get_supabase()

    # Verify ownership
    existing = db.table("journal_entries").select("id").eq("id", entry_id).eq("user_id", user_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Entry not found")

    # Re-analyze emotion with the new text
    scores = await analyze_emotion(body.entry_text)
    dominant = scores.pop("dominant")

    result = db.table("journal_entries").update({
        "entry_text":     body.entry_text.strip(),
        "score_anger":    scores.get("anger", 0),
        "score_disgust":  scores.get("disgust", 0),
        "score_fear":     scores.get("fear", 0),
        "score_joy":      scores.get("joy", 0),
        "score_neutral":  scores.get("neutral", 0),
        "score_sadness":  scores.get("sadness", 0),
        "score_surprise": scores.get("surprise", 0),
        "dominant_mood":  dominant,
    }).eq("id", entry_id).eq("user_id", user_id).execute()

    return result.data[0]

@router.delete("/entries/{entry_id}", status_code=204)
async def delete_entry(
    entry_id: str,
    user_id: str = Depends(verify_token),
):
    """Delete a journal entry belonging to the current user."""
    db = get_supabase()

    # Verify ownership before deleting
    existing = db.table("journal_entries").select("id").eq("id", entry_id).eq("user_id", user_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Entry not found")

    db.table("journal_entries").delete().eq("id", entry_id).eq("user_id", user_id).execute()
    return None

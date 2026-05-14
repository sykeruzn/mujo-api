import os
import httpx

HF_API_URL = "https://router.huggingface.co/hf-inference/models/j-hartmann/emotion-english-distilroberta-base"
HF_TOKEN = os.environ.get("HF_TOKEN", "")

EMOTION_KEYS = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]

async def analyze_emotion(text: str) -> dict:
    """
    Calls HuggingFace Inference API and returns a dict like:
    { "anger": 0.02, "joy": 0.71, ... , "dominant": "joy" }
    """
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": text}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(HF_API_URL, headers=headers, json=payload)
        response.raise_for_status()

    # HF returns: [[{"label": "joy", "score": 0.71}, ...]]
    raw = response.json()
    items = raw[0] if isinstance(raw[0], list) else raw

    scores = {item["label"].lower(): round(item["score"], 4) for item in items}

    # Ensure all 7 keys present
    for key in EMOTION_KEYS:
        scores.setdefault(key, 0.0)

    dominant = max(scores, key=scores.get)
    scores["dominant"] = dominant
    return scores
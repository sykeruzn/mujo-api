from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import journal, habits, analytics

app = FastAPI(title="MuJo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",           # Vite dev server
        "https://your-mujo-app.vercel.app", # replace with your Vercel frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(journal.router)
app.include_router(habits.router)
app.include_router(analytics.router)

@app.get("/health")
def health():
    return {"status": "ok"}
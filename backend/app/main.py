from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.discover import router as discover_router
from app.api.crm import router as crm_router
from app.api.agents import router as agent_router
from app.database import init_db

app = FastAPI()
init_db()

# ------------------------
# CORS FIX (CRITICAL)
# ------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later we restrict to Vercel domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(discover_router)
app.include_router(crm_router)
app.include_router(agent_router)


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok", "system": "BarbechAI"}

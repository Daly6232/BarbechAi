from fastapi import FastAPI

from app.api.discover import router as discover_router
from app.api.crm import router as crm_router
from app.api.agents import router as agents_router

app = FastAPI()

app.include_router(discover_router)
app.include_router(crm_router)
app.include_router(agents_router)

@app.get("/health")
def health():
    return {"status": "ok", "system": "BarbechAI"}

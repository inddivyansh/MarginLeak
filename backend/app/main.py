import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.database import init_db, get_db
from backend.app.models import Workspace
from backend.app.api import documents, reconciliations, history, evaluations, supplier_risk

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="MarginLeak — Accounts-Payable AI Auditor for Small Businesses (Hacktoberfest Side Hustle)"
)

# Enable CORS for development and deployed frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check for Render
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment,
        "database": "connected"
    }

# Workspaces endpoint
@app.get("/api/v1/workspaces/default")
def get_default_workspace(db: Session = Depends(get_db)):
    ws = db.query(Workspace).first()
    if not ws:
        init_db()
        ws = db.query(Workspace).first()
    return {
        "id": ws.id,
        "name": ws.name,
        "default_currency": ws.default_currency,
        "created_at": ws.created_at
    }

# Mount API Routers under /api/v1
app.include_router(documents.router, prefix="/api/v1")
app.include_router(reconciliations.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(evaluations.router, prefix="/api/v1")
app.include_router(supplier_risk.router, prefix="/api/v1")

# Mount built React frontend if dist exists
dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.exists(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api") or full_path == "health":
            return None
        file_path = os.path.join(dist_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_dir, "index.html"))

@app.on_event("startup")
def on_startup():
    init_db()

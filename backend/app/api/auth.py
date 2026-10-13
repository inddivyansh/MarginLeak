from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.auth import get_current_user, get_user_workspace
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models import User

router = APIRouter(tags=["Authentication"])


@router.get("/auth/config")
def auth_config():
    return {
        "supabase_url": settings.supabase_project_url,
        "supabase_anon_key": settings.supabase_anon_key,
    }


@router.get("/auth/me")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    workspace = get_user_workspace(user, db)
    return {
        "id": user.external_id,
        "email": user.email,
        "workspace": {
            "id": workspace.id,
            "name": workspace.name,
            "default_currency": workspace.default_currency,
        },
    }
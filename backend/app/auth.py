from datetime import datetime, timedelta, timezone
from typing import Any, Dict
import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models import User, Workspace, WorkspaceMembership

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str = "Authentication required") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def decode_access_token(credentials: HTTPAuthorizationCredentials | None) -> Dict[str, Any]:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    if not settings.supabase_jwt_secret:
        raise HTTPException(status_code=503, detail="Authentication is not configured on the server.")
    try:
        return jwt.decode(
            credentials.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as exc:
        raise _unauthorized("Invalid or expired access token") from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    claims = decode_access_token(credentials)
    external_id = claims.get("sub")
    if not external_id:
        raise _unauthorized("Access token has no user identity")
    user = db.query(User).filter(User.external_id == external_id).first()
    email = claims.get("email")
    if not user:
        user = User(id=str(uuid.uuid4()), external_id=external_id, email=email)
        workspace = Workspace(
            id=str(uuid.uuid4()),
            name=(email.split("@", 1)[0] if email else "Private Workspace") + "'s Workspace",
            default_currency=settings.default_currency,
        )
        user.memberships.append(WorkspaceMembership(workspace=workspace, role="owner"))
        db.add(user)
        db.commit()
        db.refresh(user)
    elif email and user.email != email:
        user.email = email
        db.commit()
    return user


def get_authorized_workspace(workspace_id: str, user: User, db: Session) -> Workspace:
    workspace = (
        db.query(Workspace)
        .join(WorkspaceMembership)
        .filter(Workspace.id == workspace_id, WorkspaceMembership.user_id == user.id)
        .first()
    )
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    return workspace


def get_user_workspace(user: User, db: Session) -> Workspace:
    membership = db.query(WorkspaceMembership).filter(WorkspaceMembership.user_id == user.id).first()
    if not membership:
        workspace = Workspace(
            id=str(uuid.uuid4()),
            name="Private Workspace",
            default_currency=settings.default_currency,
        )
        db.add(workspace)
        db.add(WorkspaceMembership(user_id=user.id, workspace=workspace, role="owner"))
        db.commit()
        return workspace
    return membership.workspace
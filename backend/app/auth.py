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

import time
import requests

bearer_scheme = HTTPBearer(auto_error=False)

# Short-lived in-memory cache for validated tokens: token -> (claims, expire_timestamp)
_verified_token_cache: Dict[str, tuple[Dict[str, Any], float]] = {}


def _unauthorized(detail: str = "Authentication required") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _verify_with_supabase_api(raw_token: str) -> Dict[str, Any]:
    now = time.time()
    if raw_token in _verified_token_cache:
        cached_claims, exp = _verified_token_cache[raw_token]
        if exp > now:
            return cached_claims

    if not settings.supabase_project_url:
        raise HTTPException(
            status_code=503,
            detail="Authentication is not configured on the server (missing Supabase URL)."
        )

    headers = {
        "Authorization": f"Bearer {raw_token}",
    }
    if settings.supabase_anon_key:
        headers["apikey"] = settings.supabase_anon_key

    endpoint = f"{settings.supabase_project_url.rstrip('/')}/auth/v1/user"
    try:
        resp = requests.get(endpoint, headers=headers, timeout=5)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Unable to verify authentication with Supabase service.") from exc

    if resp.status_code != 200:
        raise _unauthorized("Invalid or expired access token")

    data = resp.json()
    claims = {
        "sub": data.get("id"),
        "email": data.get("email"),
        "aud": data.get("aud", "authenticated"),
        "user_metadata": data.get("user_metadata", {}),
    }

    try:
        unverified = jwt.decode(raw_token, options={"verify_signature": False})
        token_exp = float(unverified.get("exp", now + 300))
    except Exception:
        token_exp = now + 300

    _verified_token_cache[raw_token] = (claims, min(token_exp, now + 300))
    return claims


def decode_access_token(credentials: HTTPAuthorizationCredentials | None) -> Dict[str, Any]:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    raw_token = credentials.credentials

    # Inspect token header for signing algorithm
    try:
        header = jwt.get_unverified_header(raw_token)
        alg = header.get("alg", "HS256")
    except Exception:
        raise _unauthorized("Malformed access token")

    # If the token is signed with HS256 and a secret is configured, attempt local fast-path verification
    if alg == "HS256" and settings.supabase_jwt_secret:
        try:
            return jwt.decode(
                raw_token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        except jwt.PyJWTError:
            if settings.supabase_project_url:
                return _verify_with_supabase_api(raw_token)
            raise _unauthorized("Invalid or expired access token")

    # For asymmetric tokens (e.g. ES256, RS256) or when no local secret is configured, verify via Supabase API
    if settings.supabase_project_url:
        return _verify_with_supabase_api(raw_token)

    if not settings.supabase_jwt_secret:
        raise HTTPException(status_code=503, detail="Authentication is not configured on the server.")

    raise _unauthorized(f"Unsupported token algorithm: {alg}")


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
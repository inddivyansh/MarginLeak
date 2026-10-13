from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.auth import get_authorized_workspace, get_current_user, get_user_workspace
from backend.app.engine.supplier_risk import predict_supplier_risk
from backend.app.models import User
from backend.app.schemas import SupplierRiskResponse

router = APIRouter(tags=["Supplier Risk"])


@router.get("/supplier-risk", response_model=SupplierRiskResponse)
def get_supplier_risk(workspace_id: Optional[str] = None, supplier_key: Optional[str] = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if workspace_id:
        get_authorized_workspace(workspace_id, user, db)
    else:
        workspace_id = get_user_workspace(user, db).id
    return predict_supplier_risk(db, workspace_id=workspace_id, supplier_key=supplier_key)
import asyncio
from pathlib import Path

import pytest
import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app import models
from backend.app.api import documents
from backend.app.api.reconciliations import (
    correct_match,
    export_csv_report,
    get_dispute_draft,
    get_reconciliation,
    list_findings,
    update_finding,
)
from backend.app.database import Base
from backend.app.auth import decode_access_token, get_current_user
from backend.app.schemas import ColumnMappingRequest, FindingUpdate, MatchCorrectionUpdate


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def seeded_records(db_session):
    workspace_a = models.Workspace(id="workspace-a", name="A", default_currency="USD")
    workspace_b = models.Workspace(id="workspace-b", name="B", default_currency="USD")
    user = models.User(id="user-a", external_id="external-a", email="a@example.com")
    membership = models.WorkspaceMembership(user_id=user.id, workspace_id=workspace_a.id, role="owner")
    invoice = models.Invoice(
        id="invoice-a",
        workspace_id=workspace_a.id,
        invoice_number="INV-1",
        supplier_name="Supplier",
        supplier_key="supplier",
        total_amount=100,
    )
    purchase_order = models.PurchaseOrder(
        id="po-a",
        workspace_id=workspace_a.id,
        po_number="PO-1",
        supplier_name="Supplier",
        supplier_key="supplier",
    )
    invoice_line = models.InvoiceLine(
        id="invoice-line-a",
        invoice_id=invoice.id,
        line_number=1,
        description="Item",
        quantity=1,
        unit_price=100,
        total_price=100,
    )
    po_line = models.PurchaseOrderLine(
        id="po-line-a",
        purchase_order_id=purchase_order.id,
        line_number=1,
        description="Item",
        quantity=1,
        unit_price=100,
        total_price=100,
    )
    reconciliation = models.Reconciliation(
        id="reconciliation-a",
        workspace_id=workspace_a.id,
        invoice_id=invoice.id,
        purchase_order_id=purchase_order.id,
        currency="USD",
    )
    finding = models.Finding(
        id="finding-a",
        reconciliation_id=reconciliation.id,
        invoice_line_id=invoice_line.id,
        po_line_id=po_line.id,
        type="PRICE_MISMATCH",
        severity="warning",
        amount_at_risk=10,
        currency="USD",
        explanation="Test finding",
        evidence_json={},
    )
    line_match = models.LineMatch(
        id="match-a",
        reconciliation_id=reconciliation.id,
        invoice_line_id=invoice_line.id,
        po_line_id=po_line.id,
        method="exact_sku",
        confidence=1,
    )
    db_session.add_all([
        workspace_a, workspace_b, user, membership, invoice, purchase_order, invoice_line,
        po_line, reconciliation, finding, line_match,
    ])
    db_session.commit()
    return db_session, workspace_a, workspace_b, reconciliation, finding, line_match, user


def assert_not_found(callable_obj, *args, **kwargs):
    with pytest.raises(HTTPException) as error:
        callable_obj(*args, **kwargs)
    assert error.value.status_code == 404


def test_workspace_cannot_read_or_modify_another_workspace_records(seeded_records):
    db, _, workspace_b, reconciliation, finding, line_match, user = seeded_records

    assert_not_found(get_reconciliation, reconciliation.id, workspace_b.id, db, user)
    assert_not_found(list_findings, reconciliation.id, workspace_b.id, db, user)
    assert_not_found(update_finding, finding.id, FindingUpdate(status="dismissed"), workspace_b.id, db, user)
    assert_not_found(get_dispute_draft, finding.id, workspace_b.id, db, user)
    assert_not_found(correct_match, line_match.id, MatchCorrectionUpdate(mark_unmatched=True), workspace_b.id, db, user)
    assert_not_found(export_csv_report, reconciliation.id, workspace_b.id, db, user)


def test_po_confirmation_requires_safe_temp_key(tmp_path, monkeypatch, db_session):
    monkeypatch.setattr(documents.settings, "upload_dir", str(tmp_path))
    workspace = models.Workspace(id="workspace-po", name="PO Workspace", default_currency="USD")
    db_session.add(workspace)
    db_session.commit()

    csv_content = b"PO Number,SKU,Description,Quantity,Unit Price\nPO-7,SKU-7,Widget,2,12.50\n"
    user = models.User(id="user-po", external_id="external-po", email="po@example.com")
    membership = models.WorkspaceMembership(user_id=user.id, workspace_id=workspace.id, role="owner")
    db_session.add_all([user, membership])
    db_session.commit()
    temp_key = f"temp_{user.id}_upload-7"
    (tmp_path / temp_key).write_bytes(csv_content)
    request = ColumnMappingRequest(
        workspace_id=workspace.id,
        filename="purchase-order.csv",
        temp_key=temp_key,
        po_number="PO-7",
        columns={
            "po_number": "PO Number",
            "sku": "SKU",
            "description": "Description",
            "quantity": "Quantity",
            "unit_price": "Unit Price",
        },
    )

    purchase_order = asyncio.run(documents.confirm_purchase_order(request, db_session, user))
    assert purchase_order.po_number == "PO-7"
    assert purchase_order.document.filename == "purchase-order.csv"

    invalid_request = request.model_copy(update={"temp_key": "../outside.csv"})
    assert_not_found_or_status(documents.confirm_purchase_order, invalid_request, db_session, 400, user)
    expired_request = request.model_copy(update={"temp_key": f"temp_{user.id}_expired"})
    assert_not_found_or_status(documents.confirm_purchase_order, expired_request, db_session, 404, user)


def assert_not_found_or_status(async_callable, request, db, status_code, user):
    with pytest.raises(HTTPException) as error:
        asyncio.run(async_callable(request, db, user))
    assert error.value.status_code == status_code


def test_missing_or_invalid_access_token_is_rejected(monkeypatch):
    monkeypatch.setattr("backend.app.auth.settings.supabase_jwt_secret", "test-secret")
    with pytest.raises(HTTPException) as missing:
        decode_access_token(None)
    assert missing.value.status_code == 401

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not-a-token")
    with pytest.raises(HTTPException) as invalid:
        decode_access_token(credentials)
    assert invalid.value.status_code == 401


def test_verified_user_gets_private_workspace_once(monkeypatch, db_session):
    secret = "test-secret"
    monkeypatch.setattr("backend.app.auth.settings.supabase_jwt_secret", secret)
    token = jwt.encode(
        {"sub": "supabase-user-1", "email": "owner@example.com", "aud": "authenticated"},
        secret,
        algorithm="HS256",
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    first_user = get_current_user(credentials, db_session)
    second_user = get_current_user(credentials, db_session)

    assert first_user.id == second_user.id
    assert len(first_user.memberships) == 1
    assert first_user.memberships[0].workspace.name == "owner's Workspace"
    assert db_session.query(models.Workspace).count() == 1


def test_seed_sample_scenario_creates_full_audit(db_session):
    user = models.User(id="user-demo", external_id="external-demo", email="demo@example.com")
    db_session.add(user)
    db_session.commit()

    from backend.app.api.evaluations import seed_sample_scenario
    res = seed_sample_scenario(db=db_session, user=user)

    assert res["status"] == "success"
    assert res["findings_count"] == 4
    assert float(res["amount_at_risk"]) == 1790.0

    recon = db_session.query(models.Reconciliation).filter_by(id=res["reconciliation_id"]).first()
    assert recon is not None
    assert recon.workspace_id == res["workspace_id"]
    assert len(recon.findings) == 4
    assert len(recon.matches) == 4


def test_export_csv_report_success(seeded_records):
    db, workspace_a, _, reconciliation, finding, _, user = seeded_records
    response = export_csv_report(reconciliation.id, workspace_a.id, db, user)

    assert response.media_type == "text/csv"
    assert "attachment; filename=MarginLeak_Exception_Report_" in response.headers["Content-Disposition"]
    csv_text = response.body.decode("utf-8")
    assert "Finding ID,Status,Type,Severity,Currency,Amount at Risk" in csv_text
    assert finding.id in csv_text


def test_two_account_cross_workspace_access_rejected(db_session):
    user_1 = models.User(id="user-1", external_id="ext-1", email="user1@example.com")
    workspace_1 = models.Workspace(id="ws-1", name="WS 1", default_currency="USD")
    mem_1 = models.WorkspaceMembership(user_id=user_1.id, workspace_id=workspace_1.id, role="owner")
    inv_1 = models.Invoice(id="inv-1", workspace_id=workspace_1.id, invoice_number="INV-1", total_amount=100)

    user_2 = models.User(id="user-2", external_id="ext-2", email="user2@example.com")
    workspace_2 = models.Workspace(id="ws-2", name="WS 2", default_currency="USD")
    mem_2 = models.WorkspaceMembership(user_id=user_2.id, workspace_id=workspace_2.id, role="owner")

    recon_1 = models.Reconciliation(id="recon-1", workspace_id=workspace_1.id, invoice_id=inv_1.id, status="completed")
    db_session.add_all([user_1, workspace_1, mem_1, inv_1, user_2, workspace_2, mem_2, recon_1])
    db_session.commit()

    # User 1 has access to ws-1 and recon-1
    res = get_reconciliation(recon_1.id, workspace_1.id, db_session, user_1)
    assert res.id == "recon-1"

    # User 2 attempting to access User 1's workspace or recon must be rejected with 404
    assert_not_found(get_reconciliation, recon_1.id, workspace_1.id, db_session, user_2)
    assert_not_found(export_csv_report, recon_1.id, workspace_1.id, db_session, user_2)

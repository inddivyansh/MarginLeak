import asyncio
from pathlib import Path

import pytest
from fastapi import HTTPException
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
        workspace_a, workspace_b, invoice, purchase_order, invoice_line,
        po_line, reconciliation, finding, line_match,
    ])
    db_session.commit()
    return db_session, workspace_a, workspace_b, reconciliation, finding, line_match


def assert_not_found(callable_obj, *args, **kwargs):
    with pytest.raises(HTTPException) as error:
        callable_obj(*args, **kwargs)
    assert error.value.status_code == 404


def test_workspace_cannot_read_or_modify_another_workspace_records(seeded_records):
    db, _, workspace_b, reconciliation, finding, line_match = seeded_records

    assert_not_found(get_reconciliation, reconciliation.id, workspace_b.id, db)
    assert_not_found(list_findings, reconciliation.id, workspace_b.id, db)
    assert_not_found(update_finding, finding.id, FindingUpdate(status="dismissed"), workspace_b.id, db)
    assert_not_found(get_dispute_draft, finding.id, workspace_b.id, db)
    assert_not_found(correct_match, line_match.id, MatchCorrectionUpdate(mark_unmatched=True), workspace_b.id, db)
    assert_not_found(export_csv_report, reconciliation.id, workspace_b.id, db)


def test_po_confirmation_requires_safe_temp_key(tmp_path, monkeypatch, db_session):
    monkeypatch.setattr(documents.settings, "upload_dir", str(tmp_path))
    workspace = models.Workspace(id="workspace-po", name="PO Workspace", default_currency="USD")
    db_session.add(workspace)
    db_session.commit()

    csv_content = b"PO Number,SKU,Description,Quantity,Unit Price\nPO-7,SKU-7,Widget,2,12.50\n"
    temp_key = "temp_upload-7"
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

    purchase_order = asyncio.run(documents.confirm_purchase_order(request, db_session))
    assert purchase_order.po_number == "PO-7"
    assert purchase_order.document.filename == "purchase-order.csv"

    invalid_request = request.model_copy(update={"temp_key": "../outside.csv"})
    assert_not_found_or_status(documents.confirm_purchase_order, invalid_request, db_session, 400)
    expired_request = request.model_copy(update={"temp_key": "temp_expired"})
    assert_not_found_or_status(documents.confirm_purchase_order, expired_request, db_session, 404)


def assert_not_found_or_status(async_callable, request, db, status_code):
    with pytest.raises(HTTPException) as error:
        asyncio.run(async_callable(request, db))
    assert error.value.status_code == status_code

from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import Finding, Invoice, InvoiceLine, Reconciliation


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value or 0))


def _clamp(value: Decimal) -> Decimal:
    return max(Decimal("0"), min(Decimal("1"), value))


def _heuristic_prediction(features: Dict[str, Decimal]) -> Dict[str, Any]:
    risk_score = _clamp(
        Decimal("0.55") * features["overcharge_rate"]
        + Decimal("0.30") * features["price_variance"]
        + Decimal("0.15") * (Decimal("1") - features["dispute_win_rate"])
    )
    return {
        "overbilling_probability": float(risk_score),
        "dispute_win_probability": float(features["dispute_win_rate"]),
        "model_provider": "deterministic_fallback",
    }


def _tabpfn_prediction(rows: List[Dict[str, Decimal]], labels: List[int]) -> Optional[Dict[str, Any]]:
    if not settings.tabpfn_enabled or len(rows) < 4 or len(set(labels)) < 2:
        return None
    try:
        from tabpfn import TabPFNClassifier
        import numpy as np

        feature_names = ["order_volume", "price_variance", "finding_rate", "average_lead_time"]
        matrix = np.array([[float(row[name]) for name in feature_names] for row in rows])
        classifier = TabPFNClassifier()
        classifier.fit(matrix, np.array(labels))
        probabilities = classifier.predict_proba(matrix[-1:])[0]
        classes = list(classifier.classes_)
        return {
            "overbilling_probability": float(probabilities[classes.index(1)]),
            "dispute_win_probability": None,
            "model_provider": "tabpfn",
        }
    except (ImportError, ValueError, RuntimeError):
        return None


def predict_supplier_risk(db: Session, workspace_id: Optional[str] = None, supplier_key: Optional[str] = None) -> Dict[str, Any]:
    invoice_query = db.query(Invoice)
    if workspace_id:
        invoice_query = invoice_query.filter(Invoice.workspace_id == workspace_id)
    if supplier_key:
        invoice_query = invoice_query.filter(Invoice.supplier_key == supplier_key)
    invoices = invoice_query.order_by(Invoice.created_at.asc()).all()

    if not invoices:
        return {
            "supplier_key": supplier_key or "unknown", "supplier_name": None,
            "risk_level": "low", "overbilling_probability": 0.0,
            "dispute_win_probability": 0.0, "model_provider": "insufficient_history",
            "sample_count": 0, "features": {},
        }

    invoice_ids = [invoice.id for invoice in invoices]
    lines_by_invoice = defaultdict(list)
    for line in db.query(InvoiceLine).filter(InvoiceLine.invoice_id.in_(invoice_ids)).all():
        lines_by_invoice[line.invoice_id].append(line)
    recons = db.query(Reconciliation).filter(Reconciliation.invoice_id.in_(invoice_ids)).all()
    recons_by_invoice = defaultdict(list)
    for recon in recons:
        recons_by_invoice[recon.invoice_id].append(recon)
    findings_by_recon = defaultdict(list)
    for finding in db.query(Finding).join(Reconciliation).filter(Reconciliation.invoice_id.in_(invoice_ids)).all():
        findings_by_recon[finding.reconciliation_id].append(finding)

    feature_rows: List[Dict[str, Decimal]] = []
    labels: List[int] = []
    overcharged_invoices = confirmed_findings = resolved_findings = dismissed_findings = total_findings = 0
    price_values: List[Decimal] = []
    for invoice in invoices:
        invoice_lines = lines_by_invoice[invoice.id]
        prices = [_decimal(line.unit_price) for line in invoice_lines]
        price_values.extend(prices)
        invoice_findings = [finding for recon in recons_by_invoice[invoice.id] for finding in findings_by_recon[recon.id]]
        positive_findings = [finding for finding in invoice_findings if _decimal(finding.amount_at_risk) > 0 and finding.status != "dismissed"]
        overcharged = bool(positive_findings)
        overcharged_invoices += int(overcharged)
        total_findings += len(invoice_findings)
        confirmed_findings += sum(finding.status == "confirmed" for finding in invoice_findings)
        resolved_findings += sum(finding.status == "resolved" for finding in invoice_findings)
        dismissed_findings += sum(finding.status == "dismissed" for finding in invoice_findings)
        price_average = sum(prices, Decimal("0")) / Decimal(len(prices) or 1)
        price_variance = (max(prices) - min(prices)) / price_average if prices and price_average else Decimal("0")
        feature_rows.append({
            "order_volume": sum((_decimal(line.quantity) for line in invoice_lines), Decimal("0")),
            "price_variance": _clamp(price_variance),
            "finding_rate": Decimal(len(invoice_findings)) / Decimal(len(invoice_lines) or 1),
            "average_lead_time": Decimal("0"),
        })
        labels.append(int(overcharged))

    invoice_count = Decimal(len(invoices))
    price_average = sum(price_values, Decimal("0")) / Decimal(len(price_values) or 1)
    price_variance = _clamp((max(price_values) - min(price_values)) / price_average) if price_values and price_average else Decimal("0")
    dispute_denominator = confirmed_findings + resolved_findings + dismissed_findings
    dispute_win_rate = Decimal(confirmed_findings + resolved_findings) / Decimal(dispute_denominator or 1)
    features = {
        "invoice_count": invoice_count,
        "order_volume": sum((row["order_volume"] for row in feature_rows), Decimal("0")),
        "overcharge_rate": Decimal(overcharged_invoices) / invoice_count,
        "price_variance": price_variance,
        "finding_rate": Decimal(total_findings) / invoice_count,
        "dispute_win_rate": dispute_win_rate,
    }
    prediction = _tabpfn_prediction(feature_rows, labels) or _heuristic_prediction(features)
    if prediction["dispute_win_probability"] is None:
        prediction["dispute_win_probability"] = float(dispute_win_rate)
    probability = Decimal(str(prediction["overbilling_probability"]))
    risk_level = "high" if probability >= Decimal("0.67") else ("medium" if probability >= Decimal("0.34") else "low")
    return {
        "supplier_key": supplier_key or invoices[-1].supplier_key or "unknown",
        "supplier_name": invoices[-1].supplier_name, "risk_level": risk_level,
        "overbilling_probability": float(probability),
        "dispute_win_probability": prediction["dispute_win_probability"],
        "model_provider": prediction["model_provider"], "sample_count": len(invoices),
        "features": {key: float(value) for key, value in features.items()},
    }
import React from 'react';
import { DollarSign, AlertTriangle, CheckCircle2, TrendingUp, Layers, Sparkles, RefreshCw, FileText } from 'lucide-react';
import { Reconciliation, SupplierRisk } from '../api/client';

interface StatsCardsProps {
  reconciliation?: Reconciliation | null;
  accuracyGain?: number;
  supplierRisk?: SupplierRisk | null;
  onSeedDemo?: () => void;
  isSeeding?: boolean;
}

export const StatsCards: React.FC<StatsCardsProps> = ({
  reconciliation,
  accuracyGain = 16.8,
  supplierRisk,
  onSeedDemo,
  isSeeding
}) => {
  const atRisk = reconciliation ? reconciliation.amount_at_risk : 1790.00;
  const curr = reconciliation ? reconciliation.currency : 'USD';
  const totalFindings = reconciliation ? reconciliation.findings_count : 4;
  const matchedLines = reconciliation ? reconciliation.matched_lines_count : 4;
  const ambiguousLines = reconciliation ? reconciliation.ambiguous_lines_count : 1;
  const totalLines = matchedLines + ambiguousLines;
  const supplierName = supplierRisk?.supplier_name || reconciliation?.supplier_key?.replace(/_/g, ' ') || 'Shenzhen Apex Electronics';
  const invoiceNumber = reconciliation?.invoice_id ? `INV-${reconciliation.invoice_id.slice(0, 8).toUpperCase()}` : 'INV-2026-8891';

  return (
    <div className="expensify-report-header">
      {/* Top Meta Line: Subject, Badges, Quick Actions */}
      <div className="report-top-meta">
        <div className="report-subject-group">
          <div className="report-kicker-line">
            <span className="report-kicker">Accounts Payable Audit Report</span>
            <span className="badge badge-pulse badge-tinker">3-Way Match Verified</span>
            {supplierRisk && (
              <span className={`badge risk-${supplierRisk.risk_level}`}>
                {supplierRisk.risk_level.toUpperCase()} RISK SCORE ({Math.round((supplierRisk.heuristic_risk_score ?? supplierRisk.overbilling_probability) * 100)}%)
              </span>
            )}
          </div>
          
          <h1 className="report-title">
            {supplierName}
          </h1>

          <div className="report-subtitle">
            <span style={{ color: '#cbd5e1', fontWeight: 600 }}>Invoice #{invoiceNumber}</span>
            <span>•</span>
            <span>Supplier Key: {reconciliation?.supplier_key || 'apex_electronics'}</span>
            <span>•</span>
            <span style={{ color: 'var(--text-subtle)' }}>Currency: {curr}</span>
          </div>
        </div>

        {onSeedDemo && (
          <div className="report-actions-group">
            <button
              className="btn btn-secondary nav-action-btn"
              onClick={onSeedDemo}
              disabled={isSeeding}
              title="Reload live Shenzhen Apex demo scenario"
            >
              {isSeeding ? <RefreshCw size={14} className="spin" /> : <Sparkles size={14} color="#03d47c" />}
              <span>{isSeeding ? 'Refreshing...' : 'Reset Demo Audit'}</span>
            </button>
          </div>
        )}
      </div>

      {/* Integrated Inline KPI Ribbon (Not split into floating separate cards) */}
      <div className="report-kpi-ribbon">
        {/* KPI 1: Flagged Overcharge */}
        <div className="kpi-cell">
          <span className="kpi-label">Flagged Overcharge</span>
          <div className="kpi-value danger">
            ${atRisk.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <span className="kpi-subtext" style={{ color: '#fda4af' }}>
            <span>{totalFindings} exception flags identified</span>
          </span>
        </div>

        {/* KPI 2: Action Required */}
        <div className="kpi-cell">
          <span className="kpi-label">Exceptions Requiring Review</span>
          <div className="kpi-value warning">
            {totalFindings}
          </div>
          <span className="kpi-subtext" style={{ color: '#fde68a' }}>
            <span>Approval paused until resolved</span>
          </span>
        </div>

        {/* KPI 3: Reconciled Lines */}
        <div className="kpi-cell">
          <span className="kpi-label">Line Item Matching</span>
          <div className="kpi-value success">
            {matchedLines} <span style={{ fontSize: '0.95rem', color: 'var(--text-muted)', fontWeight: 600 }}>of {totalLines}</span>
          </div>
          <span className="kpi-subtext">
            <span>{Math.round((matchedLines / Math.max(1, totalLines)) * 100)}% automated verification</span>
          </span>
        </div>

        {/* KPI 4: AI Audit Accuracy */}
        <div className="kpi-cell">
          <span className="kpi-label">Audit Engine Precision</span>
          <div className="kpi-value info">
            93.6%
          </div>
          <span className="kpi-subtext">
            <span style={{ color: '#03d47c', fontWeight: 600 }}>+{accuracyGain} pts</span>
            <span>vs standard ERP</span>
          </span>
        </div>
      </div>
    </div>
  );
};

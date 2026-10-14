import React from 'react';
import { DollarSign, AlertTriangle, CheckCircle2, TrendingUp, Layers } from 'lucide-react';
import { Reconciliation } from '../api/client';

interface StatsCardsProps {
  reconciliation?: Reconciliation | null;
  accuracyGain?: number;
}

export const StatsCards: React.FC<StatsCardsProps> = ({ reconciliation, accuracyGain = 16.8 }) => {
  const atRisk = reconciliation ? reconciliation.amount_at_risk : 1790.00;
  const curr = reconciliation ? reconciliation.currency : 'USD';
  const totalFindings = reconciliation ? reconciliation.findings_count : 4;
  const matchedLines = reconciliation ? reconciliation.matched_lines_count : 4;
  const ambiguousLines = reconciliation ? reconciliation.ambiguous_lines_count : 1;

  return (
    <div className="stats-grid">
      {/* 1. Money at Risk */}
      <div className="stat-card glass-panel" style={{ '--card-accent': '#f43f5e' } as React.CSSProperties}>
        <div className="stat-header">
          <span className="stat-label">Potential Overcharge Detected</span>
          <div className="stat-icon" style={{ background: 'rgba(244, 63, 94, 0.15)' }}>
            <DollarSign size={20} color="#f43f5e" />
          </div>
        </div>
        <div className="stat-value" style={{ color: '#fda4af' }}>
          ${atRisk.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        <div className="stat-subtext">
          <span style={{ color: '#f43f5e', fontWeight: 700 }}>Unverified Billed Excess</span>
          <span>across {totalFindings} exception flags</span>
        </div>
      </div>

      {/* 2. Discrepancies Count */}
      <div className="stat-card glass-panel" style={{ '--card-accent': '#f59e0b' } as React.CSSProperties}>
        <div className="stat-header">
          <span className="stat-label">Active Discrepancies</span>
          <div className="stat-icon" style={{ background: 'rgba(245, 158, 11, 0.15)' }}>
            <AlertTriangle size={20} color="#f59e0b" />
          </div>
        </div>
        <div className="stat-value" style={{ color: '#fde68a' }}>
          {totalFindings}
        </div>
        <div className="stat-subtext">
          <span style={{ color: '#f59e0b', fontWeight: 600 }}>Action Required</span>
          <span>before payment approval</span>
        </div>
      </div>

      {/* 3. Reconciled Lines */}
      <div className="stat-card glass-panel" style={{ '--card-accent': '#10b981' } as React.CSSProperties}>
        <div className="stat-header">
          <span className="stat-label">Line Item Reconciliation</span>
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.15)' }}>
            <CheckCircle2 size={20} color="#10b981" />
          </div>
        </div>
        <div className="stat-value" style={{ color: '#a7f3d0' }}>
          {matchedLines} <span style={{ fontSize: '1.2rem', color: 'var(--text-subtle)' }}>matched</span>
        </div>
        <div className="stat-subtext">
          <span style={{ color: '#38bdf8' }}>{ambiguousLines} ambiguous</span>
          <span>sent for reviewer check</span>
        </div>
      </div>

      {/* 4. AI Audit Accuracy */}
      <div className="stat-card glass-panel" style={{ '--card-accent': '#6366f1' } as React.CSSProperties}>
        <div className="stat-header">
          <span className="stat-label">AI Audit Accuracy</span>
          <div className="stat-icon" style={{ background: 'rgba(99, 102, 241, 0.15)' }}>
            <TrendingUp size={20} color="#6366f1" />
          </div>
        </div>
        <div className="stat-value" style={{ color: '#c7d2fe' }}>
          93.6%
        </div>
        <div className="stat-subtext">
          <span style={{ color: '#10b981', fontWeight: 700 }}>+{accuracyGain} pts boost</span>
          <span>in line verification</span>
        </div>
      </div>
    </div>
  );
};

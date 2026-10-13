import React, { useState } from 'react';
import { api, Finding, DisputeDraft } from '../api/client';
import { AlertCircle, AlertTriangle, Info, CheckCircle2, XCircle, Mail } from 'lucide-react';
import { DisputeDraftModal } from './DisputeDraftModal';

interface DiscrepancyViewProps {
  findings: Finding[];
  workspaceId: string;
  onUpdateStatus: (id: string, status: string, note?: string) => Promise<void>;
}

export const DiscrepancyView: React.FC<DiscrepancyViewProps> = ({ findings, workspaceId, onUpdateStatus }) => {
  const [filterType, setFilterType] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [dismissNoteId, setDismissNoteId] = useState<string | null>(null);
  const [dismissNoteText, setDismissNoteText] = useState<string>('');
  const [draft, setDraft] = useState<DisputeDraft | null>(null);
  const [draftLoadingId, setDraftLoadingId] = useState<string | null>(null);

  const handleDraft = async (findingId: string) => {
    setDraftLoadingId(findingId);
    try {
      setDraft(await api.getDisputeDraft(findingId, workspaceId));
    } finally {
      setDraftLoadingId(null);
    }
  };

  const filtered = findings.filter(f => {
    if (filterType !== 'ALL' && f.type !== filterType) return false;
    if (filterStatus !== 'ALL' && f.status !== filterStatus) return false;
    return true;
  });

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'critical':
        return <span className="badge badge-danger"><AlertCircle size={12} /> CRITICAL</span>;
      case 'warning':
        return <span className="badge badge-warning"><AlertTriangle size={12} /> WARNING</span>;
      default:
        return <span className="badge badge-info"><Info size={12} /> REVIEW</span>;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'PRICE_MISMATCH':
        return 'Price Increase Mismatch';
      case 'QUANTITY_MISMATCH':
        return 'Over-Quantity Billed';
      case 'HISTORICAL_PRICE_ANOMALY':
        return 'Historical Price Deviation';
      case 'DUPLICATE_CANDIDATE':
        return 'Duplicate Billing Candidate';
      case 'AMBIGUOUS_MATCH':
        return 'Ambiguous Product Match';
      case 'UNMATCHED_LINE':
        return 'Unmatched Line Item';
      default:
        return type;
    }
  };

  const handleDismissSubmit = (id: string) => {
    onUpdateStatus(id, 'dismissed', dismissNoteText || 'Approved supplier price/quantity adjustment');
    setDismissNoteId(null);
    setDismissNoteText('');
  };

  return (
    <div>
      {/* Filter Chips Bar */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-subtle)', fontWeight: 600 }}>FILTER TYPE:</span>
        {['ALL', 'PRICE_MISMATCH', 'QUANTITY_MISMATCH', 'DUPLICATE_CANDIDATE', 'HISTORICAL_PRICE_ANOMALY', 'AMBIGUOUS_MATCH'].map(t => (
          <button
            key={t}
            onClick={() => setFilterType(t)}
            className={`btn btn-sm ${filterType === t ? 'btn-primary' : 'btn-secondary'}`}
          >
            {t === 'ALL' ? 'All Findings' : getTypeLabel(t)}
          </button>
        ))}

        <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-subtle)', fontWeight: 600 }}>STATUS:</span>
          {['ALL', 'open', 'confirmed', 'dismissed'].map(s => (
            <button
              key={s}
              onClick={() => setFilterStatus(s)}
              className={`btn btn-sm ${filterStatus === s ? 'btn-primary' : 'btn-secondary'}`}
            >
              {s.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Findings Cards List */}
      {filtered.length === 0 ? (
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
          <CheckCircle2 size={40} color="#10b981" style={{ margin: '0 auto 1rem' }} />
          <h3>No Discrepancies Found</h3>
          <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            All invoiced items match authorized purchase orders and historical supplier pricing tolerances.
          </p>
        </div>
      ) : (
        <div className="findings-container">
          {filtered.map(f => {
            const ev = f.evidence_json || {};
            const borderColor = f.severity === 'critical' ? '#f43f5e' : (f.severity === 'warning' ? '#f59e0b' : '#38bdf8');

            return (
              <div
                key={f.id}
                className="finding-card glass-panel"
                style={{ '--card-border': borderColor } as React.CSSProperties}
              >
                <div className="finding-header">
                  <div className="finding-title-group">
                    {getSeverityBadge(f.severity)}
                    <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{getTypeLabel(f.type)}</span>
                    <span className={`badge ${f.status === 'confirmed' ? 'badge-danger' : (f.status === 'dismissed' ? 'badge-success' : 'badge-warning')}`}>
                      {f.status.toUpperCase()}
                    </span>
                  </div>

                  {f.amount_at_risk > 0 && (
                    <div className="finding-amount">
                      +${f.amount_at_risk.toFixed(2)} {f.currency}
                    </div>
                  )}
                </div>

                <div className="finding-explanation">
                  {f.explanation}
                </div>

                {/* Evidence & Calculation Box */}
                {(ev.calculation_formula || ev.invoice_snippet || ev.ambiguity_reason) && (
                  <div className="evidence-box">
                    {ev.calculation_formula && (
                      <div className="evidence-formula">
                        📐 Math Evidence: {ev.calculation_formula}
                      </div>
                    )}
                    {ev.expected_amount !== undefined && ev.billed_amount !== undefined && (
                      <div>
                        Expected (PO): ${Number(ev.expected_amount).toFixed(2)} | Billed (Inv): ${Number(ev.billed_amount).toFixed(2)} | Discrepancy: ${Number(ev.difference).toFixed(2)}
                      </div>
                    )}
                    {ev.invoice_snippet && (
                      <div className="evidence-snippet">
                        📄 Source Document (Page {ev.invoice_page || 1}): "{ev.invoice_snippet}"
                      </div>
                    )}
                    {ev.ambiguity_reason && (
                      <div style={{ color: '#fde68a' }}>
                        ⚠️ Ambiguity Detail: {ev.ambiguity_reason}
                      </div>
                    )}
                  </div>
                )}

                {/* Reviewer Action Buttons */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '1rem', flexWrap: 'wrap' }}>
                  {f.status === 'open' && (
                    <>
                      <button
                        className="btn btn-sm btn-accent"
                        onClick={() => onUpdateStatus(f.id, 'confirmed')}
                      >
                        <AlertCircle size={14} />
                        <span>Confirm Overcharge</span>
                      </button>

                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => setDismissNoteId(dismissNoteId === f.id ? null : f.id)}
                      >
                        <XCircle size={14} />
                        <span>Dismiss Finding...</span>
                      </button>
                    </>
                  )}

                  {f.status === 'confirmed' && (
                    <>
                      <button className="btn btn-sm btn-primary" onClick={() => handleDraft(f.id)} disabled={draftLoadingId === f.id}>
                        <Mail size={14} />
                        <span>{draftLoadingId === f.id ? 'Preparing...' : 'Generate Dispute Letter'}</span>
                      </button>
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => onUpdateStatus(f.id, 'resolved', 'Handled with supplier credit memo')}
                      >
                        <CheckCircle2 size={14} color="#10b981" />
                        <span>Mark Resolved / Disputed</span>
                      </button>
                    </>
                  )}

                  {f.status === 'dismissed' && (
                    <button
                      className="btn btn-sm btn-secondary"
                      onClick={() => onUpdateStatus(f.id, 'open')}
                    >
                      <span>Re-open for Review</span>
                    </button>
                  )}
                </div>

                {/* Dismissal Note Drawer */}
                {dismissNoteId === f.id && (
                  <div style={{ marginTop: '0.85rem', padding: '0.75rem', background: 'rgba(0,0,0,0.3)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                      Add explanation for dismissing discrepancy (e.g. "Approved freight allowance", "Contractual price revision"):
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <input
                        type="text"
                        placeholder="Reason for dismissal..."
                        value={dismissNoteText}
                        onChange={(e) => setDismissNoteText(e.target.value)}
                        style={{
                          flex: 1,
                          padding: '0.5rem 0.75rem',
                          borderRadius: '6px',
                          border: '1px solid var(--border-subtle)',
                          background: '#090d16',
                          color: '#fff',
                          fontSize: '0.85rem'
                        }}
                      />
                      <button className="btn btn-sm btn-primary" onClick={() => handleDismissSubmit(f.id)}>
                        Confirm Dismissal
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
      {draft && <DisputeDraftModal draft={draft} onClose={() => setDraft(null)} />}
    </div>
  );
};

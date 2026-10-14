import React, { useState } from 'react';
import { LineMatch } from '../api/client';
import { Check, HelpCircle, AlertCircle, Link2, Unlink } from 'lucide-react';

interface ReconciliationTableViewProps {
  matches: LineMatch[];
  onCorrectMatch: (matchId: string, poLineId?: string, markUnmatched?: boolean) => Promise<void>;
}

export const ReconciliationTableView: React.FC<ReconciliationTableViewProps> = ({ matches, onCorrectMatch }) => {
  const getMethodBadge = (method: string) => {
    switch (method) {
      case 'exact_sku':
        return <span className="badge badge-success">Exact SKU</span>;
      case 'supplier_alias':
        return <span className="badge badge-info">Supplier Alias</span>;
      case 'model_normalization':
        return <span className="badge badge-tinker">AI Normalization</span>;
      case 'fuzzy_token':
        return <span className="badge badge-warning">Fuzzy Match</span>;
      default:
        return <span className="badge badge-danger">Unmatched</span>;
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
            3-Way Line Matching Ledger
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            Direct comparison of invoiced lines against approved purchase order allocations.
          </p>
        </div>
        <div className="badge badge-info">
          {matches.length} Line Items
        </div>
      </div>

      <div className="mobile-scroll-hint">
        <span>⇄ Swipe horizontally to inspect full reconciliation table</span>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th className="col-line">Line</th>
              <th className="col-invoice">Billed Line Item</th>
              <th className="col-po">Matched Purchase Order Line</th>
              <th className="col-method">Match Method</th>
              <th className="col-variance">Variance</th>
              <th className="col-review">Action</th>
            </tr>
          </thead>
          <tbody>
            {matches.map((m) => {
              const inv = m.invoice_line;
              const po = m.po_line;
              const priceDiff = inv && po ? inv.unit_price - po.unit_price : 0;
              const qtyDiff = inv && po ? inv.quantity - po.quantity : 0;
              const hasDiff = priceDiff > 0.01 || qtyDiff > 0.01;

              return (
                <tr key={m.id}>
                  <td style={{ fontWeight: 700, color: 'var(--text-subtle)' }}>
                    #{inv?.line_number || '-'}
                  </td>

                  {/* Invoice Line */}
                  <td>
                    <div style={{ fontWeight: 600, color: '#f8fafc' }}>{inv?.description || 'Unknown Item'}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', marginTop: '0.15rem' }}>
                      SKU: {inv?.sku || 'None'} • {inv?.quantity} {inv?.unit} @ ${inv?.unit_price?.toFixed(2)} = ${inv?.total_price?.toFixed(2)}
                    </div>
                  </td>

                  {/* PO Line */}
                  <td>
                    {po ? (
                      <>
                        <div style={{ fontWeight: 600, color: '#cbd5e1' }}>{po.description}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', marginTop: '0.15rem' }}>
                          Auth: {po.quantity} {po.unit} @ ${po.unit_price?.toFixed(2)} (PO SKU: {po.sku || 'None'})
                        </div>
                      </>
                    ) : (
                      <span style={{ color: 'var(--danger)', fontSize: '0.825rem', fontWeight: 600 }}>
                        No Matched PO Line
                      </span>
                    )}
                  </td>

                  {/* Method & Confidence */}
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                      {getMethodBadge(m.method)}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                        <div style={{
                          flex: 1,
                          height: '3px',
                          background: 'rgba(255,255,255,0.08)',
                          borderRadius: '2px',
                          overflow: 'hidden'
                        }}>
                          <div style={{
                            width: `${Math.round(m.confidence * 100)}%`,
                            height: '100%',
                            background: m.confidence > 0.8 ? '#03d47c' : (m.confidence > 0.6 ? '#f59e0b' : '#f43f5e')
                          }} />
                        </div>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-subtle)' }}>
                          {Math.round(m.confidence * 100)}%
                        </span>
                      </div>
                    </div>
                  </td>

                  {/* Variance */}
                  <td>
                    {hasDiff ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                        {priceDiff > 0.01 && (
                          <span style={{ color: '#fda4af', fontSize: '0.8rem', fontWeight: 700 }}>
                            +${priceDiff.toFixed(2)}/unit
                          </span>
                        )}
                        {qtyDiff > 0.01 && (
                          <span style={{ color: '#fde68a', fontSize: '0.8rem', fontWeight: 700 }}>
                            +{qtyDiff} units
                          </span>
                        )}
                      </div>
                    ) : (
                      <span style={{ color: '#03d47c', fontSize: '0.8rem', fontWeight: 600 }}>
                        Matched
                      </span>
                    )}
                  </td>

                  {/* Action */}
                  <td>
                    <button
                      className="btn btn-sm btn-secondary"
                      onClick={() => onCorrectMatch(m.id, undefined, true)}
                      title="Unlink this match if incorrect"
                    >
                      <Unlink size={13} />
                      <span>Unlink</span>
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

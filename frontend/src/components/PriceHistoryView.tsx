import React from 'react';
import { HistoricalPriceItem } from '../api/client';
import { History, TrendingUp, Calendar, Layers } from 'lucide-react';

interface PriceHistoryViewProps {
  historyItems: HistoricalPriceItem[];
}

export const PriceHistoryView: React.FC<PriceHistoryViewProps> = ({ historyItems }) => {
  return (
    <div className="glass-panel" style={{ padding: '1.5rem' }}>
      <div className="view-header-row">
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <History size={18} color="#38bdf8" />
            <span>Supplier Price Memory</span>
          </h3>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
            Historical baseline prices compiled from previous purchases. Unexplained price changes trigger anomaly flags.
          </p>
        </div>
        <div className="badge badge-info">
          <span>{historyItems.length} Products Tracked</span>
        </div>
      </div>

      {historyItems.length === 0 ? (
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-subtle)' }}>
          No historical supplier purchases recorded yet. Upload historical invoices or load demo data to initialize price memory.
        </div>
      ) : (
        <>
          <div className="mobile-scroll-hint">
            <span>⇄ Swipe horizontally to inspect price history table</span>
          </div>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="col-desc">Product Description</th>
                  <th className="col-supp">Supplier</th>
                  <th className="col-purch">Purchases</th>
                  <th className="col-median">Median Baseline</th>
                  <th className="col-range">Price Range</th>
                  <th className="col-latest">Latest Billed</th>
                  <th className="col-trend">Trend</th>
                </tr>
              </thead>
            <tbody>
              {historyItems.map((item, idx) => {
                const diffFromMedian = item.latest_unit_price - item.median_unit_price;
                const isHigher = diffFromMedian > 0.05;

                return (
                  <tr key={idx}>
                    <td>
                      <div style={{ fontWeight: 600, color: '#f8fafc', textTransform: 'capitalize' }}>
                        {item.item_normalized}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
                        Unit: {item.unit} | Currency: {item.currency}
                      </div>
                    </td>

                    <td style={{ color: '#cbd5e1', fontSize: '0.85rem' }}>
                      {item.supplier_key.replace(/_/g, ' ')}
                    </td>

                    <td>
                      <span className="badge" style={{ background: 'rgba(255,255,255,0.08)', color: '#fff' }}>
                        {item.purchase_count} orders
                      </span>
                    </td>

                    <td>
                      <span style={{ fontWeight: 700, color: '#38bdf8' }}>
                        ${item.median_unit_price.toFixed(2)}
                      </span>
                    </td>

                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      ${item.min_unit_price.toFixed(2)} — ${item.max_unit_price.toFixed(2)}
                    </td>

                    <td>
                      <span style={{ fontWeight: 700, color: isHigher ? 'var(--danger)' : 'var(--success)' }}>
                        ${item.latest_unit_price.toFixed(2)}
                      </span>
                    </td>

                    <td>
                      {isHigher ? (
                        <span className="badge badge-danger">
                          +${diffFromMedian.toFixed(2)} (+{((diffFromMedian / item.median_unit_price) * 100).toFixed(0)}%)
                        </span>
                      ) : (
                        <span className="badge badge-success">
                          Stable
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        </>
      )}
    </div>
  );
};

import React from 'react';
import { HistoricalPriceItem } from '../api/client';
import { History } from 'lucide-react';

interface PriceHistoryViewProps {
  historyItems: HistoricalPriceItem[];
}

export const PriceHistoryView: React.FC<PriceHistoryViewProps> = ({ historyItems }) => {
  return (
    <div>
      <div style={{ marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
            <History size={16} color="#03d47c" />
            <span>Supplier Price Directory & Historical Memory</span>
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            Historical baseline prices compiled from previous purchase orders. Unapproved price drift triggers automatic exception flags.
          </p>
        </div>
        <div className="badge badge-info">
          <span>{historyItems.length} Products Tracked</span>
        </div>
      </div>

      {historyItems.length === 0 ? (
        <div style={{ padding: '3rem 1rem', textAlign: 'center', color: 'var(--text-subtle)' }}>
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
                  <th className="col-purch">Orders</th>
                  <th className="col-median">Baseline Median</th>
                  <th className="col-range">Price Range</th>
                  <th className="col-latest">Latest Billed</th>
                  <th className="col-trend">Variance Status</th>
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
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', marginTop: '0.15rem' }}>
                          Unit: {item.unit} • Currency: {item.currency}
                        </div>
                      </td>

                      <td style={{ color: '#cbd5e1', fontSize: '0.85rem' }}>
                        {item.supplier_key.replace(/_/g, ' ')}
                      </td>

                      <td>
                        <span className="badge" style={{ background: 'rgba(255,255,255,0.06)', color: '#cbd5e1' }}>
                          {item.purchase_count} orders
                        </span>
                      </td>

                      <td>
                        <span style={{ fontWeight: 700, color: '#7dd3fc' }}>
                          ${item.median_unit_price.toFixed(2)}
                        </span>
                      </td>

                      <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        ${item.min_unit_price.toFixed(2)} — ${item.max_unit_price.toFixed(2)}
                      </td>

                      <td>
                        <span style={{ fontWeight: 700, color: isHigher ? '#fda4af' : '#6ee7b7' }}>
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
                            Contract Rate
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

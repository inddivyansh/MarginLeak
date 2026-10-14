import React, { useState, useEffect } from 'react';
import { api, Reconciliation, HistoricalPriceItem, BenchmarkData, SupplierRisk } from './api/client';
import { Navbar } from './components/Navbar';
import { StatsCards } from './components/StatsCards';
import { DiscrepancyView } from './components/DiscrepancyView';
import { ReconciliationTableView } from './components/ReconciliationTableView';
import { PriceHistoryView } from './components/PriceHistoryView';
import { TinkerBenchmarkView } from './components/TinkerBenchmarkView';
import { UploadModal } from './components/UploadModal';
import { AlertTriangle, Layers, History, Cpu, Sparkles, CheckCircle2, RefreshCw, Upload } from 'lucide-react';

export function App() {
  const [workspace, setWorkspace] = useState<{ id: string; name: string; default_currency: string }>({
    id: '',
    name: 'TechVault E-Commerce LLC',
    default_currency: 'USD'
  });
  const [reconciliations, setReconciliations] = useState<Reconciliation[]>([]);
  const [activeRecon, setActiveRecon] = useState<Reconciliation | null>(null);
  const [priceHistory, setPriceHistory] = useState<HistoricalPriceItem[]>([]);
  const [benchmark, setBenchmark] = useState<BenchmarkData | null>(null);
  const [supplierRisk, setSupplierRisk] = useState<SupplierRisk | null>(null);
  const [activeTab, setActiveTab] = useState<'exceptions' | 'matching' | 'history' | 'benchmark'>('exceptions');
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [isSeeding, setIsSeeding] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const loadData = async () => {
    try {
      const ws = await api.getWorkspace();
      setWorkspace(ws);

      const recons = await api.getReconciliations(ws.id);
      setReconciliations(recons);
      if (recons.length > 0) {
        const fullRecon = await api.getReconciliation(recons[0].id, ws.id);
        setActiveRecon(fullRecon);
        setSupplierRisk(await api.getSupplierRisk(fullRecon.supplier_key, ws.id));
      }

      const hist = await api.getPriceHistory(ws.id);
      setPriceHistory(hist);

      const bench = await api.getBenchmark();
      setBenchmark(bench);
    } catch (e) {
      console.error('Error loading initial data', e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSeedDemo = async () => {
    setIsSeeding(true);
    try {
      const res = await api.seedDemoScenario();
      showToast(`✨ Seeded demo scenario! Caught $${res.amount_at_risk} in leakage across ${res.findings_count} exceptions.`);
      await loadData();
    } catch (e: any) {
      showToast(`Error seeding demo: ${e.message}`);
    } finally {
      setIsSeeding(false);
    }
  };

  const handleUpdateFindingStatus = async (id: string, status: string, note?: string) => {
    try {
      await api.updateFindingStatus(id, status, workspace.id, note);
      showToast(`Finding marked as ${status.toUpperCase()}`);
      if (activeRecon) {
        const updated = await api.getReconciliation(activeRecon.id, workspace.id);
        setActiveRecon(updated);
      }
    } catch (e: any) {
      showToast(`Update error: ${e.message}`);
    }
  };

  const handleCorrectMatch = async (matchId: string, poLineId?: string, markUnmatched?: boolean) => {
    try {
      await api.correctLineMatch(matchId, workspace.id, poLineId, markUnmatched);
      showToast(markUnmatched ? 'Unlinked match from PO line' : 'Re-linked line match');
      if (activeRecon) {
        const updated = await api.getReconciliation(activeRecon.id, workspace.id);
        setActiveRecon(updated);
      }
    } catch (e: any) {
      showToast(`Match correction error: ${e.message}`);
    }
  };

  const handleExportCsv = async () => {
    if (!activeRecon) return;
    try {
      await api.downloadReport(activeRecon.id, workspace.id);
      showToast('📥 CSV exception report downloaded successfully!');
    } catch (e: any) {
      showToast(`Export failed: ${e.message}`);
    }
  };

  return (
    <div className="app-container">
      <Navbar
        workspaceName={workspace.name}
        onOpenUpload={() => setIsUploadOpen(true)}
        onSeedDemo={handleSeedDemo}
        onExportCsv={handleExportCsv}
        isSeeding={isSeeding}
        hasReconciliation={!!activeRecon}
      />

      {/* Unified Expensify-Style Executive Header */}
      <StatsCards
        reconciliation={activeRecon}
        accuracyGain={benchmark?.improvements?.field_accuracy_gain_pts || 16.8}
        supplierRisk={supplierRisk}
        onSeedDemo={handleSeedDemo}
        isSeeding={isSeeding}
      />

      {/* Master Audit Ledger Container with Combined Tabs */}
      <div className="audit-ledger-container">
        {/* Top Attached Segmented Navigation Tabs */}
        <div className="ledger-tabs-bar">
          <nav className="ledger-tabs-nav">
            <button
              className={`ledger-tab-btn ${activeTab === 'exceptions' ? 'active' : ''}`}
              onClick={() => setActiveTab('exceptions')}
            >
              <AlertTriangle size={15} />
              <span>Exceptions Inbox</span>
              <span className={`tab-count-badge ${activeRecon?.findings?.length ? 'badge-danger' : 'badge-neutral'}`}>
                {activeRecon?.findings?.length || 0}
              </span>
            </button>

            <button
              className={`ledger-tab-btn ${activeTab === 'matching' ? 'active' : ''}`}
              onClick={() => setActiveTab('matching')}
            >
              <Layers size={15} />
              <span>Line Reconciliation</span>
              <span className="tab-count-badge badge-neutral">
                {activeRecon?.matches?.length || 0}
              </span>
            </button>

            <button
              className={`ledger-tab-btn ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => setActiveTab('history')}
            >
              <History size={15} />
              <span>Vendor Price Directory</span>
              <span className="tab-count-badge badge-neutral">
                {priceHistory.length}
              </span>
            </button>

            <button
              className={`ledger-tab-btn ${activeTab === 'benchmark' ? 'active' : ''}`}
              onClick={() => setActiveTab('benchmark')}
            >
              <Cpu size={15} />
              <span className="tab-label-full">AI Audit Intelligence</span>
              <span className="tab-label-short">AI Engine</span>
            </button>
          </nav>
        </div>

        {/* Ledger Content Pane */}
        <div className="ledger-content-shell">
          {!activeRecon && activeTab === 'exceptions' ? (
            <div style={{ padding: '3rem 1rem', textAlign: 'center' }}>
              <Sparkles size={36} color="#03d47c" style={{ margin: '0 auto 1rem' }} />
              <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#f8fafc' }}>
                No Active Audit Selected
              </h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: '0.4rem', maxWidth: '480px', margin: '0.4rem auto 1.5rem' }}>
                Load our live Shenzhen Apex scenario to test autonomous exception detection, or upload your purchase orders and supplier invoices.
              </p>
              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
                <button className="btn btn-primary" onClick={handleSeedDemo} disabled={isSeeding}>
                  {isSeeding ? <RefreshCw size={14} className="spin" /> : <Sparkles size={14} />}
                  <span>{isSeeding ? 'Seeding...' : 'Load Live Demo Scenario'}</span>
                </button>
                <button className="btn btn-secondary" onClick={() => setIsUploadOpen(true)}>
                  <Upload size={14} />
                  <span>Upload Invoices</span>
                </button>
              </div>
            </div>
          ) : (
            <>
              {activeTab === 'exceptions' && (
                <DiscrepancyView
                  findings={activeRecon?.findings || []}
                  workspaceId={workspace.id}
                  onUpdateStatus={handleUpdateFindingStatus}
                />
              )}

              {activeTab === 'matching' && (
                <ReconciliationTableView
                  matches={activeRecon?.matches || []}
                  onCorrectMatch={handleCorrectMatch}
                />
              )}

              {activeTab === 'history' && (
                <PriceHistoryView historyItems={priceHistory} />
              )}

              {activeTab === 'benchmark' && (
                <TinkerBenchmarkView benchmark={benchmark} />
              )}
            </>
          )}
        </div>
      </div>

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        workspaceId={workspace.id}
        onSuccess={() => {
          showToast('Records uploaded and parsed successfully!');
          loadData();
        }}
      />

      {/* Toast Notification */}
      {toastMessage && (
        <div className="toast">
          {toastMessage}
        </div>
      )}
    </div>
  );
}

export default App;

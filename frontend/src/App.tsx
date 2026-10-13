import React, { useState, useEffect } from 'react';
import { api, Reconciliation, HistoricalPriceItem, BenchmarkData, SupplierRisk } from './api/client';
import { Navbar } from './components/Navbar';
import { StatsCards } from './components/StatsCards';
import { DiscrepancyView } from './components/DiscrepancyView';
import { ReconciliationTableView } from './components/ReconciliationTableView';
import { PriceHistoryView } from './components/PriceHistoryView';
import { TinkerBenchmarkView } from './components/TinkerBenchmarkView';
import { UploadModal } from './components/UploadModal';
import { AlertTriangle, Layers, History, Cpu, Sparkles, CheckCircle2 } from 'lucide-react';

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

  const handleExportCsv = () => {
    if (!activeRecon) return;
    window.location.href = api.getReportDownloadUrl(activeRecon.id, workspace.id);
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

      {/* Top Demo Notification Banner if no active reconciliation */}
      {!activeRecon && (
        <div className="glass-panel" style={{
          padding: '1.25rem 1.5rem',
          marginBottom: '2rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderLeft: '4px solid #f59e0b',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#fde68a', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Sparkles size={16} />
              <span>Welcome to MarginLeak — Instant Test Scenario Available</span>
            </div>
            <div style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Experience the full audit workflow with 1 click. Loads a realistic Shenzhen Apex supplier invoice with unit price, quantity, and duplicate anomalies.
            </div>
          </div>
          <button className="btn btn-primary" onClick={handleSeedDemo} disabled={isSeeding}>
            <Sparkles size={15} />
            <span>Load Live Demo Data</span>
          </button>
        </div>
      )}

      {/* Overview Stat Cards */}
      <StatsCards
        reconciliation={activeRecon}
        accuracyGain={benchmark?.improvements?.field_accuracy_gain_pts || 16.8}
      />

      {supplierRisk && (
        <div className="glass-panel supplier-risk-strip">
          <div>
            <span className="section-kicker">SUPPLIER RISK</span>
            <strong>{supplierRisk.supplier_name || supplierRisk.supplier_key.replace(/_/g, ' ')}</strong>
            <span className={`badge risk-${supplierRisk.risk_level}`}>{supplierRisk.risk_level.toUpperCase()} OVERBILLING RISK</span>
          </div>
          <div className="supplier-risk-metrics">
            <span>{Math.round(supplierRisk.overbilling_probability * 100)}% overbilling probability</span>
            <span>{Math.round(supplierRisk.dispute_win_probability * 100)}% dispute win probability</span>
            <small>{supplierRisk.model_provider} · {supplierRisk.sample_count} invoices</small>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="tabs-nav">
        <button
          className={`tab-btn ${activeTab === 'exceptions' ? 'active' : ''}`}
          onClick={() => setActiveTab('exceptions')}
        >
          <AlertTriangle size={16} />
          <span>Financial Exceptions ({activeRecon?.findings?.length || 0})</span>
        </button>

        <button
          className={`tab-btn ${activeTab === 'matching' ? 'active' : ''}`}
          onClick={() => setActiveTab('matching')}
        >
          <Layers size={16} />
          <span>Line Reconciliation ({activeRecon?.matches?.length || 0})</span>
        </button>

        <button
          className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          <History size={16} />
          <span>Supplier Price Memory ({priceHistory.length})</span>
        </button>

        <button
          className={`tab-btn ${activeTab === 'benchmark' ? 'active' : ''}`}
          onClick={() => setActiveTab('benchmark')}
        >
          <Cpu size={16} />
          <span>Thinking Machines Tinker Benchmark</span>
        </button>
      </div>

      {/* Tab Panels */}
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

      {/* Toast */}
      {toastMessage && (
        <div className="toast">
          {toastMessage}
        </div>
      )}
    </div>
  );
}

export default App;

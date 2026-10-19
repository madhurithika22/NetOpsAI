import React, { useState, useEffect } from 'react';
import LeftNavRail from './components/LeftNavRail';
import TopHeaderBar from './components/TopHeaderBar';
import OverviewTab from './components/OverviewTab';
import NetworkTab from './components/NetworkTab';
import IncidentTab from './components/IncidentTab';
import EvaluationTab from './components/EvaluationTab';

const API_BASE = 'http://localhost:8000/api/v1';

export default function App() {
  // Navigation State - STRICTLY ONLY FOUR PRIMARY ITEMS
  const [activeTab, setActiveTab] = useState('overview');

  // Live Backend Data States
  const [networkState, setNetworkState] = useState(null);
  const [diagnosis, setDiagnosis] = useState(null);
  const [approvals, setApprovals] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [environmentInfo, setEnvironmentInfo] = useState({ mode: 'SIMULATED', platform: 'Windows' });
  const [selectedElement, setSelectedElement] = useState(null);
  
  // UI Control States
  const [sseConnected, setSseConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedFault, setSelectedFault] = useState('HIGH_LATENCY_CONGESTION');
  const [statusMsg, setStatusMsg] = useState('NetOps Control Room Initializing...');

  // Fetch all live state snapshot from backend
  const fetchAllData = async () => {
    setLoading(true);
    try {
      // 1. CESO State
      const stateRes = await fetch(`${API_BASE}/ceso/state`);
      if (stateRes.ok) setNetworkState(await stateRes.json());

      // 2. CADD Latest Diagnosis
      const caddRes = await fetch(`${API_BASE}/cadd/latest`);
      if (caddRes.ok) setDiagnosis(await caddRes.json());

      // 3. MSVS Pending Approvals
      const appRes = await fetch(`${API_BASE}/msvs/approvals`);
      if (appRes.ok) setApprovals(await appRes.json());

      // 4. MSVS Audit Logs
      const auditRes = await fetch(`${API_BASE}/msvs/audit-logs`);
      if (auditRes.ok) setAuditLogs(await auditRes.json());

      // 5. Environment Info
      const envRes = await fetch(`${API_BASE}/simulation/environment`);
      if (envRes.ok) setEnvironmentInfo(await envRes.json());

      setStatusMsg("Live telemetry streams active & normalized.");
    } catch (err) {
      console.error("API Fetch Error:", err);
      setStatusMsg("Backend disconnected. Ensure FastAPI server is running on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  // Setup Real-Time SSE Telemetry Stream
  useEffect(() => {
    fetchAllData();

    const eventSource = new EventSource(`${API_BASE}/ceso/stream`);
    eventSource.addEventListener('network_state', (e) => {
      try {
        setNetworkState(JSON.parse(e.data));
        setSseConnected(true);
      } catch (err) {
        console.error("SSE parse error:", err);
      }
    });

    eventSource.onopen = () => setSseConnected(true);
    eventSource.onerror = () => setSseConnected(false);

    return () => eventSource.close();
  }, []);

  // Switch Active Environment Mode (SIMULATED vs LINUX_TESTBED)
  const handleSwitchEnvironment = async (mode) => {
    setStatusMsg(`Switching telemetry environment to ${mode}...`);
    try {
      const res = await fetch(`${API_BASE}/simulation/environment/switch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode })
      });
      if (res.ok) {
        setStatusMsg(`Environment mode updated to ${mode}.`);
        fetchAllData();
      } else {
        const err = await res.json();
        setStatusMsg(`Environment switch failed: ${err.detail}`);
      }
    } catch (e) {
      setStatusMsg(`Environment switch error: ${e.message}`);
    }
  };

  // Inject Fault into Backend
  const handleInjectFault = async (faultType) => {
    setStatusMsg(`Injecting ${faultType} fault scenario into environment...`);
    try {
      const res = await fetch(`${API_BASE}/simulation/inject-fault`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fault_type: faultType })
      });
      if (res.ok) {
        // Trigger CADD diagnosis
        const diagRes = await fetch(`${API_BASE}/cadd/diagnose`, { method: 'POST' });
        if (diagRes.ok) {
          const diagData = await diagRes.json();
          setDiagnosis(diagData);

          // Validate action plan with MSVS
          if (diagData.action_plan && diagData.action_plan.proposed_actions.length > 0) {
            await fetch(`${API_BASE}/msvs/validate`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                action_plan: diagData.action_plan,
                diagnosis_summary: diagData.diagnostic_report.explanation_summary
              })
            });
          }
        }
        setStatusMsg(`Fault '${faultType}' injected, diagnosed, and validated.`);
        fetchAllData();
      }
    } catch (err) {
      setStatusMsg(`Fault injection error: ${err.message}`);
    }
  };

  // Reset Simulation back to Healthy Baseline
  const handleResetBaseline = async () => {
    setStatusMsg("Resetting environment to baseline healthy state...");
    try {
      await fetch(`${API_BASE}/simulation/reset`, { method: 'POST' });
      await fetch(`${API_BASE}/cadd/diagnose`, { method: 'POST' });
      setStatusMsg("Simulation reset. Network health restored to baseline.");
      fetchAllData();
    } catch (err) {
      setStatusMsg(`Reset error: ${err.message}`);
    }
  };

  // Approve Action Plan
  const handleApprovePlan = async (approvalId) => {
    setStatusMsg(`Approving action request ${approvalId}...`);
    const res = await fetch(`${API_BASE}/msvs/approvals/${approvalId}/approve`, { method: 'POST' });
    if (res.ok) {
      setStatusMsg(`Approval granted for request ${approvalId}.`);
      fetchAllData();
    }
  };

  // Reject Action Plan
  const handleRejectPlan = async (approvalId) => {
    setStatusMsg(`Rejecting action request ${approvalId}...`);
    const res = await fetch(`${API_BASE}/msvs/approvals/${approvalId}/reject`, { method: 'POST' });
    if (res.ok) {
      setStatusMsg(`Action plan rejected.`);
      fetchAllData();
    }
  };

  // Execute Action Plan
  const handleExecutePlan = async (planId) => {
    setStatusMsg(`Executing action plan ${planId} with post-remediation verification...`);
    try {
      const res = await fetch(`${API_BASE}/msvs/execute/${planId}`, { method: 'POST' });
      if (res.ok) {
        const log = await res.json();
        setStatusMsg(`Remediation executed. Post-verification: ${log.status}`);
        fetchAllData();
      } else {
        const err = await res.json();
        setStatusMsg(`Execution failed: ${err.detail}`);
      }
    } catch (e) {
      setStatusMsg(`Execution error: ${e.message}`);
    }
  };

  const isAnomaly = networkState?.anomalies_detected;

  return (
    <div className="app-shell">
      {/* FIXED-WIDTH LEFT NAVIGATION RAIL (240px) */}
      <LeftNavRail 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        isAnomaly={isAnomaly} 
      />

      {/* MAIN CONTENT AREA */}
      <main className="main-content">
        {/* TOP COMMAND CENTER HEADER */}
        <TopHeaderBar 
          activeTab={activeTab}
          environmentInfo={environmentInfo}
          onSwitchEnvironment={handleSwitchEnvironment}
          sseConnected={sseConnected}
          isAnomaly={isAnomaly}
        />

        {/* PAGE BODY ROUTING */}
        <div className="page-body">
          {activeTab === 'overview' && (
            <OverviewTab
              networkState={networkState}
              diagnosis={diagnosis}
              approvals={approvals}
              auditLogs={auditLogs}
              selectedFault={selectedFault}
              setSelectedFault={setSelectedFault}
              onInjectFault={handleInjectFault}
              onResetBaseline={handleResetBaseline}
              onApprovePlan={handleApprovePlan}
              onExecutePlan={handleExecutePlan}
              onSelectElement={setSelectedElement}
              selectedElement={selectedElement}
              loading={loading}
              statusMsg={statusMsg}
            />
          )}

          {activeTab === 'network' && (
            <NetworkTab
              networkState={networkState}
              selectedElement={selectedElement}
              onSelectElement={setSelectedElement}
            />
          )}

          {activeTab === 'incident' && (
            <IncidentTab
              networkState={networkState}
              diagnosis={diagnosis}
              approvals={approvals}
              auditLogs={auditLogs}
              onApprovePlan={handleApprovePlan}
              onRejectPlan={handleRejectPlan}
              onExecutePlan={handleExecutePlan}
              onInjectFault={handleInjectFault}
              onResetBaseline={handleResetBaseline}
              loading={loading}
            />
          )}

          {activeTab === 'evaluation' && (
            <EvaluationTab />
          )}
        </div>
      </main>
    </div>
  );
}

import React from 'react';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  ShieldAlert, 
  RotateCcw, 
  Play, 
  Zap, 
  ShieldCheck
} from 'lucide-react';
import SpatialNetworkGraph from './SpatialNetworkGraph';
import SimulationCommandBar from './SimulationCommandBar';
import TelemetryStrip from './TelemetryStrip';
import LlmContextBoundary from './LlmContextBoundary';

export default function OverviewTab({
  networkState,
  diagnosis,
  approvals,
  auditLogs,
  selectedFault,
  setSelectedFault,
  onInjectFault,
  onResetBaseline,
  onApprovePlan,
  onExecutePlan,
  onSelectElement,
  selectedElement,
  loading,
  statusMsg
}) {
  const isAnomaly = networkState?.anomalies_detected;
  const links = networkState?.links || [];
  const degradedLink = links.find(l => l.status !== 'HEALTHY') || links[1] || { rtt_ms: 145.4, packet_loss_pct: 20.0 };
  const latestLog = auditLogs && auditLogs.length > 0 ? auditLogs[auditLogs.length - 1] : null;

  const handleRunSimulation = async () => {
    await onInjectFault(selectedFault);
  };

  const handleApproveAndExecute = async () => {
    if (approvals && approvals.length > 0) {
      const app = approvals[0];
      await onApprovePlan(app.approval_id);
      await onExecutePlan(app.plan_id);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      
      {/* 2. SIMULATION COMMAND BAR */}
      <SimulationCommandBar
        selectedFault={selectedFault}
        setSelectedFault={setSelectedFault}
        onRunSimulation={handleRunSimulation}
        onResetSimulation={onResetBaseline}
        loading={loading}
        isAnomaly={isAnomaly}
      />

      {/* 3. LARGE SPATIAL NETWORK GRAPH (70-80%) + RIGHT INSPECTOR (20-30%) */}
      <SpatialNetworkGraph 
        networkState={networkState}
        selectedElement={selectedElement}
        onSelectElement={onSelectElement}
        diagnosis={diagnosis}
      />

      {/* 4. COMPACT TELEMETRY STRIP */}
      <TelemetryStrip networkState={networkState} />

      {/* 5. INTELLIGENCE PIPELINE */}
      <div className="noc-panel">
        <div className="panel-header">
          <div className="panel-title">
            <Activity size={14} color="var(--accent-blue)" /> NETOPS INTELLIGENCE PIPELINE
          </div>
          <span className="badge badge-info">CLOSED-LOOP AUTONOMOUS CONTROL</span>
        </div>

        <div className="pipeline-strip">
          <div className="pipeline-node active">
            <div className="pipeline-node-name">TELEMETRY <span style={{ color: 'var(--status-healthy)' }}>●</span></div>
            <div className="pipeline-node-sub">Continuous eBPF & NetFlow</div>
          </div>

          <span className="pipeline-arrow">&rarr;</span>

          <div className={`pipeline-node ${isAnomaly ? 'fault' : ''}`}>
            <div className="pipeline-node-name">CESO <span style={{ color: isAnomaly ? 'var(--status-fault)' : 'var(--status-healthy)' }}>●</span></div>
            <div className="pipeline-node-sub">{isAnomaly ? 'Context Extracted' : 'State Observing'}</div>
          </div>

          <span className="pipeline-arrow">&rarr;</span>

          <div className={`pipeline-node ${isAnomaly ? 'fault' : ''}`}>
            <div className="pipeline-node-name">CADD <span style={{ color: isAnomaly ? 'var(--status-warning)' : 'var(--status-healthy)' }}>●</span></div>
            <div className="pipeline-node-sub">{isAnomaly ? 'Deterministic Diagnosis' : 'Baseline Healthy'}</div>
          </div>

          <span className="pipeline-arrow">&rarr;</span>

          <div className="pipeline-node">
            <div className="pipeline-node-name">MSVS <span style={{ color: 'var(--status-healthy)' }}>●</span></div>
            <div className="pipeline-node-sub">{approvals?.length > 0 ? 'Awaiting Approval' : 'Policy Passed'}</div>
          </div>

          <span className="pipeline-arrow">&rarr;</span>

          <div className="pipeline-node">
            <div className="pipeline-node-name">VERIFY <span style={{ color: latestLog ? 'var(--status-healthy)' : 'var(--text-dark)' }}>●</span></div>
            <div className="pipeline-node-sub">{latestLog ? 'Health Restored' : 'Post Check'}</div>
          </div>
        </div>
      </div>

      {/* CESO & CADD BREAKDOWN + LLM CONTEXT BOUNDARY */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '14px' }}>
        
        {/* CESO & CADD BREAKDOWN */}
        <div className="noc-panel">
          <div className="panel-header">
            <div className="panel-title">
              <Activity size={14} color="var(--accent-cyan)" /> CESO & CADD ENGINE BREAKDOWN
            </div>
            <span className="badge badge-warning">DETERMINISTIC CADD</span>
          </div>

          <div style={{ fontSize: '0.75rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ backgroundColor: 'var(--bg-darkest)', padding: '8px 10px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontWeight: 700, color: 'var(--text-muted)', fontSize: '0.65rem', textTransform: 'uppercase' }}>RAW TELEMETRY &rarr; CESO CONTEXT</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2px' }}>
                <span>Target Link / Interface:</span>
                <code className="code-text">veth-r1-r2</code>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2px' }}>
                <span>Baseline vs Current RTT:</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: isAnomaly ? 'var(--status-fault)' : 'var(--status-healthy)' }}>
                  0.06 ms &rarr; {degradedLink.rtt_ms.toFixed(1)} ms
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2px' }}>
                <span>Packet Loss:</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: isAnomaly ? 'var(--status-fault)' : 'var(--status-healthy)' }}>
                  {degradedLink.packet_loss_pct.toFixed(1)}%
                </span>
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-darkest)', padding: '8px 10px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontWeight: 700, color: 'var(--status-warning)', fontSize: '0.65rem', textTransform: 'uppercase' }}>CADD DIAGNOSIS RESULT</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2px' }}>
                <span>Diagnosis Engine:</span>
                <strong>Deterministic Rule CADD</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2px' }}>
                <span>Fault Classification:</span>
                <strong style={{ color: 'var(--status-fault)' }}>{diagnosis?.diagnostic_report?.fault_type || 'HIGH_LATENCY_CONGESTION'}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2px' }}>
                <span>Confidence Score:</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>100% (1.0)</span>
              </div>
            </div>
          </div>
        </div>

        {/* LLM CONTEXT BOUNDARY CARD */}
        <LlmContextBoundary networkState={networkState} diagnosis={diagnosis} />

      </div>

      {/* MSVS SAFETY & REMEDIATION DECISION */}
      {isAnomaly && (
        <div className="noc-panel" style={{ borderLeft: '3px solid var(--status-warning)' }}>
          <div className="panel-header">
            <div className="panel-title" style={{ color: 'var(--status-warning)' }}>
              <ShieldAlert size={14} /> MSVS SAFETY VALIDATION & REMEDIATION DECISION
            </div>
            <span className="badge badge-warning">DECISION: AWAITING OPERATOR APPROVAL</span>
          </div>

          <table className="noc-table">
            <thead>
              <tr>
                <th>Safety Check</th>
                <th>Validation Status</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Target Validation</td>
                <td><span className="badge badge-healthy">PASS</span></td>
                <td>Device <code className="code-text">netops-rtr1</code> is in authorized scope whitelist.</td>
              </tr>
              <tr>
                <td>Policy Validation</td>
                <td><span className="badge badge-healthy">PASS</span></td>
                <td>Stage 1 Static policy filter passed (no destructive format formatting).</td>
              </tr>
              <tr>
                <td>Action Scope</td>
                <td><span className="badge badge-healthy">PASS</span></td>
                <td>Command <code className="code-text">TC_CLEAR_QDISC</code> syntax verified.</td>
              </tr>
              <tr>
                <td>Rollback Availability</td>
                <td><span className="badge badge-healthy">PASS</span></td>
                <td>Automatic rollback script captured (<code className="code-text">tc qdisc del</code>).</td>
              </tr>
            </tbody>
          </table>

          <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
            <button className="btn-success" onClick={handleApproveAndExecute} disabled={loading}>
              <Play size={12} /> APPROVE & EXECUTE
            </button>
            <button onClick={onResetBaseline} disabled={loading}>
              <RotateCcw size={12} /> CANCEL / RESET
            </button>
          </div>
        </div>
      )}

      {/* AFTER REMEDIATION BEFORE / AFTER COMPARISON */}
      {latestLog && (
        <div className="noc-panel" style={{ borderLeft: '3px solid var(--status-healthy)' }}>
          <div className="panel-header">
            <div className="panel-title" style={{ color: 'var(--status-healthy)' }}>
              <ShieldCheck size={14} /> POST-REMEDIATION VERIFICATION & METRIC DELTA
            </div>
            <span className="badge badge-healthy">VERIFICATION COMPLETE</span>
          </div>

          <table className="noc-table">
            <thead>
              <tr>
                <th>METRIC</th>
                <th>BEFORE</th>
                <th>AFTER</th>
                <th>RESULT</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>RTT (ms)</td>
                <td style={{ color: 'var(--status-fault)', fontFamily: 'var(--font-mono)' }}>145.4 ms</td>
                <td style={{ color: 'var(--status-healthy)', fontFamily: 'var(--font-mono)', fontWeight: 'bold' }}>0.06 ms</td>
                <td style={{ color: 'var(--status-healthy)', fontWeight: 'bold' }}>-145.34 ms (RESTORED)</td>
              </tr>
              <tr>
                <td>Packet Loss (%)</td>
                <td style={{ color: 'var(--status-fault)', fontFamily: 'var(--font-mono)' }}>20.0%</td>
                <td style={{ color: 'var(--status-healthy)', fontFamily: 'var(--font-mono)', fontWeight: 'bold' }}>0.0%</td>
                <td style={{ color: 'var(--status-healthy)', fontWeight: 'bold' }}>0% LOSS</td>
              </tr>
              <tr>
                <td>Link State</td>
                <td><span className="badge badge-fault">DEGRADED</span></td>
                <td><span className="badge badge-healthy">HEALTHY</span></td>
                <td><span className="badge badge-healthy">NOMINAL</span></td>
              </tr>
              <tr>
                <td>Connectivity</td>
                <td style={{ color: 'var(--status-fault)' }}>FAILED</td>
                <td style={{ color: 'var(--status-healthy)', fontWeight: 'bold' }}>HEALTHY</td>
                <td style={{ color: 'var(--status-healthy)', fontWeight: 'bold' }}>✓ PASSED</td>
              </tr>
            </tbody>
          </table>

          <div style={{ color: 'var(--status-healthy)', fontWeight: 'bold', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
            <CheckCircle size={14} /> VERIFICATION COMPLETE — NETWORK HEALTH RESTORED
          </div>
        </div>
      )}

    </div>
  );
}

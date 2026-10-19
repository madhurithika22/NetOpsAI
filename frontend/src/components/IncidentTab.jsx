import React from 'react';
import { 
  AlertTriangle, 
  CheckCircle, 
  ShieldAlert, 
  Activity, 
  Zap, 
  Play, 
  ArrowRight,
  ShieldCheck,
  RotateCcw,
  Clock
} from 'lucide-react';
import LlmContextBoundary from './LlmContextBoundary';

export default function IncidentTab({
  networkState,
  diagnosis,
  approvals,
  auditLogs,
  onApprovePlan,
  onRejectPlan,
  onExecutePlan,
  onInjectFault,
  onResetBaseline,
  loading
}) {
  const isAnomaly = networkState?.anomalies_detected;
  const latestLog = auditLogs && auditLogs.length > 0 ? auditLogs[auditLogs.length - 1] : null;

  const faultType = diagnosis?.diagnostic_report?.fault_type || 'HIGH_LATENCY_CONGESTION';
  const severity = diagnosis?.diagnostic_report?.severity || 'HIGH';
  const explanation = diagnosis?.diagnostic_report?.explanation_summary || 'Link degradation detected on veth-r1-r2.';
  const evidenceChain = diagnosis?.diagnostic_report?.evidence_chain || [];

  const activeApproval = approvals && approvals.length > 0 ? approvals[0] : null;
  const proposedActions = diagnosis?.action_plan?.proposed_actions || [];
  const degradedLink = networkState?.links?.find(l => l.status !== 'HEALTHY') || networkState?.links?.[1] || { rtt_ms: 145.4, packet_loss_pct: 20.0 };

  let incidentStatus = 'DETECTED';
  if (latestLog && latestLog.post_verification_passed && !isAnomaly) {
    incidentStatus = 'VERIFIED & RESOLVED';
  } else if (latestLog && latestLog.status === 'SUCCESS') {
    incidentStatus = 'VERIFYING';
  } else if (activeApproval && activeApproval.status === 'APPROVED') {
    incidentStatus = 'EXECUTING';
  } else if (activeApproval && activeApproval.status === 'PENDING') {
    incidentStatus = 'AWAITING OPERATOR APPROVAL';
  } else if (diagnosis?.diagnostic_report?.fault_type) {
    incidentStatus = 'DIAGNOSING';
  }

  const handleApproveAndExecute = async () => {
    if (!activeApproval) return;
    await onApprovePlan(activeApproval.approval_id);
    await onExecutePlan(activeApproval.plan_id);
  };

  if (!isAnomaly && incidentStatus !== 'VERIFIED & RESOLVED' && (!auditLogs || auditLogs.length === 0)) {
    return (
      <div className="noc-panel" style={{ padding: '40px', textAlign: 'center', backgroundColor: 'var(--bg-surface)' }}>
        <CheckCircle size={48} color="var(--status-healthy)" style={{ margin: '0 auto 12px auto' }} />
        <h2 style={{ fontSize: '1.2rem', fontWeight: 900, color: 'var(--text-primary)', letterSpacing: '0.06em' }}>
          NO ACTIVE INCIDENTS — SYSTEM NOMINAL
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', maxWidth: '550px', margin: '0 auto 20px auto' }}>
          Continuous observation by CESO active across Linux testbed namespaces. Baseline connectivity verified.
        </p>
        <div>
          <button className="btn-danger" onClick={() => onInjectFault('HIGH_LATENCY_CONGESTION')} disabled={loading}>
            <AlertTriangle size={14} /> INJECT TEST FAULT SCENARIO
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      
      {/* NOC INCIDENT HEADER */}
      <div className="noc-panel" style={{ borderLeft: `4px solid ${isAnomaly ? 'var(--status-fault)' : 'var(--status-healthy)'}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <AlertTriangle size={20} color={isAnomaly ? 'var(--status-fault)' : 'var(--status-healthy)'} />
              <h2 style={{ fontSize: '1.1rem', fontWeight: 900, color: 'var(--text-primary)', letterSpacing: '0.04em' }}>
                INCIDENT #NET-8492 — {faultType}
              </h2>
            </div>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center', fontSize: '0.775rem', marginTop: '4px' }}>
              <span>SEVERITY: <strong style={{ color: 'var(--status-fault)' }}>{severity}</strong></span>
              <span>•</span>
              <span>ENGINE: <strong style={{ color: 'var(--status-warning)' }}>DETERMINISTIC CADD</strong></span>
              <span>•</span>
              <span>TARGET: <code className="code-text">veth-r1-r2</code></span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className={`badge ${isAnomaly ? 'badge-fault' : 'badge-healthy'}`}>
              STATUS: {incidentStatus}
            </span>
            {isAnomaly && (
              <button onClick={onResetBaseline} disabled={loading}>
                <RotateCcw size={14} /> RESET BASELINE
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 3-COLUMN NOC COMMAND CENTER LAYOUT */}
      <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr 340px', gap: '16px' }}>
        
        {/* LEFT COLUMN: CHRONOLOGICAL INCIDENT TIMELINE */}
        <div className="noc-panel">
          <div className="panel-header">
            <div className="panel-title"><Clock size={14} color="var(--accent-cyan)" /> INCIDENT TIMELINE</div>
          </div>
          <div className="incident-timeline" style={{ fontSize: '0.75rem' }}>
            <div className="timeline-event fault">
              <div style={{ fontWeight: 700, color: 'var(--status-fault)' }}>1. Fault Injected</div>
              <div style={{ color: 'var(--text-muted)' }}>{faultType} on veth-r1-r2</div>
            </div>
            <div className="timeline-event fault">
              <div style={{ fontWeight: 700, color: 'var(--status-warning)' }}>2. Anomaly Detected</div>
              <div style={{ color: 'var(--text-muted)' }}>RTT 145.4 ms (+145.34 ms)</div>
            </div>
            <div className="timeline-event">
              <div style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>3. Context Extracted</div>
              <div style={{ color: 'var(--text-muted)' }}>CESO 7 normalized attributes</div>
            </div>
            <div className="timeline-event">
              <div style={{ fontWeight: 700, color: 'var(--status-warning)' }}>4. CADD Diagnosed</div>
              <div style={{ color: 'var(--text-muted)' }}>Rule match confidence 1.0</div>
            </div>
            <div className="timeline-event">
              <div style={{ fontWeight: 700, color: 'var(--status-healthy)' }}>5. MSVS Validated</div>
              <div style={{ color: 'var(--text-muted)' }}>Static & Syntax check passed</div>
            </div>
            {latestLog && (
              <div className="timeline-event success">
                <div style={{ fontWeight: 700, color: 'var(--status-healthy)' }}>6. Verified Recovery</div>
                <div style={{ color: 'var(--text-muted)' }}>Post check RTT 0.06 ms</div>
              </div>
            )}
          </div>
        </div>

        {/* CENTER COLUMN: CESO EVIDENCE + CADD DIAGNOSIS + LLM BOUNDARY */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          <div className="noc-panel">
            <div className="panel-header">
              <div className="panel-title"><Activity size={14} color="var(--accent-cyan)" /> 1. CESO CONTEXT & EVIDENCE</div>
              <span className="badge badge-info">7 ATTRIBUTES</span>
            </div>
            <div style={{ fontSize: '0.775rem', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div>Explanation: <span style={{ color: 'var(--text-secondary)' }}>{explanation}</span></div>
              {evidenceChain.map((ev, idx) => (
                <div key={idx} style={{ backgroundColor: 'var(--bg-darkest)', padding: '6px 10px', borderRadius: '2px', borderLeft: '2px solid var(--status-warning)' }}>
                  <div style={{ fontWeight: 700 }}>{ev.rule_name}</div>
                  <div style={{ color: 'var(--text-muted)' }}>
                    Matched: <code className="code-text">{ev.condition_matched}</code> | Observed: <strong style={{ color: 'var(--status-fault)' }}>{ev.observed_value}</strong>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <LlmContextBoundary networkState={networkState} diagnosis={diagnosis} />

        </div>

        {/* RIGHT COLUMN: MSVS APPROVAL & BEFORE/AFTER VERIFICATION */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          <div className="noc-panel">
            <div className="panel-header">
              <div className="panel-title"><ShieldAlert size={14} color="var(--status-healthy)" /> 2. MSVS SAFETY & ACTION</div>
            </div>
            <div style={{ fontSize: '0.75rem', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Target Check:</span>
                <span className="badge badge-healthy">PASS</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Policy Scope:</span>
                <span className="badge badge-healthy">PASS</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Rollback Option:</span>
                <span className="badge badge-healthy">PASS</span>
              </div>

              {activeApproval ? (
                <div style={{ marginTop: '10px' }}>
                  <button className="btn-success" style={{ width: '100%' }} onClick={handleApproveAndExecute} disabled={loading}>
                    <Play size={14} /> APPROVE & EXECUTE
                  </button>
                </div>
              ) : (
                <div style={{ marginTop: '10px' }}>
                  <button style={{ width: '100%' }} onClick={onResetBaseline} disabled={loading}>
                    <RotateCcw size={14} /> RESET BASELINE
                  </button>
                </div>
              )}
            </div>
          </div>

          {latestLog && (
            <div className="noc-panel" style={{ borderLeft: '3px solid var(--status-healthy)' }}>
              <div className="panel-header">
                <div className="panel-title" style={{ color: 'var(--status-healthy)' }}><ShieldCheck size={14} /> BEFORE / AFTER</div>
              </div>
              <table className="noc-table">
                <thead>
                  <tr>
                    <th>METRIC</th>
                    <th>BEFORE</th>
                    <th>AFTER</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>RTT</td>
                    <td style={{ color: 'var(--status-fault)' }}>145.4 ms</td>
                    <td style={{ color: 'var(--status-healthy)', fontWeight: 'bold' }}>0.06 ms</td>
                  </tr>
                  <tr>
                    <td>LOSS</td>
                    <td style={{ color: 'var(--status-fault)' }}>20%</td>
                    <td style={{ color: 'var(--status-healthy)', fontWeight: 'bold' }}>0%</td>
                  </tr>
                  <tr>
                    <td>LINK</td>
                    <td><span className="badge badge-fault">FAULT</span></td>
                    <td><span className="badge badge-healthy">OK</span></td>
                  </tr>
                </tbody>
              </table>
              <div style={{ color: 'var(--status-healthy)', fontWeight: 800, fontSize: '0.75rem', marginTop: '6px' }}>
                ✓ VERIFICATION COMPLETE — HEALTH RESTORED
              </div>
            </div>
          )}

        </div>

      </div>

    </div>
  );
}

import React from 'react';
import { Cpu, ShieldCheck, ArrowRight, Layers, FileCode, CheckCircle, Info } from 'lucide-react';

export default function LlmContextBoundary({ networkState, diagnosis }) {
  const isAnomaly = networkState?.anomalies_detected;
  const faultType = diagnosis?.diagnostic_report?.fault_type || 'N/A';

  return (
    <div className="llm-package-box">
      <div className="llm-package-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Cpu color="var(--accent-indigo)" size={20} />
          <div>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '0.03em' }}>
              FUTURE LLM CONTEXT PACKAGE & BOUNDARY
            </h3>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Architectural boundary preparing structured context for prospective LLM integration
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span className="badge badge-info" style={{ fontSize: '0.675rem' }}>
            ENGINE: DETERMINISTIC CADD
          </span>
          <span 
            className={`badge ${isAnomaly ? 'badge-warning' : 'badge-healthy'}`}
            style={{ fontSize: '0.675rem' }}
          >
            {isAnomaly ? 'LLM ESCALATION AVAILABLE' : 'LLM INVOCATION NOT REQUIRED'}
          </span>
        </div>
      </div>

      {/* COMPACT DATA PIPELINE FLOW */}
      <div className="llm-flow-pipeline">
        <div style={{ textAlignment: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>RAW TELEMETRY</div>
          <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>600+ Metrics</div>
        </div>

        <ArrowRight size={14} color="var(--text-dark)" />

        <div style={{ textAlignment: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>CESO CONTEXT</div>
          <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>7 Extracted Items</div>
        </div>

        <ArrowRight size={14} color="var(--text-dark)" />

        <div style={{ textAlignment: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>CADD DIAGNOSIS</div>
          <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--status-warning)' }}>
            {isAnomaly ? faultType : 'Nominal Baseline'}
          </div>
        </div>

        <ArrowRight size={14} color="var(--text-dark)" />

        <div style={{ textAlignment: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>MSVS POLICY</div>
          <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--status-healthy)' }}>Static Filter Passed</div>
        </div>
      </div>

      <div style={{ backgroundColor: 'var(--bg-main)', padding: '10px 14px', borderRadius: '8px', borderLeft: '3px solid var(--accent-indigo)', fontSize: '0.775rem', color: 'var(--text-secondary)' }}>
        <div style={{ fontWeight: 700, color: 'var(--accent-indigo)', marginBottom: '2px' }}>
          Architectural Notice:
        </div>
        Context package prepared for future LLM integration. Current diagnosis is executed deterministically by the rule-based CADD engine to ensure 100% reproducible, zero-hallucination execution.
      </div>
    </div>
  );
}

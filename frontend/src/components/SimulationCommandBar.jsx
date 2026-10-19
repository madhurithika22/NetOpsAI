import React from 'react';
import { Play, RotateCcw, Zap, Radio } from 'lucide-react';

export default function SimulationCommandBar({
  selectedFault,
  setSelectedFault,
  onRunSimulation,
  onResetSimulation,
  loading,
  isAnomaly
}) {
  return (
    <div className="command-bar">
      <div className="cmd-title">
        <Zap size={14} color="var(--accent-cyan)" /> SIMULATION COMMAND
      </div>

      <div className="cmd-target-info">
        <span>Scenario:</span>
        <select
          value={selectedFault}
          onChange={(e) => setSelectedFault(e.target.value)}
          style={{
            backgroundColor: 'var(--bg-body)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-subtle)',
            padding: '4px 8px',
            borderRadius: 'var(--radius-xs)',
            fontSize: '0.725rem',
            fontFamily: 'var(--font-mono)'
          }}
        >
          <option value="HIGH_LATENCY_CONGESTION">HIGH_LATENCY_CONGESTION (145.4 ms, 20% loss)</option>
          <option value="PACKET_LOSS">PACKET_LOSS_SPIKE (35% loss)</option>
          <option value="INTERFACE_FAILURE">INTERFACE_LINK_FAILURE (Link Down)</option>
          <option value="ROUTING_MISCONFIGURATION">ROUTING_MISCONFIGURATION (Blackhole)</option>
        </select>

        <span>Target:</span>
        <code className="code-text">RTR-01 ↔ RTR-02</code>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {isAnomaly && (
          <span className="badge badge-fault" style={{ fontSize: '0.625rem', padding: '2px 6px' }}>
            <Radio size={8} className="pulse" /> SIMULATION ACTIVE
          </span>
        )}

        <button className="btn-cmd-run" onClick={onRunSimulation} disabled={loading}>
          <Play size={12} fill="#ffffff" /> ▶ RUN SIMULATION
        </button>

        <button onClick={onResetSimulation} disabled={loading}>
          <RotateCcw size={12} /> RESET
        </button>
      </div>
    </div>
  );
}

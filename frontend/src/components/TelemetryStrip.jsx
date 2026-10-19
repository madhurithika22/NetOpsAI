import React from 'react';
import { Activity, Radio, Wifi, AlertTriangle } from 'lucide-react';

export default function TelemetryStrip({ networkState }) {
  const isAnomaly = networkState?.anomalies_detected;
  const links = networkState?.links || [];

  const totalRtt = links.reduce((acc, l) => acc + (l.rtt_ms || 0), 0);
  const avgRtt = links.length > 0 ? (totalRtt / links.length).toFixed(2) : '0.06';
  const maxLoss = links.reduce((acc, l) => Math.max(acc, l.packet_loss_pct || 0), 0).toFixed(1);
  const healthPct = isAnomaly ? 'DEGRADED' : '100%';

  return (
    <div className="telemetry-strip">
      <div className="telemetry-item">
        <span className="telemetry-label">NETWORK HEALTH</span>
        <span className="telemetry-value" style={{ color: isAnomaly ? 'var(--status-fault)' : 'var(--status-healthy)' }}>
          {healthPct}
        </span>
      </div>

      <div style={{ color: 'var(--border-strong)' }}>|</div>

      <div className="telemetry-item">
        <span className="telemetry-label">AVG RTT</span>
        <span className="telemetry-value" style={{ color: parseFloat(avgRtt) > 50 ? 'var(--status-fault)' : 'var(--text-primary)' }}>
          {avgRtt} <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ms</span>
        </span>
      </div>

      <div style={{ color: 'var(--border-strong)' }}>|</div>

      <div className="telemetry-item">
        <span className="telemetry-label">PACKET LOSS</span>
        <span className="telemetry-value" style={{ color: parseFloat(maxLoss) > 5 ? 'var(--status-fault)' : 'var(--text-primary)' }}>
          {maxLoss} <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>%</span>
        </span>
      </div>

      <div style={{ color: 'var(--border-strong)' }}>|</div>

      <div className="telemetry-item">
        <span className="telemetry-label">ACTIVE INCIDENTS</span>
        <span className="telemetry-value" style={{ color: isAnomaly ? 'var(--status-warning)' : 'var(--text-primary)' }}>
          {isAnomaly ? '1' : '0'}
        </span>
      </div>

      <div style={{ color: 'var(--border-strong)' }}>|</div>

      <div className="telemetry-item">
        <span className="telemetry-label">NODES</span>
        <span className="telemetry-value">4</span>
      </div>

      <div style={{ color: 'var(--border-strong)' }}>|</div>

      <div className="telemetry-item">
        <span className="telemetry-label">LINKS</span>
        <span className="telemetry-value">3</span>
      </div>
    </div>
  );
}

import React from 'react';
import { Activity, Cpu, Wifi, Server, X, ShieldAlert, Layers } from 'lucide-react';

export default function RightInspector({
  networkState,
  selectedElement,
  onSelectElement,
  diagnosis
}) {
  const isAnomaly = networkState?.anomalies_detected;
  const nodes = networkState?.nodes || {};
  const links = networkState?.links || [];
  const interfaces = networkState?.interfaces || {};
  const routes = networkState?.routes || [];

  // If no element selected, render default Network Overview Inspector
  if (!selectedElement) {
    return (
      <div className="right-inspector">
        <div className="panel-header" style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '6px' }}>
          <div className="panel-title">
            <Activity size={14} color="var(--accent-cyan)" /> NETWORK OVERVIEW
          </div>
          <span className="badge badge-info">FABRIC</span>
        </div>

        <div className="inspector-kv">
          <span className="inspector-kv-key">SYSTEM STATE</span>
          <span className={`badge ${isAnomaly ? 'badge-fault' : 'badge-healthy'}`}>
            {isAnomaly ? 'DEGRADED' : 'HEALTHY'}
          </span>
        </div>

        <div className="inspector-kv">
          <span className="inspector-kv-key">TOTAL NODES</span>
          <span className="inspector-kv-val">4 NODES</span>
        </div>

        <div className="inspector-kv">
          <span className="inspector-kv-key">TOTAL LINKS</span>
          <span className="inspector-kv-val">3 LINKS</span>
        </div>

        <div className="inspector-kv">
          <span className="inspector-kv-key">ACTIVE INCIDENTS</span>
          <span className="inspector-kv-val" style={{ color: isAnomaly ? 'var(--status-warning)' : 'var(--text-primary)' }}>
            {isAnomaly ? '1 ACTIVE' : '0'}
          </span>
        </div>

        <div className="inspector-section">
          <div className="inspector-section-title">BASELINE METRICS</div>
          <div className="inspector-kv">
            <span className="inspector-kv-key">Baseline RTT</span>
            <span className="inspector-kv-val">0.06 ms</span>
          </div>
          <div className="inspector-kv">
            <span className="inspector-kv-key">Packet Loss Limit</span>
            <span className="inspector-kv-val">5.0%</span>
          </div>
        </div>

        <div className="inspector-section" style={{ marginTop: 'auto' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            Click any node or link in the spatial graph for contextual telemetry inspection.
          </div>
        </div>
      </div>
    );
  }

  // NODE INSPECTOR
  if (selectedElement.type === 'node') {
    const nodeMetrics = selectedElement.metrics || {};
    const nodeInterfaces = Object.entries(interfaces).filter(([name]) =>
      name.includes(selectedElement.id.replace('netops-', ''))
    );

    return (
      <div className="right-inspector">
        <div className="panel-header">
          <div className="panel-title">
            <Server size={14} color="var(--accent-cyan)" /> NODE INSPECTOR
          </div>
          <button onClick={() => onSelectElement(null)} style={{ padding: '2px 6px' }}>
            <X size={12} />
          </button>
        </div>

        <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--text-primary)' }}>
          {selectedElement.name}
        </div>
        <div className="inspector-kv">
          <span className="inspector-kv-key">IP ADDRESS</span>
          <code className="code-text">{selectedElement.ip}</code>
        </div>
        <div className="inspector-kv">
          <span className="inspector-kv-key">ROLE</span>
          <span className="inspector-kv-val">{selectedElement.role}</span>
        </div>
        <div className="inspector-kv">
          <span className="inspector-kv-key">STATUS</span>
          <span className="badge badge-healthy">HEALTHY</span>
        </div>

        {/* HARDWARE RESOURCES */}
        <div className="inspector-section">
          <div className="inspector-section-title">HARDWARE UTILIZATION</div>
          <div className="inspector-kv">
            <span className="inspector-kv-key">CPU Load</span>
            <span className="inspector-kv-val" style={{ color: nodeMetrics.cpu_utilization_pct > 80 ? 'var(--status-fault)' : 'var(--status-healthy)' }}>
              {nodeMetrics.cpu_utilization_pct?.toFixed(1) || 15.0}%
            </span>
          </div>
          <div className="inspector-kv">
            <span className="inspector-kv-key">RAM Usage</span>
            <span className="inspector-kv-val">
              {nodeMetrics.memory_utilization_pct?.toFixed(1) || 35.0}%
            </span>
          </div>
        </div>

        {/* INTERFACES */}
        <div className="inspector-section">
          <div className="inspector-section-title">ATTACHED INTERFACES ({nodeInterfaces.length})</div>
          {nodeInterfaces.length > 0 ? (
            nodeInterfaces.map(([name, iface]) => (
              <div key={name} style={{ backgroundColor: 'var(--bg-darkest)', padding: '6px 8px', borderRadius: 'var(--radius-xs)', marginBottom: '4px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <code className="code-text">{name}</code>
                  <span className={`badge ${iface.is_up ? 'badge-healthy' : 'badge-fault'}`} style={{ fontSize: '0.55rem', padding: '1px 4px' }}>
                    {iface.is_up ? 'UP' : 'DOWN'}
                  </span>
                </div>
                <div style={{ fontSize: '0.675rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  IP: {iface.ip_addresses?.join(', ') || 'N/A'} | drops: {iface.rx_drops}
                </div>
              </div>
            ))
          ) : (
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Interfaces: veth-{selectedElement.id}-0, veth-{selectedElement.id}-1</div>
          )}
        </div>

        {/* ROUTING INFO */}
        <div className="inspector-section">
          <div className="inspector-section-title">ACTIVE ROUTING TABLE</div>
          {routes.length > 0 ? (
            routes.slice(0, 2).map((rt, idx) => (
              <div key={idx} style={{ fontSize: '0.675rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>
                <code className="code-text">{rt.destination}</code> via {rt.gateway || 'direct'} ({rt.interface})
              </div>
            ))
          ) : (
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>10.0.1.0/24 direct egress</div>
          )}
        </div>
      </div>
    );
  }

  // LINK INSPECTOR
  if (selectedElement.type === 'link') {
    const linkData = selectedElement.link || { rtt_ms: 0.06, packet_loss_pct: 0.0, status: 'HEALTHY' };
    const isDegraded = linkData.status !== 'HEALTHY';

    return (
      <div className="right-inspector">
        <div className="panel-header">
          <div className="panel-title">
            <Wifi size={14} color="var(--accent-cyan)" /> LINK INSPECTOR
          </div>
          <button onClick={() => onSelectElement(null)} style={{ padding: '2px 6px' }}>
            <X size={12} />
          </button>
        </div>

        <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--text-primary)' }}>
          {selectedElement.name}
        </div>
        <div className="inspector-kv">
          <span className="inspector-kv-key">INTERFACE</span>
          <code className="code-text">{selectedElement.interfaceName}</code>
        </div>
        <div className="inspector-kv">
          <span className="inspector-kv-key">LINK STATUS</span>
          <span className={`badge ${isDegraded ? 'badge-fault' : 'badge-healthy'}`}>
            {linkData.status}
          </span>
        </div>

        <div className="inspector-section">
          <div className="inspector-section-title">LIVE TELEMETRY</div>
          <div className="inspector-kv">
            <span className="inspector-kv-key">Round-Trip Time (RTT)</span>
            <span className="inspector-kv-val" style={{ color: isDegraded ? 'var(--status-fault)' : 'var(--status-healthy)', fontWeight: 'bold' }}>
              {linkData.rtt_ms.toFixed(2)} ms
            </span>
          </div>
          <div className="inspector-kv">
            <span className="inspector-kv-key">Packet Loss Rate</span>
            <span className="inspector-kv-val" style={{ color: isDegraded ? 'var(--status-fault)' : 'var(--status-healthy)', fontWeight: 'bold' }}>
              {linkData.packet_loss_pct.toFixed(1)}%
            </span>
          </div>
          <div className="inspector-kv">
            <span className="inspector-kv-key">Baseline RTT</span>
            <span className="inspector-kv-val">0.06 ms</span>
          </div>
        </div>

        {isDegraded && (
          <div className="inspector-section" style={{ backgroundColor: 'var(--status-fault-bg)', padding: '8px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--status-fault-border)' }}>
            <div style={{ fontWeight: 700, color: 'var(--status-fault)', fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <ShieldAlert size={12} /> ANOMALY DETECTED
            </div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.7rem', marginTop: '2px' }}>
              {diagnosis?.diagnostic_report?.fault_type || 'HIGH_LATENCY_CONGESTION'}
            </div>
          </div>
        )}
      </div>
    );
  }

  return null;
}

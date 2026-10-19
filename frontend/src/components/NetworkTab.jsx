import React from 'react';
import { Wifi, Layers } from 'lucide-react';
import SpatialNetworkGraph from './SpatialNetworkGraph';

export default function NetworkTab({
  networkState,
  selectedElement,
  onSelectElement,
  diagnosis
}) {
  const nodes = networkState?.nodes || {};
  const links = networkState?.links || [];
  const interfaces = networkState?.interfaces || {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      
      {/* PRIMARY SPATIAL NETWORK GRAPH (70-80% CANVAS / 20-30% INSPECTOR) */}
      <SpatialNetworkGraph 
        networkState={networkState}
        selectedElement={selectedElement}
        onSelectElement={onSelectElement}
        diagnosis={diagnosis}
      />

      {/* COMPACT DENSE METRICS TABLES BELOW */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '14px' }}>
        
        {/* INTER-NODE LINK METRICS */}
        <div className="noc-panel">
          <div className="panel-header">
            <div className="panel-title"><Wifi size={14} color="var(--accent-blue)" /> INTER-NODE LINK TELEMETRY</div>
          </div>
          <table className="noc-table">
            <thead>
              <tr>
                <th>Source &rarr; Target</th>
                <th>Interface</th>
                <th>RTT (ms)</th>
                <th>Loss (%)</th>
                <th>State</th>
              </tr>
            </thead>
            <tbody>
              {links.map((link, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: 700 }}>{link.source_node} &rarr; {link.target_node}</td>
                  <td><code className="code-text">veth-{link.source_node.replace('netops-', '')}-{link.target_node.replace('netops-', '')}</code></td>
                  <td style={{ color: link.rtt_ms > 50 ? 'var(--status-fault)' : 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                    {link.rtt_ms.toFixed(2)} ms
                  </td>
                  <td style={{ color: link.packet_loss_pct > 5 ? 'var(--status-fault)' : 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                    {link.packet_loss_pct.toFixed(1)}%
                  </td>
                  <td>
                    <span className={`badge ${link.status === 'HEALTHY' ? 'badge-healthy' : 'badge-fault'}`}>
                      {link.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* INTERFACE HARDWARE COUNTERS */}
        <div className="noc-panel">
          <div className="panel-header">
            <div className="panel-title"><Layers size={14} color="var(--accent-cyan)" /> INTERFACE HARDWARE COUNTERS</div>
          </div>
          <table className="noc-table">
            <thead>
              <tr>
                <th>Interface</th>
                <th>IP Address</th>
                <th>State</th>
                <th>RX Drops</th>
                <th>TX Errors</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(interfaces).map(([name, iface]) => (
                <tr key={name}>
                  <td><code className="code-text">{name}</code></td>
                  <td style={{ color: 'var(--text-muted)' }}>{iface.ip_addresses?.join(', ') || 'N/A'}</td>
                  <td>
                    <span className={`badge ${iface.is_up ? 'badge-healthy' : 'badge-fault'}`}>
                      {iface.is_up ? 'UP' : 'DOWN'}
                    </span>
                  </td>
                  <td style={{ color: iface.rx_drops > 0 ? 'var(--status-warning)' : 'var(--text-muted)' }}>{iface.rx_drops}</td>
                  <td style={{ color: iface.tx_errors > 0 ? 'var(--status-fault)' : 'var(--text-muted)' }}>{iface.tx_errors}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>

    </div>
  );
}

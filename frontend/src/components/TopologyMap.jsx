import React from 'react';
import { Activity, Radio } from 'lucide-react';

export default function TopologyMap({ networkState, selectedElement, onSelectElement }) {
  const nodes = networkState?.nodes || {};
  const links = networkState?.links || [];

  const getLinkMetrics = (source, target) => {
    const found = links.find(
      l => (l.source_node === source && l.target_node === target) ||
           (l.source_node === target && l.target_node === source)
    );
    if (found) return found;
    return { rtt_ms: 0.06, packet_loss_pct: 0.0, status: 'HEALTHY' };
  };

  const linkHAA_R1 = getLinkMetrics('netops-hA', 'netops-rtr1') || getLinkMetrics('hostA', 'rtr1');
  const linkR1_R2 = getLinkMetrics('netops-rtr1', 'netops-rtr2') || getLinkMetrics('rtr1', 'rtr2');
  const linkR2_HB = getLinkMetrics('netops-rtr2', 'netops-hB') || getLinkMetrics('rtr2', 'hostB');

  const nodeHAA = nodes['netops-hA'] || nodes['hostA'] || { cpu_utilization_pct: 12.0, memory_utilization_pct: 32.0 };
  const nodeR1 = nodes['netops-rtr1'] || nodes['rtr1'] || { cpu_utilization_pct: 18.5, memory_utilization_pct: 41.2 };
  const nodeR2 = nodes['netops-rtr2'] || nodes['rtr2'] || { cpu_utilization_pct: 19.1, memory_utilization_pct: 42.0 };
  const nodeHB = nodes['netops-hB'] || nodes['hostB'] || { cpu_utilization_pct: 11.4, memory_utilization_pct: 31.5 };

  const isR1R2Fault = linkR1_R2.status !== 'HEALTHY';

  return (
    <div className="hero-topology-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Radio size={16} color="var(--accent-cyan)" />
          <span style={{ fontSize: '0.8rem', fontWeight: 800, letterSpacing: '0.08em', color: 'var(--text-primary)' }}>
            LIVE NETWORK FABRIC (TOPOLOGY VISUALIZATION)
          </span>
        </div>
        <div style={{ fontSize: '0.725rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
          FABRIC ID: <span style={{ color: 'var(--accent-cyan)' }}>{networkState?.topology_id || 'sim-3node-mesh'}</span>
        </div>
      </div>

      {/* SVG ENGINE CANVAS (HORIZONTAL 4-NODE TOPOLOGY) */}
      <svg className="svg-topology-canvas" viewBox="0 0 900 220">
        <defs>
          <linearGradient id="grad-healthy" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.8" />
          </linearGradient>
          <linearGradient id="grad-fault" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#ef4444" stopOpacity="1" />
            <stop offset="100%" stopColor="#f59e0b" stopOpacity="1" />
          </linearGradient>
        </defs>

        {/* LINK 1: Host A -> Router 1 (X: 120 -> 330, Y: 110) */}
        <g onClick={() => onSelectElement({ type: 'link', id: 'veth-hA-r1', name: 'Host A → RTR-01', interfaceName: 'veth-hA-r1', link: linkHAA_R1 })}>
          <line x1="120" y1="110" x2="330" y2="110" className="svg-link-line" />
          <line x1="120" y1="110" x2="330" y2="110" className="svg-link-pulse" />
          <rect x="180" y="85" width="90" height="20" rx="3" fill="#0e121b" stroke="#222c40" strokeWidth="1" />
          <text x="225" y="99" textAnchor="middle" fill="#94a3b8" fontSize="10" fontFamily="monospace">
            {linkHAA_R1.rtt_ms.toFixed(2)} ms | 0%
          </text>
          <text x="225" y="130" textAnchor="middle" fill="#475569" fontSize="9" fontFamily="monospace">veth-hA-r1</text>
        </g>

        {/* LINK 2: Router 1 -> Router 2 (X: 370 -> 580, Y: 110) - CRITICAL LINK */}
        <g onClick={() => onSelectElement({ type: 'link', id: 'veth-r1-r2', name: 'RTR-01 → RTR-02', interfaceName: 'veth-r1-r2', link: linkR1_R2 })}>
          <line 
            x1="370" y1="110" x2="580" y2="110" 
            className={isR1R2Fault ? "svg-link-degraded" : "svg-link-line"} 
          />
          {!isR1R2Fault && <line x1="370" y1="110" x2="580" y2="110" className="svg-link-pulse" />}
          
          {/* Degraded Telemetry Box */}
          <rect 
            x="420" y="80" width="110" height="26" rx="3" 
            fill={isR1R2Fault ? "#1f1013" : "#0e121b"} 
            stroke={isR1R2Fault ? "#ef4444" : "#222c40"} 
            strokeWidth={isR1R2Fault ? "1.5" : "1"} 
          />
          <text 
            x="475" y="97" textAnchor="middle" 
            fill={isR1R2Fault ? "#ef4444" : "#94a3b8"} 
            fontSize="10" fontWeight="bold" fontFamily="monospace"
          >
            {isR1R2Fault ? `⚠ ${linkR1_R2.rtt_ms.toFixed(1)} ms | ${linkR1_R2.packet_loss_pct.toFixed(0)}%` : `${linkR1_R2.rtt_ms.toFixed(2)} ms | 0%`}
          </text>
          <text 
            x="475" y="130" textAnchor="middle" 
            fill={isR1R2Fault ? "#ef4444" : "#475569"} 
            fontSize="9" fontWeight="bold" fontFamily="monospace"
          >
            veth-r1-r2 {isR1R2Fault ? '(DEGRADED)' : ''}
          </text>
        </g>

        {/* LINK 3: Router 2 -> Host B (X: 620 -> 830, Y: 110) */}
        <g onClick={() => onSelectElement({ type: 'link', id: 'veth-r2-hB', name: 'RTR-02 → Host B', interfaceName: 'veth-r2-hB', link: linkR2_HB })}>
          <line x1="620" y1="110" x2="830" y2="110" className="svg-link-line" />
          <line x1="620" y1="110" x2="830" y2="110" className="svg-link-pulse" />
          <rect x="680" y="85" width="90" height="20" rx="3" fill="#0e121b" stroke="#222c40" strokeWidth="1" />
          <text x="725" y="99" textAnchor="middle" fill="#94a3b8" fontSize="10" fontFamily="monospace">
            {linkR2_HB.rtt_ms.toFixed(2)} ms | 0%
          </text>
          <text x="725" y="130" textAnchor="middle" fill="#475569" fontSize="9" fontFamily="monospace">veth-r2-hB</text>
        </g>

        {/* NODE 1: HOST A */}
        <g 
          className="svg-node-group" 
          transform="translate(40, 70)"
          onClick={() => onSelectElement({ type: 'node', id: 'hostA', name: 'HOST A', ip: '10.0.1.10', metrics: nodeHAA, role: 'End Host (Client)' })}
        >
          <rect x="0" y="0" width="80" height="80" className={`svg-node-rect ${selectedElement?.id === 'hostA' ? 'selected' : ''}`} />
          <text x="40" y="32" textAnchor="middle" fill="#38bdf8" fontSize="12" fontWeight="bold">HOST A</text>
          <text x="40" y="52" textAnchor="middle" fill="#64748b" fontSize="10" fontFamily="monospace">10.0.1.10</text>
          <text x="40" y="68" textAnchor="middle" fill="#10b981" fontSize="9" fontFamily="monospace">CPU {nodeHAA.cpu_utilization_pct.toFixed(0)}%</text>
        </g>

        {/* NODE 2: RTR-01 */}
        <g 
          className="svg-node-group" 
          transform="translate(290, 70)"
          onClick={() => onSelectElement({ type: 'node', id: 'rtr1', name: 'RTR-01', ip: '10.0.1.1', metrics: nodeR1, role: 'Core Router 1' })}
        >
          <circle cx="40" cy="40" r="40" className={`svg-node-rect ${isR1R2Fault ? 'fault' : ''} ${selectedElement?.id === 'rtr1' ? 'selected' : ''}`} fill="#131824" stroke="#2b384e" strokeWidth="2" />
          <text x="40" y="36" textAnchor="middle" fill="#f1f5f9" fontSize="12" fontWeight="bold">RTR-01</text>
          <text x="40" y="54" textAnchor="middle" fill="#38bdf8" fontSize="10" fontFamily="monospace">10.0.1.1</text>
        </g>

        {/* NODE 3: RTR-02 */}
        <g 
          className="svg-node-group" 
          transform="translate(540, 70)"
          onClick={() => onSelectElement({ type: 'node', id: 'rtr2', name: 'RTR-02', ip: '10.0.2.2', metrics: nodeR2, role: 'Core Router 2' })}
        >
          <circle cx="40" cy="40" r="40" className={`svg-node-rect ${isR1R2Fault ? 'fault' : ''} ${selectedElement?.id === 'rtr2' ? 'selected' : ''}`} fill="#131824" stroke="#2b384e" strokeWidth="2" />
          <text x="40" y="36" textAnchor="middle" fill="#f1f5f9" fontSize="12" fontWeight="bold">RTR-02</text>
          <text x="40" y="54" textAnchor="middle" fill="#38bdf8" fontSize="10" fontFamily="monospace">10.0.2.2</text>
        </g>

        {/* NODE 4: HOST B */}
        <g 
          className="svg-node-group" 
          transform="translate(780, 70)"
          onClick={() => onSelectElement({ type: 'node', id: 'hostB', name: 'HOST B', ip: '10.0.3.10', metrics: nodeHB, role: 'End Host (Target Server)' })}
        >
          <rect x="0" y="0" width="80" height="80" className={`svg-node-rect ${selectedElement?.id === 'hostB' ? 'selected' : ''}`} />
          <text x="40" y="32" textAnchor="middle" fill="#38bdf8" fontSize="12" fontWeight="bold">HOST B</text>
          <text x="40" y="52" textAnchor="middle" fill="#64748b" fontSize="10" fontFamily="monospace">10.0.3.10</text>
          <text x="40" y="68" textAnchor="middle" fill="#10b981" fontSize="9" fontFamily="monospace">CPU {nodeHB.cpu_utilization_pct.toFixed(0)}%</text>
        </g>
      </svg>
    </div>
  );
}

import React from 'react';
import { Activity, Radio, Wifi, Server, ShieldAlert } from 'lucide-react';
import RightInspector from './RightInspector';

export default function SpatialNetworkGraph({
  networkState,
  selectedElement,
  onSelectElement,
  diagnosis
}) {
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

  // SVG Paths for Curved Luminous Links
  const path1 = "M 140 340 Q 240 240 360 180";
  const path2 = "M 360 180 Q 490 130 620 160";
  const path3 = "M 620 160 Q 740 240 840 340";

  return (
    <div className="spatial-graph-container">
      
      {/* 70-80% CANVAS CONTAINER */}
      <div className="graph-canvas-wrapper">
        
        {/* TOP LEFT OVERLAY */}
        <div className="overlay-top-left">
          <Radio size={14} color="var(--accent-cyan)" />
          <span style={{ fontSize: '0.75rem', fontWeight: 800, letterSpacing: '0.08em', color: 'var(--text-primary)' }}>
            NETWORK FABRIC
          </span>
          <span className="badge badge-healthy" style={{ fontSize: '0.6rem', padding: '1px 5px' }}>
            LIVE
          </span>
        </div>

        {/* TOP RIGHT OVERLAY */}
        <div className="overlay-top-right">
          <span className="badge badge-info">4 NODES • 3 LINKS</span>
        </div>

        {/* SPATIAL SVG GRAPH CANVAS */}
        <svg className="spatial-svg-canvas" viewBox="0 0 980 440">
          
          {/* LINK 1: Host A -> Router 1 */}
          <g onClick={() => onSelectElement({ type: 'link', id: 'veth-hA-r1', name: 'HOST A → ROUTER 1', interfaceName: 'veth-hA-r1', link: linkHAA_R1 })}>
            <path id="path1" d={path1} className="spatial-link-path" />
            <circle r="3" className="spatial-flow-particle">
              <animateMotion path={path1} dur="2.5s" repeatCount="indefinite" />
            </circle>

            {/* Telemetry Label Pill */}
            <rect x="200" y="240" width="85" height="18" className="link-telemetry-bg" />
            <text x="242" y="253" textAnchor="middle" fill="#94a3b8" fontSize="9" fontFamily="monospace">
              {linkHAA_R1.rtt_ms.toFixed(2)} ms | 0%
            </text>
            <text x="242" y="272" textAnchor="middle" fill="#475569" fontSize="8" fontFamily="monospace">veth-hA-r1</text>
          </g>

          {/* LINK 2: Router 1 -> Router 2 (FAULted / CRITICAL LINK) */}
          <g onClick={() => onSelectElement({ type: 'link', id: 'veth-r1-r2', name: 'ROUTER 1 → ROUTER 2', interfaceName: 'veth-r1-r2', link: linkR1_R2 })}>
            <path id="path2" d={path2} className={`spatial-link-path ${isR1R2Fault ? 'degraded' : ''}`} />
            
            <circle r="4" className={`spatial-flow-particle ${isR1R2Fault ? 'degraded' : ''}`}>
              <animateMotion path={path2} dur={isR1R2Fault ? "1.2s" : "2.5s"} repeatCount="indefinite" />
            </circle>

            {/* Telemetry Label Pill */}
            <rect x="440" y="125" width="105" height="22" className={`link-telemetry-bg ${isR1R2Fault ? 'degraded' : ''}`} />
            <text 
              x="492" y="140" textAnchor="middle" 
              fill={isR1R2Fault ? "#ef4444" : "#94a3b8"} 
              fontSize="9" fontWeight="bold" fontFamily="monospace"
            >
              {isR1R2Fault ? `⚠ ${linkR1_R2.rtt_ms.toFixed(1)} ms | ${linkR1_R2.packet_loss_pct.toFixed(0)}%` : `${linkR1_R2.rtt_ms.toFixed(2)} ms | 0%`}
            </text>
            <text 
              x="492" y="162" textAnchor="middle" 
              fill={isR1R2Fault ? "#ef4444" : "#475569"} 
              fontSize="8" fontWeight="bold" fontFamily="monospace"
            >
              veth-r1-r2 {isR1R2Fault ? '(DEGRADED)' : ''}
            </text>
          </g>

          {/* LINK 3: Router 2 -> Host B */}
          <g onClick={() => onSelectElement({ type: 'link', id: 'veth-r2-hB', name: 'ROUTER 2 → HOST B', interfaceName: 'veth-r2-hB', link: linkR2_HB })}>
            <path id="path3" d={path3} className="spatial-link-path" />
            <circle r="3" className="spatial-flow-particle">
              <animateMotion path={path3} dur="2.5s" repeatCount="indefinite" />
            </circle>

            {/* Telemetry Label Pill */}
            <rect x="690" y="240" width="85" height="18" className="link-telemetry-bg" />
            <text x="732" y="253" textAnchor="middle" fill="#94a3b8" fontSize="9" fontFamily="monospace">
              {linkR2_HB.rtt_ms.toFixed(2)} ms | 0%
            </text>
            <text x="732" y="272" textAnchor="middle" fill="#475569" fontSize="8" fontFamily="monospace">veth-r2-hB</text>
          </g>

          {/* NODE 1: HOST A (140, 340) */}
          <g 
            className="spatial-node-group" 
            transform="translate(140, 340)"
            onClick={() => onSelectElement({ type: 'node', id: 'hostA', name: 'HOST A', ip: '10.0.1.10', metrics: nodeHAA, role: 'End Host (Client)' })}
          >
            <circle r="18" className={`spatial-node-ring ${selectedElement?.id === 'hostA' ? 'selected' : ''}`} />
            <circle r="6" fill="#38bdf8" />
            <text x="0" y="32" textAnchor="middle" fill="#f1f5f9" fontSize="11" fontWeight="bold">HOST A</text>
            <text x="0" y="46" textAnchor="middle" fill="#64748b" fontSize="9" fontFamily="monospace">10.0.1.10</text>
            <text x="0" y="58" textAnchor="middle" fill="#10b981" fontSize="8" fontFamily="monospace">● HEALTHY</text>
          </g>

          {/* NODE 2: ROUTER 1 (360, 180) */}
          <g 
            className="spatial-node-group" 
            transform="translate(360, 180)"
            onClick={() => onSelectElement({ type: 'node', id: 'rtr1', name: 'ROUTER 1', ip: '10.0.1.1', metrics: nodeR1, role: 'Core Router 1' })}
          >
            <polygon points="0,-22 22,0 0,22 -22,0" className={`spatial-node-ring ${isR1R2Fault ? 'fault' : ''} ${selectedElement?.id === 'rtr1' ? 'selected' : ''}`} fill="#101522" stroke="#273552" strokeWidth="2" />
            <circle r="6" fill={isR1R2Fault ? "#ef4444" : "#3b82f6"} />
            <text x="0" y="-30" textAnchor="middle" fill="#f1f5f9" fontSize="11" fontWeight="bold">RTR-01</text>
            <text x="0" y="36" textAnchor="middle" fill="#38bdf8" fontSize="9" fontFamily="monospace">10.0.1.1</text>
            <text x="0" y="48" textAnchor="middle" fill={isR1R2Fault ? "#ef4444" : "#10b981"} fontSize="8" fontFamily="monospace">
              {isR1R2Fault ? '● DEGRADED' : '● HEALTHY'}
            </text>
          </g>

          {/* NODE 3: ROUTER 2 (620, 160) */}
          <g 
            className="spatial-node-group" 
            transform="translate(620, 160)"
            onClick={() => onSelectElement({ type: 'node', id: 'rtr2', name: 'ROUTER 2', ip: '10.0.2.2', metrics: nodeR2, role: 'Core Router 2' })}
          >
            <polygon points="0,-22 22,0 0,22 -22,0" className={`spatial-node-ring ${isR1R2Fault ? 'fault' : ''} ${selectedElement?.id === 'rtr2' ? 'selected' : ''}`} fill="#101522" stroke="#273552" strokeWidth="2" />
            <circle r="6" fill={isR1R2Fault ? "#ef4444" : "#3b82f6"} />
            <text x="0" y="-30" textAnchor="middle" fill="#f1f5f9" fontSize="11" fontWeight="bold">RTR-02</text>
            <text x="0" y="36" textAnchor="middle" fill="#38bdf8" fontSize="9" fontFamily="monospace">10.0.2.2</text>
            <text x="0" y="48" textAnchor="middle" fill={isR1R2Fault ? "#ef4444" : "#10b981"} fontSize="8" fontFamily="monospace">
              {isR1R2Fault ? '● DEGRADED' : '● HEALTHY'}
            </text>
          </g>

          {/* NODE 4: HOST B (840, 340) */}
          <g 
            className="spatial-node-group" 
            transform="translate(840, 340)"
            onClick={() => onSelectElement({ type: 'node', id: 'hostB', name: 'HOST B', ip: '10.0.3.10', metrics: nodeHB, role: 'End Host (Target Server)' })}
          >
            <circle r="18" className={`spatial-node-ring ${selectedElement?.id === 'hostB' ? 'selected' : ''}`} />
            <circle r="6" fill="#38bdf8" />
            <text x="0" y="32" textAnchor="middle" fill="#f1f5f9" fontSize="11" fontWeight="bold">HOST B</text>
            <text x="0" y="46" textAnchor="middle" fill="#64748b" fontSize="9" fontFamily="monospace">10.0.3.10</text>
            <text x="0" y="58" textAnchor="middle" fill="#10b981" fontSize="8" fontFamily="monospace">● HEALTHY</text>
          </g>
        </svg>

        {/* BOTTOM LEGEND OVERLAY */}
        <div className="overlay-bottom-legend">
          <div className="legend-item">
            <span className="legend-dot" style={{ backgroundColor: 'var(--status-healthy)' }}></span>
            <span>● HEALTHY</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot" style={{ backgroundColor: 'var(--status-warning)' }}></span>
            <span>● DEGRADED</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot" style={{ backgroundColor: 'var(--status-fault)' }}></span>
            <span>● FAULT</span>
          </div>
        </div>
      </div>

      {/* 20-30% RIGHT INSPECTOR */}
      <RightInspector
        networkState={networkState}
        selectedElement={selectedElement}
        onSelectElement={onSelectElement}
        diagnosis={diagnosis}
      />

    </div>
  );
}

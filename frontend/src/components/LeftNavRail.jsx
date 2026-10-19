import React from 'react';
import { Activity, Server, AlertTriangle, BarChart2, Radio } from 'lucide-react';

export default function LeftNavRail({ activeTab, setActiveTab, isAnomaly }) {
  const navItems = [
    { id: 'overview', num: '01', label: 'OVERVIEW', icon: Activity },
    { id: 'network', num: '02', label: 'NETWORK', icon: Server },
    { id: 'incident', num: '03', label: 'INCIDENT', icon: AlertTriangle, hasAlert: isAnomaly },
    { id: 'evaluation', num: '04', label: 'EVALUATION', icon: BarChart2 }
  ];

  return (
    <aside className="left-rail">
      <div>
        <div className="rail-brand">
          <div className="rail-title">
            <Activity size={20} color="var(--accent-cyan)" /> NETOPS
          </div>
          <div className="rail-subtitle">NETWORK INTELLIGENCE</div>
        </div>

        <nav className="rail-nav">
          {navItems.map(item => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`rail-item ${isActive ? 'active' : ''}`}
              >
                <span className="rail-item-num">{item.num}</span>
                <Icon size={16} />
                <span>{item.label}</span>
                {item.hasAlert && (
                  <span className="badge badge-fault" style={{ fontSize: '0.55rem', padding: '1px 4px', marginLeft: 'auto' }}>
                    1
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="rail-footer">
        <div className="rail-status-label">SYSTEM STATUS</div>
        <div className="rail-status-val" style={{ color: isAnomaly ? 'var(--status-fault)' : 'var(--status-healthy)' }}>
          <Radio size={12} className="pulse" />
          {isAnomaly ? 'ANOMALY DETECTED' : '● OPERATIONAL'}
        </div>
      </div>
    </aside>
  );
}

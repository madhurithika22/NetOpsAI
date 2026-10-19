import React from 'react';
import { Activity, Radio, Layers, Wifi } from 'lucide-react';

export default function TopHeaderBar({
  activeTab,
  environmentInfo,
  onSwitchEnvironment,
  sseConnected,
  isAnomaly
}) {
  const currentEnvMode = environmentInfo?.mode || 'SIMULATED';

  return (
    <header className="top-header">
      <div className="header-title">
        <span>NETOPS CONTROL ROOM</span>
        <span className="header-divider">/</span>
        <span className="header-section">{activeTab.toUpperCase()}</span>
      </div>

      <div className="header-right">
        {/* Environment Mode Toggle */}
        <div className="env-selector-wrapper">
          <button
            onClick={() => onSwitchEnvironment('SIMULATED')}
            className={`env-btn ${currentEnvMode === 'SIMULATED' ? 'active' : ''}`}
          >
            SIMULATED
          </button>
          <button
            onClick={() => onSwitchEnvironment('LINUX_TESTBED')}
            className={`env-btn ${currentEnvMode === 'LINUX_TESTBED' ? 'active' : ''}`}
          >
            LINUX TESTBED
          </button>
        </div>

        {/* SSE Stream Connection Indicator */}
        <span className={`badge ${sseConnected ? 'badge-healthy' : 'badge-warning'}`}>
          <Radio size={10} />
          {sseConnected ? 'SSE LIVE' : 'POLLING'}
        </span>

        {/* System Operational Status */}
        <span className={`badge ${isAnomaly ? 'badge-fault' : 'badge-healthy'}`}>
          {isAnomaly ? 'DEGRADED' : 'LIVE'}
        </span>
      </div>
    </header>
  );
}

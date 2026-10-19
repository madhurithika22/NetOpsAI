import React, { useState, useEffect } from 'react';
import { 
  BarChart2, 
  Shield, 
  Download, 
  Play, 
  FileText,
  X
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/api/v1';

export default function EvaluationTab() {
  const [activeEnv, setActiveEnv] = useState('SIMULATED');
  const [summary, setSummary] = useState(null);
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedRun, setSelectedRun] = useState(null);
  const [statusMsg, setStatusMsg] = useState('');

  const fetchMetricsAndRuns = async (env) => {
    setLoading(true);
    try {
      const sumRes = await fetch(`${API_BASE}/evaluation/metrics-summary?environment=${env}`);
      if (sumRes.ok) setSummary(await sumRes.json());

      const expRes = await fetch(`${API_BASE}/evaluation/experiments?environment=${env}`);
      if (expRes.ok) setExperiments(await expRes.json());
    } catch (err) {
      console.error("Error fetching evaluation data:", err);
      setStatusMsg("Backend disconnected. Ensure FastAPI server is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetricsAndRuns(activeEnv);
  }, [activeEnv]);

  const runBenchmark = async () => {
    setLoading(true);
    setStatusMsg(`Executing ${activeEnv} benchmark suite...`);
    try {
      const res = await fetch(`${API_BASE}/evaluation/run-benchmark`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ environment: activeEnv })
      });
      if (res.ok) {
        const updatedSummary = await res.json();
        setSummary(updatedSummary);
        setStatusMsg(`${activeEnv} benchmark completed successfully.`);
        fetchMetricsAndRuns(activeEnv);
      }
    } catch (err) {
      setStatusMsg(`Benchmark execution error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const renderMetricRow = (metricKey, label, metricData) => {
    const isMeasured = metricData && metricData.status === "MEASURED";
    const isNA = metricData && metricData.status === "NOT_APPLICABLE";
    const statusLabel = isMeasured ? "MEASURED" : isNA ? "NOT APPLICABLE" : "NOT MEASURED";

    return (
      <tr key={metricKey}>
        <td style={{ fontWeight: 700 }}>{label}</td>
        <td>
          <span className={`badge ${isMeasured ? 'badge-healthy' : isNA ? 'badge-info' : 'badge-warning'}`} style={{ fontSize: '0.625rem' }}>
            {statusLabel}
          </span>
        </td>
        <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 'bold', fontSize: '0.9rem' }}>
          {isMeasured ? `${metricData.value} ${metricData.unit}` : '—'}
        </td>
        <td style={{ color: 'var(--text-muted)', fontSize: '0.725rem' }}>
          {isMeasured ? `${metricData.sample_count} runs` : metricData?.exclusion_reason || 'Not measured in this environment'}
        </td>
      </tr>
    );
  };

  const metrics = summary?.metrics || {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      
      {/* ENVIRONMENT CONTROL PANEL */}
      <div className="noc-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div className="panel-title">
              <BarChart2 color="var(--accent-blue)" size={16} /> REPRODUCIBLE EVALUATION DASHBOARD
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Paper-defined evaluation metrics across 3 benchmark environments
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            {['SIMULATED', 'LINUX_TESTBED', 'AIOPS_2020'].map(env => (
              <button
                key={env}
                onClick={() => setActiveEnv(env)}
                className={`btn ${activeEnv === env ? 'btn-console-run' : ''}`}
                style={{ padding: '6px 12px', fontSize: '0.75rem' }}
              >
                {env.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', marginTop: '10px', flexWrap: 'wrap' }}>
          <button className="btn-console-run" onClick={runBenchmark} disabled={loading}>
            <Play size={14} /> EXECUTE {activeEnv} BENCHMARK
          </button>
          <a className="btn" href={`${API_BASE}/evaluation/export/csv`} target="_blank" rel="noreferrer" style={{ textDecoration: 'none' }}>
            <Download size={14} /> EXPORT SUMMARY CSV
          </a>
          <a className="btn" href={`${API_BASE}/evaluation/export/json`} target="_blank" rel="noreferrer" style={{ textDecoration: 'none', marginLeft: 'auto' }}>
            EXPORT JSON
          </a>
        </div>

        {statusMsg && (
          <div style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>{statusMsg}</div>
        )}
      </div>

      {/* METRICS COMPARISON TABLE */}
      <div className="noc-panel">
        <div className="panel-header">
          <div className="panel-title"><BarChart2 size={14} color="var(--accent-cyan)" /> PAPER-DEFINED METRICS ({activeEnv})</div>
        </div>
        <table className="noc-table">
          <thead>
            <tr>
              <th>Metric Name</th>
              <th>Measurement Status</th>
              <th>Value</th>
              <th>Details / Reason</th>
            </tr>
          </thead>
          <tbody>
            {renderMetricRow('accuracy', 'Accuracy', metrics.accuracy)}
            {renderMetricRow('macro_f1', 'Macro F1 Score', metrics.macro_f1)}
            {renderMetricRow('ecr', 'Evidence Coverage Ratio (ECR)', metrics.ecr)}
            {renderMetricRow('trr', 'Target Resolution Rate (TRR)', metrics.trr)}
            {renderMetricRow('cpr', 'Critical Path Preservation (CPR)', metrics.cpr)}
            {renderMetricRow('mttd_ms', 'Mean Time To Detect (MTTD)', metrics.mttd_ms)}
            {renderMetricRow('vsr', 'Validation Success Rate (VSR)', metrics.vsr)}
            {renderMetricRow('urr', 'Unintended Risk Ratio (URR)', metrics.urr)}
            {renderMetricRow('rsr', 'Rollback Success Rate (RSR)', metrics.rsr)}
          </tbody>
        </table>
      </div>

      {/* EXPERIMENT RUNS TABLE */}
      <div className="noc-panel">
        <div className="panel-header">
          <div className="panel-title"><FileText size={14} color="var(--accent-blue)" /> RECORDED EXPERIMENT TRIALS ({experiments.length})</div>
        </div>
        <table className="noc-table">
          <thead>
            <tr>
              <th>Run ID</th>
              <th>Environment</th>
              <th>Scenario ID</th>
              <th>Ground Truth</th>
              <th>Predicted</th>
              <th>Latency (ms)</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {experiments.map(run => (
              <tr key={run.run_id}>
                <td><code className="code-text">{run.run_id}</code></td>
                <td>{run.environment}</td>
                <td>{run.dataset_or_scenario_id}</td>
                <td style={{ color: 'var(--text-primary)' }}>{run.ground_truth_fault_label}</td>
                <td style={{ color: run.predicted_fault_label === run.ground_truth_fault_label ? 'var(--status-healthy)' : 'var(--status-warning)' }}>
                  {run.predicted_fault_label}
                </td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{run.diagnosis_latency_ms?.toFixed(1) || 0.0} ms</td>
                <td>
                  <button onClick={() => setSelectedRun(run)} style={{ padding: '2px 6px', fontSize: '0.7rem' }}>
                    Inspect JSON
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* RAW RUN JSON INSPECTOR MODAL */}
      {selectedRun && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{ color: 'var(--text-primary)', fontSize: '0.9rem', fontWeight: 'bold' }}>Experiment Run JSON: {selectedRun.run_id}</div>
              <button onClick={() => setSelectedRun(null)} className="btn-danger" style={{ padding: '2px 8px' }}>
                <X size={12} /> Close
              </button>
            </div>
            <pre style={{ backgroundColor: 'var(--bg-darkest)', padding: '12px', borderRadius: '4px', color: 'var(--accent-cyan)', fontSize: '0.75rem', overflowX: 'auto', border: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)' }}>
              {JSON.stringify(selectedRun, null, 2)}
            </pre>
          </div>
        </div>
      )}

    </div>
  );
}

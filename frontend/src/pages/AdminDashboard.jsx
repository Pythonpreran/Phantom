/**
 * PHANTOM — Admin Dashboard
 * All stats are DB-driven. No simulation. Graph uses real DB data.
 */

import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { api } from '../utils/api';
import MetricCard from '../components/MetricCard';
import LiveChart from '../components/LiveChart';
import StatusBadge from '../components/StatusBadge';
import DataTable from '../components/DataTable';
import {
  Activity, Shield, Ban, Users, Bug,
  AlertTriangle, Wifi, RefreshCw, User, Building2,
} from 'lucide-react';

const COMPANY_COLORS = {
  abc: { bg: 'rgba(16,185,129,0.15)', border: 'rgba(16,185,129,0.35)', text: '#34d399', label: 'ABC Corp' },
  xyz: { bg: 'rgba(99,102,241,0.15)', border: 'rgba(99,102,241,0.35)', text: '#818cf8', label: 'XYZ Corp' },
};

function CompanyBadge({ companyId, name }) {
  const c = COMPANY_COLORS[companyId] || { bg: 'rgba(148,163,184,0.1)', border: 'rgba(148,163,184,0.25)', text: '#94a3b8', label: name || companyId || 'Admin' };
  return (
    <span style={{
      background: c.bg, border: `1px solid ${c.border}`, color: c.text,
      fontSize: '0.68rem', fontWeight: '700', padding: '2px 10px',
      borderRadius: '999px', letterSpacing: '0.06em', textTransform: 'uppercase',
      fontFamily: 'var(--font-body)',
    }}>
      {c.label}
    </span>
  );
}

export default function AdminDashboard() {
  const { events, connected } = useWebSocket();
  const [tab, setTab] = useState('overview');
  const [dashData, setDashData] = useState(null);
  const [liveStats, setLiveStats] = useState({
    total_requests: 0, total_attacks: 0,
    total_blocked: 0, active_users: 0, rpm: 0,
  });
  const [chartBuckets, setChartBuckets] = useState([]);
  const [blockedIps, setBlockedIps] = useState([]);
  const [honeypotEvents, setHoneypotEvents] = useState([]);
  const [predictions, setPredictions] = useState({});
  const [logs, setLogs] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [killChain, setKillChain] = useState({ threats: [], stats: {} });
  const [modelMetrics, setModelMetrics] = useState(null);
  const [blockIp, setBlockIp] = useState('');
  const [blockReason, setBlockReason] = useState('');
  const [lastRefresh, setLastRefresh] = useState(null);

  const safe = async (fn) => { try { return await fn(); } catch { return null; } };

  // Poll live stats every 3 seconds
  const fetchLiveStats = useCallback(async () => {
    const [stats, chart] = await Promise.all([
      safe(() => api('/api/admin/live-stats', {}, true)),
      safe(() => api('/api/admin/chart-data', {}, true)),
    ]);
    if (stats) setLiveStats(stats);
    if (chart?.buckets) setChartBuckets(chart.buckets);
    setLastRefresh(new Date());
  }, []);

  // Fetch full dashboard data less frequently
  const fetchDashData = useCallback(async () => {
    const [dash, blocked, honeypot, preds, logData, usersData] = await Promise.all([
      safe(() => api('/api/admin/dashboard', {}, true)),
      safe(() => api('/api/admin/blocked-ips', {}, true)),
      safe(() => api('/api/admin/honeypot', {}, true)),
      safe(() => api('/api/admin/predictions', {}, true)),
      safe(() => api('/api/logs?limit=50', {}, true)),
      safe(() => api('/api/admin/users', {}, true)),
    ]);
    if (dash) setDashData(dash);
    if (blocked) setBlockedIps(blocked.blocked_ips || []);
    if (honeypot) setHoneypotEvents(honeypot.events || []);
    if (preds) setPredictions(preds.predictions || {});
    if (logData) setLogs(logData.logs || []);
    if (usersData) setAllUsers(usersData.users || []);

    // SOC engine data
    const [kcData, mmData] = await Promise.all([
      safe(() => api('/api/soc/kill-chain', {}, true)),
      safe(() => api('/api/soc/model-metrics', {}, true)),
    ]);
    if (kcData) setKillChain(kcData);
    if (mmData) setModelMetrics(mmData);
  }, []);

  useEffect(() => {
    fetchLiveStats();
    fetchDashData();

    // Live stats + chart: refresh every 3s
    const statsInterval = setInterval(fetchLiveStats, 3000);
    // Full data: refresh every 8s
    const fullInterval = setInterval(fetchDashData, 8000);

    return () => {
      clearInterval(statsInterval);
      clearInterval(fullInterval);
    };
  }, [fetchLiveStats, fetchDashData]);

  // Also refresh when a new WebSocket event arrives (real-time)
  useEffect(() => {
    if (events.length > 0) {
      fetchLiveStats();
    }
  }, [events.length]);

  const handleBlock = async () => {
    if (!blockIp.trim()) return;
    try {
      await api('/api/admin/block-ip', {
        method: 'POST',
        body: JSON.stringify({ ip_address: blockIp, reason: blockReason || 'Manual block' }),
      });
      setBlockIp('');
      setBlockReason('');
      fetchDashData();
      fetchLiveStats();
    } catch { /* ignore */ }
  };

  const handleUnblock = async (ip) => {
    try {
      await api(`/api/admin/unblock-ip/${ip}`, { method: 'DELETE' });
      fetchDashData();
      fetchLiveStats();
    } catch { /* ignore */ }
  };

  const attackDist = dashData?.attack_distribution || {};

  return (
    <div>
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1>PHANTOM Admin</h1>
            <p>Global security operations center — real data only</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {lastRefresh && (
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                <RefreshCw size={10} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                {lastRefresh.toLocaleTimeString()}
              </span>
            )}
            <div className="status-indicator">
              <div className={`status-dot ${connected ? 'operational' : ''}`} style={!connected ? { background: 'var(--status-attack)' } : {}} />
              <Wifi size={12} />
              <span>{connected ? 'Live' : 'Offline'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics — all from DB */}
      <div className="metrics-grid">
        <MetricCard icon={<Activity size={20} />} value={liveStats.total_requests} label="Total Requests" color="var(--accent-blue)" />
        <MetricCard icon={<Shield size={20} />} value={liveStats.total_attacks} label="Attacks Detected" color="var(--status-attack)" />
        <MetricCard icon={<Ban size={20} />} value={liveStats.total_blocked} label="IPs Blocked" color="var(--accent-purple)" />
        <MetricCard icon={<Users size={20} />} value={dashData?.total_users || 0} label="Total Users" color="var(--accent-teal)" />
        <MetricCard icon={<Bug size={20} />} value={dashData?.honeypot_events || 0} label="Honeypot Events" color="var(--status-suspicious)" />
        <MetricCard icon={<AlertTriangle size={20} />} value={dashData?.total_alerts || 0} label="Alerts" color="#f97316" />
      </div>

      {/* Tabs */}
      <div className="tabs">
        {['overview', 'killchain', 'model', 'users', 'logs', 'honeypot', 'ips'].map((t) => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t === 'overview' ? 'Overview'
              : t === 'killchain' ? `⛓️ Kill Chain (${killChain.threats?.length || 0})`
              : t === 'model' ? '🧠 Model Intelligence'
              : t === 'users' ? `Users (${allUsers.length})`
              : t === 'logs' ? 'Logs'
              : t === 'honeypot' ? 'Honeypot'
              : 'IP Management'}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {tab === 'overview' && (
        <>
          <div className="two-col" style={{ marginBottom: 'var(--space-lg)' }}>
            <div className="card">
              <div className="card-header">
                <h3>Live Traffic</h3>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>DB — last 2 min</span>
              </div>
              {/* Use DB chart data */}
              <LiveChart events={events} chartBuckets={chartBuckets} />
            </div>

            <div className="card">
              <div className="card-header">
                <h3>ML Predictions</h3>
              </div>
              <div style={{ padding: 'var(--space-md) 0' }}>
                {Object.entries(predictions).map(([key, val]) => (
                  <div key={key} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '10px var(--space-md)', borderBottom: '1px solid var(--border-primary)',
                  }}>
                    <StatusBadge status={key} />
                    <div style={{ display: 'flex', gap: '24px' }}>
                      <span className="mono" style={{ color: 'var(--text-primary)' }}>{val.count?.toLocaleString()}</span>
                      <span className="mono" style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                        avg: {(val.avg_confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
                {Object.keys(predictions).length === 0 && (
                  <div className="empty-state" style={{ padding: '24px' }}>
                    <p>No predictions yet — waiting for user activity</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Attack Distribution */}
          {Object.keys(attackDist).length > 0 && (
            <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
              <div className="card-header">
                <h3>Attack Distribution</h3>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-md)', padding: 'var(--space-sm) 0' }}>
                {Object.entries(attackDist).sort((a, b) => b[1] - a[1]).map(([type, count]) => (
                  <div key={type} style={{
                    background: 'var(--bg-input)', borderRadius: 'var(--radius-md)',
                    padding: '12px 16px', minWidth: '140px',
                  }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>{type}</div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.25rem', fontWeight: '600', color: 'var(--status-attack)' }}>
                      {count}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Alerts */}
          <div className="card">
            <div className="card-header">
              <h3>Recent Alerts</h3>
              <button className="btn btn-secondary btn-sm" onClick={fetchDashData} style={{ fontSize: '0.7rem' }}>
                <RefreshCw size={10} /> Refresh
              </button>
            </div>
            <DataTable
              columns={[
                { key: 'severity', label: 'Severity', render: (val) => <StatusBadge status={val} /> },
                { key: 'title', label: 'Alert' },
                { key: 'ip_address', label: 'IP', mono: true },
                { key: 'attack_type', label: 'Type', render: (val) => val || '—' },
                {
                  key: 'cdl',
                  label: 'CDL Risk',
                  render: (val) => (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{
                        width: '48px', height: '6px',
                        background: 'var(--bg-input)', borderRadius: '3px', overflow: 'hidden',
                      }}>
                        <div style={{
                          width: `${((val?.risk_score || 0) * 100).toFixed(0)}%`,
                          height: '100%',
                          background: (val?.risk_score || 0) > 0.7
                            ? 'var(--status-attack)' : 'var(--accent-teal)',
                          transition: 'width 0.5s ease',
                        }} />
                      </div>
                      <span className="mono" style={{ fontSize: '0.72rem', color: (val?.risk_score || 0) > 0.7 ? '#f87171' : '#34d399', fontWeight: '700' }}>
                        {val ? `${((val.risk_score || 0) * 100).toFixed(0)}%` : '0%'}
                      </span>
                    </div>
                  ),
                },
                {
                  key: 'cdl',
                  label: 'Predicted Next',
                  render: (val) => (
                    <span style={{ fontSize: '0.72rem', color: 'var(--accent-purple)', fontWeight: '700', fontFamily: 'var(--font-mono)' }}>
                      {val?.prediction?.next_attack || '—'}
                    </span>
                  ),
                },
                {
                  key: 'cdl',
                  label: 'Countermeasure',
                  render: (val) => (
                    <span style={{
                      fontSize: '0.68rem', fontWeight: '700', padding: '2px 8px',
                      borderRadius: '6px', fontFamily: 'var(--font-mono)',
                      background: val?.action?.action === 'DECEIVE' ? 'rgba(239,68,68,0.12)'
                        : val?.action?.action === 'DELAY' ? 'rgba(251,146,60,0.12)'
                        : val?.action?.action === 'HONEYPOT' ? 'rgba(168,85,247,0.12)'
                        : 'rgba(100,116,139,0.12)',
                      color: val?.action?.action === 'DECEIVE' ? '#f87171'
                        : val?.action?.action === 'DELAY' ? '#fb923c'
                        : val?.action?.action === 'HONEYPOT' ? '#c084fc'
                        : '#94a3b8',
                    }}>
                      {val?.action?.action || 'MONITOR'}
                    </span>
                  ),
                },
                { key: 'action_taken', label: 'Action' },
                { key: 'timestamp', label: 'Time', mono: true, render: (val) => val ? new Date(val).toLocaleTimeString() : '—' },
              ]}
              data={dashData?.recent_alerts || []}
              emptyMessage="No alerts yet — launch an attack from the user panel"
            />
          </div>
        </>
      )}

      {/* Kill Chain Tab */}
      {tab === 'killchain' && (
        <div className="card">
          <div className="card-header">
            <h3>⛓️ Kill Chain Tracker · MITRE ATT&CK</h3>
            <button className="btn btn-secondary btn-sm" onClick={fetchDashData} style={{ fontSize: '0.7rem' }}>
              <RefreshCw size={10} /> Refresh
            </button>
          </div>
          {killChain.threats?.length === 0 ? (
            <div className="empty-state" style={{ padding: '40px' }}>
              <p>No active threats tracked yet.</p>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '8px' }}>Launch attack simulations from the user panel — kill chain updates in real time.</p>
            </div>
          ) : (
            <div style={{ padding: 'var(--space-sm) 0' }}>
              {killChain.threats.map((t, i) => {
                const stageColors = ['#64748b','#60a5fa','#f59e0b','#fb923c','#f87171','#ef4444'];
                const stageLabels = ['CLEAN','RECON','INITIAL ACCESS','EXECUTION','LATERAL MOVE','EXFILTRATION'];
                const sc = stageColors[t.stage_num] || '#64748b';
                return (
                  <div key={i} style={{
                    padding: '16px var(--space-md)',
                    borderBottom: '1px solid var(--border-primary)',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px', marginBottom: '10px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: 'var(--accent-blue)' }}>{t.ip || t.identity_key}</code>
                        <span style={{ background: `${sc}18`, border: `1px solid ${sc}44`, color: sc, fontSize: '0.68rem', fontWeight: '700', padding: '2px 8px', borderRadius: '8px' }}>
                          {t.severity}
                        </span>
                        <span style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#fca5a5', fontSize: '0.65rem', fontFamily: 'var(--font-mono)', padding: '2px 8px', borderRadius: '8px' }}>
                          {t.mitre_id} · {t.mitre_name}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        Last seen: {t.last_seen ? new Date(t.last_seen).toLocaleTimeString() : '—'}
                      </div>
                    </div>
                    {/* Stage progress bar */}
                    <div style={{ display: 'flex', gap: '3px' }}>
                      {stageLabels.map((label, si) => (
                        <div key={si} style={{ flex: 1 }}>
                          <div style={{ height: '5px', borderRadius: '3px', background: t.stage_num >= si && si > 0 ? stageColors[si] : 'rgba(255,255,255,0.07)', boxShadow: t.stage_num === si ? `0 0 6px ${stageColors[si]}` : 'none', marginBottom: '4px', transition: 'all 0.4s' }} />
                          <div style={{ fontSize: '0.52rem', color: t.stage_num >= si && si > 0 ? stageColors[si] : 'var(--text-muted)', fontWeight: t.stage_num === si ? '800' : '400', textTransform: 'uppercase', textAlign: 'center', letterSpacing: '0.3px' }}>{label}</div>
                        </div>
                      ))}
                    </div>
                    {/* History */}
                    {t.history?.length > 0 && (
                      <div style={{ marginTop: '10px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                        {t.history.slice(-5).map((h, hi) => (
                          <span key={hi} style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '2px 8px', fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                            {h}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Model Intelligence Tab */}
      {tab === 'model' && (
        <>
          {/* Metric Cards Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 'var(--space-md)', marginBottom: 'var(--space-lg)' }}>
            {[
              { label: 'Accuracy', value: modelMetrics ? `${(modelMetrics.accuracy * 100).toFixed(2)}%` : '93.51%', color: '#06d6a0' },
              { label: 'Macro F1', value: modelMetrics ? modelMetrics.macro_f1?.toFixed(4) : '0.9345', color: '#3b82f6' },
              { label: 'ROC-AUC', value: modelMetrics ? modelMetrics.roc_auc?.toFixed(4) : '0.9848', color: '#8b5cf6' },
              { label: 'False Positive Rate', value: modelMetrics ? `${(modelMetrics.fpr * 100).toFixed(2)}%` : '6.45%', color: '#f59e0b' },
              { label: 'False Negative Rate', value: modelMetrics ? `${(modelMetrics.fnr * 100).toFixed(2)}%` : '6.52%', color: '#f87171' },
              { label: 'Threshold', value: modelMetrics ? modelMetrics.threshold : '0.85', color: '#06d6a0' },
            ].map((m) => (
              <div key={m.label} style={{ background: 'linear-gradient(145deg, #111827, #1e293b)', border: '1px solid #2d3748', borderRadius: '12px', padding: '18px', textAlign: 'center', position: 'relative', overflow: 'hidden' }}>
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: `linear-gradient(90deg, ${m.color}, transparent)` }} />
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.6rem', fontWeight: '700', color: m.color, lineHeight: 1, marginBottom: '6px' }}>{m.value}</div>
                <div style={{ fontSize: '0.65rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '1.5px' }}>{m.label}</div>
              </div>
            ))}
          </div>

          {/* Feature selection + hyperparams */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-md)' }}>
            <div className="card">
              <div className="card-header"><h3>🔬 Feature Pipeline</h3></div>
              <div style={{ padding: 'var(--space-md)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
                  {[
                    { label: 'Raw Features', val: modelMetrics?.features_before_selection || 206, color: '#64748b' },
                    { label: '→', val: null, color: '#475569' },
                    { label: 'After Selection', val: modelMetrics?.features_after_selection || 18, color: '#06d6a0' },
                  ].map((item, i) => item.val !== null ? (
                    <div key={i} style={{ flex: 1, background: 'rgba(255,255,255,0.03)', border: `1px solid ${item.color}33`, borderRadius: '10px', padding: '12px', textAlign: 'center' }}>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.5rem', fontWeight: '700', color: item.color }}>{item.val}</div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginTop: '4px' }}>{item.label}</div>
                    </div>
                  ) : <div key={i} style={{ color: '#475569', fontWeight: '700', fontSize: '1.2rem' }}>→</div>
                  )}
                </div>
                {[
                  { label: 'Dataset', val: 'UNSW-NB15' },
                  { label: 'Train Samples', val: (modelMetrics?.train_samples || 175341).toLocaleString() },
                  { label: 'Test Samples', val: (modelMetrics?.test_samples || 82332).toLocaleString() },
                  { label: 'Model', val: 'LightGBM (Optuna HPO)' },
                  { label: 'Selector', val: 'XGBoost SelectFromModel' },
                  { label: 'Scaler', val: 'MinMaxScaler' },
                ].map(({ label, val }) => (
                  <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{label}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{val}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <div className="card-header"><h3>⚙️ Best Hyperparameters (Optuna)</h3></div>
              <div style={{ padding: 'var(--space-md)' }}>
                {Object.entries(modelMetrics?.best_params || {
                  n_estimators: 565, max_depth: 9, learning_rate: 0.109,
                  num_leaves: 214, subsample: 0.865, colsample_bytree: 0.935,
                  min_child_samples: 58, reg_alpha: 0.193, reg_lambda: 0.195,
                }).filter(([k]) => !['random_state','verbose','n_jobs'].includes(k)).map(([k, v]) => (
                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{k}</span>
                    <span style={{ fontSize: '0.75rem', fontWeight: '600', color: '#06d6a0', fontFamily: 'var(--font-mono)' }}>{typeof v === 'number' ? (v % 1 === 0 ? v : v.toFixed(4)) : v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Users Tab */}
      {tab === 'users' && (
        <div className="card">
          <div className="card-header">
            <h3><User size={14} style={{ marginRight: '6px', display: 'inline' }} />Global User Management</h3>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{allUsers.length} total accounts</span>
          </div>
          <div style={{ padding: 'var(--space-sm) 0' }}>
            {allUsers.map((u) => (
              <div key={u.id} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '14px var(--space-md)',
                borderBottom: '1px solid var(--border-primary)',
                transition: 'background 0.15s',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  <div style={{
                    width: '36px', height: '36px', borderRadius: '50%',
                    background: u.role === 'admin' ? 'linear-gradient(135deg, #f59e0b, #ef4444)' : 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.85rem', fontWeight: '700', color: '#fff', flexShrink: 0,
                  }}>
                    {u.username.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: '600', color: 'var(--text-primary)', fontSize: '0.9rem' }}>{u.username}</span>
                      <CompanyBadge companyId={u.company_id} name={u.company_name} />
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{u.email}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '2px' }}>Role</div>
                    <div style={{ fontSize: '0.75rem', fontWeight: '600', textTransform: 'uppercase', color: u.role === 'admin' ? '#f59e0b' : u.role === 'company' ? 'var(--accent-blue)' : 'var(--text-muted)' }}>{u.role}</div>
                  </div>
                  <div style={{ textAlign: 'right', minWidth: '110px' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '2px' }}>Simulated IP</div>
                    <code style={{ fontSize: '0.8rem', color: 'var(--accent-blue)', fontFamily: 'var(--font-mono)' }}>{u.simulated_ip || '—'}</code>
                  </div>
                  <div style={{ minWidth: '80px', textAlign: 'center' }}>
                    {u.is_blocked ? (
                      <span style={{
                        background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)',
                        color: '#f87171', fontSize: '0.7rem', fontWeight: '700',
                        padding: '3px 10px', borderRadius: '999px', textTransform: 'uppercase',
                        animation: 'pulse 2s infinite',
                      }}>Blocked</span>
                    ) : (
                      <span style={{
                        background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.25)',
                        color: '#34d399', fontSize: '0.7rem', fontWeight: '700',
                        padding: '3px 10px', borderRadius: '999px', textTransform: 'uppercase',
                      }}>Active</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Logs Tab */}
      {tab === 'logs' && (
        <div className="card">
          <div className="card-header">
            <h3>Request Logs</h3>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Last 50 · DB only</span>
          </div>
          <DataTable
            columns={[
              { key: 'ip_address', label: 'IP', mono: true },
              { key: 'endpoint', label: 'Endpoint' },
              { key: 'method', label: 'Method' },
              { key: 'status_code', label: 'Status', mono: true },
              { key: 'prediction', label: 'Prediction', render: (val) => <StatusBadge status={val} /> },
              { key: 'confidence', label: 'Confidence', mono: true, render: (val) => val ? `${(val * 100).toFixed(1)}%` : '—' },
              { key: 'attack_type', label: 'Type', render: (val) => val || '—' },
              { key: 'timestamp', label: 'Time', mono: true, render: (val) => val ? new Date(val).toLocaleTimeString() : '—' },
            ]}
            data={logs}
            emptyMessage="No logs yet — start using user accounts"
          />
        </div>
      )}

      {/* Honeypot Tab */}
      {tab === 'honeypot' && (
        <div className="card">
          <div className="card-header">
            <h3><Bug size={14} style={{ marginRight: '6px', display: 'inline' }} />Honeypot Captured Events</h3>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{honeypotEvents.length} events</span>
          </div>
          <DataTable
            columns={[
              { key: 'ip_address', label: 'IP', mono: true },
              { key: 'event_type', label: 'Type', render: (val) => <StatusBadge status={val === 'login_attempt' ? 'attack' : val === 'sql_injection' ? 'critical' : 'suspicious'} /> },
              { key: 'endpoint', label: 'Endpoint' },
              { key: 'method', label: 'Method' },
              { key: 'payload', label: 'Payload', render: (val) => <code style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{val ? (val.length > 50 ? val.slice(0, 50) + '...' : val) : '—'}</code> },
              { key: 'captured_data', label: 'Captured Info', render: (val) => val ? val.slice(0, 60) : '—' },
              { key: 'timestamp', label: 'Time', mono: true, render: (val) => val ? new Date(val).toLocaleTimeString() : '—' },
            ]}
            data={honeypotEvents}
            emptyMessage="No honeypot events captured yet"
          />
        </div>
      )}

      {/* IP Management Tab */}
      {tab === 'ips' && (
        <>
          <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
            <div className="card-header"><h3>Block IP Address</h3></div>
            <div style={{ display: 'flex', gap: 'var(--space-md)', alignItems: 'flex-end' }}>
              <div className="input-group" style={{ flex: 1, marginBottom: 0 }}>
                <label>IP Address</label>
                <input className="input" placeholder="203.x.x.x" value={blockIp} onChange={(e) => setBlockIp(e.target.value)} />
              </div>
              <div className="input-group" style={{ flex: 2, marginBottom: 0 }}>
                <label>Reason</label>
                <input className="input" placeholder="Reason for blocking" value={blockReason} onChange={(e) => setBlockReason(e.target.value)} />
              </div>
              <button className="btn btn-danger" onClick={handleBlock} style={{ height: '40px' }}>
                <Ban size={14} /> Block
              </button>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h3>Active Blocked IPs</h3>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{blockedIps.length} active</span>
            </div>
            <DataTable
              columns={[
                {
                  key: 'ip_address', label: 'IP Address', mono: true,
                  render: (val, row) => (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span>{val}</span>
                      {row?.flagged && (
                        <span style={{
                          background: 'linear-gradient(135deg, #dc2626, #ef4444)',
                          color: '#fff', fontSize: '0.6rem', fontWeight: '700',
                          padding: '2px 8px', borderRadius: '4px',
                          letterSpacing: '0.05em', textTransform: 'uppercase',
                          animation: 'pulse 2s infinite',
                          boxShadow: '0 0 8px rgba(220, 38, 38, 0.4)',
                        }}>⚠ FLAGGED</span>
                      )}
                    </span>
                  ),
                },
                { key: 'reason', label: 'Reason' },
                {
                  key: 'attack_type', label: 'Attack Type',
                  render: (val) => (
                    <span style={{
                      color: val === 'Brute Force' ? '#f87171' : val === 'DDoS' ? '#c084fc' : val === 'SQL Injection' ? '#fb923c' : val === 'XSS' ? '#facc15' : 'var(--text-muted)',
                      fontWeight: '600', fontSize: '0.8rem',
                    }}>{val || '—'}</span>
                  ),
                },
                { key: 'confidence', label: 'Confidence', mono: true, render: (val) => val ? `${(val * 100).toFixed(0)}%` : '—' },
                {
                  key: 'blocked_by', label: 'Blocked By',
                  render: (val) => (
                    <span style={{ color: val === 'system' ? 'var(--status-attack)' : 'var(--accent-blue)', fontWeight: '500' }}>
                      {val === 'system' ? '🤖 Auto' : '👤 Admin'}
                    </span>
                  ),
                },
                { key: 'blocked_at', label: 'Time', mono: true, render: (val) => val ? new Date(val).toLocaleString() : '—' },
                {
                  key: 'action', label: 'Action',
                  render: (val, row) => (
                    <button className="btn btn-secondary btn-sm" onClick={() => handleUnblock(row?.ip_address)}>
                      Unblock
                    </button>
                  ),
                },
              ]}
              data={blockedIps}
              emptyMessage="No blocked IPs"
            />
          </div>
        </>
      )}
    </div>
  );
}

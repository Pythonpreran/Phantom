/**
 * PHANTOM — Company Dashboard
 * Shows only THIS company's data: users, logs, threats, blocked IPs.
 */

import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAuth } from '../hooks/useAuth';
import { api } from '../utils/api';
import MetricCard from '../components/MetricCard';
import LiveChart from '../components/LiveChart';
import StatusBadge from '../components/StatusBadge';
import DataTable from '../components/DataTable';
import {
  Activity, Shield, Ban, Users, Zap, AlertTriangle,
  RefreshCw, Wifi, User, Clock,
} from 'lucide-react';

const COMPANY_COLORS = {
  abc: { bg: 'rgba(16,185,129,0.15)', border: 'rgba(16,185,129,0.35)', text: '#34d399', label: 'ABC Corp' },
  xyz: { bg: 'rgba(99,102,241,0.15)', border: 'rgba(99,102,241,0.35)', text: '#818cf8', label: 'XYZ Corp' },
};

function CompanyBadge({ companyId, name }) {
  const c = COMPANY_COLORS[companyId] || { bg: 'rgba(148,163,184,0.1)', border: 'rgba(148,163,184,0.25)', text: '#94a3b8', label: name || companyId };
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

export default function CompanyDashboard() {
  const { events, connected } = useWebSocket();
  const { user } = useAuth();
  const [tab, setTab] = useState('overview');
  const [dash, setDash] = useState(null);
  const [users, setUsers] = useState([]);
  const [logs, setLogs] = useState([]);
  const [threats, setThreats] = useState([]);
  const [blocked, setBlocked] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [lastRefresh, setLastRefresh] = useState(null);

  const safe = async (fn) => { try { return await fn(); } catch { return null; } };

  const fetchAll = useCallback(async () => {
    const [d, u, l, t, b, a] = await Promise.all([
      safe(() => api('/api/company/dashboard', {}, true)),
      safe(() => api('/api/company/users', {}, true)),
      safe(() => api('/api/company/logs', {}, true)),
      safe(() => api('/api/company/threats', {}, true)),
      safe(() => api('/api/company/blocked', {}, true)),
      safe(() => api('/api/company/alerts', {}, true)),
    ]);
    if (d) setDash(d);
    if (u) setUsers(u.users || []);
    if (l) setLogs(l.logs || []);
    if (t) setThreats(t.threats || []);
    if (b) setBlocked(b.blocked_ips || []);
    if (a) setAlerts(a.alerts || []);
    setLastRefresh(new Date());
  }, []);

  useEffect(() => {
    fetchAll();
    const iv = setInterval(fetchAll, 8000);
    return () => clearInterval(iv);
  }, [fetchAll]);

  useEffect(() => {
    if (events.length > 0) fetchAll();
  }, [events.length]);

  const companyName = dash?.company_name || user?.company_name || 'Company';
  const companyId = user?.company_id;

  return (
    <div>
      {/* Header */}
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                <h1 style={{ margin: 0 }}>{companyName}</h1>
                <CompanyBadge companyId={companyId} name={companyName} />
              </div>
              <p style={{ margin: 0 }}>Security Dashboard — Protected by PHANTOM</p>
            </div>
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

      {/* Metrics */}
      <div className="metrics-grid">
        <MetricCard icon={<Activity size={20} />} value={dash?.total_requests ?? 0} label="Total Requests" color="var(--accent-blue)" />
        <MetricCard icon={<Users size={20} />} value={dash?.total_users ?? users.length} label="Company Users" color="var(--accent-teal)" />
        <MetricCard icon={<Shield size={20} />} value={dash?.total_attacks ?? 0} label="Threats Detected" color="var(--status-attack)" />
        <MetricCard icon={<Ban size={20} />} value={dash?.blocked_ips ?? 0} label="IPs Blocked" color="var(--accent-purple)" />
        <MetricCard icon={<Zap size={20} />} value={dash?.last_hour_requests ?? 0} label="Last Hour" color="var(--status-suspicious)" />
      </div>

      {/* Tabs */}
      <div className="tabs">
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'users', label: `Users (${users.length})` },
          { id: 'logs', label: 'IP Logs' },
          { id: 'threats', label: `Threats (${threats.length})` },
          { id: 'blocked', label: `Blocked IPs (${blocked.length})` },
        ].map((t) => (
          <button key={t.id} className={`tab ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Overview */}
      {tab === 'overview' && (
        <>
          <div className="two-col" style={{ marginBottom: 'var(--space-lg)' }}>
            <div className="card">
              <div className="card-header">
                <h3>Live Traffic</h3>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Real-time · 2 min window</span>
              </div>
              <LiveChart events={events} />
            </div>
            <div className="card">
              <div className="card-header">
                <h3>Live Event Feed</h3>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{events.length} events</span>
              </div>
              <div className="event-feed">
                {events.slice(0, 30).map((e, i) => (
                  <div className="event-item" key={`${e.id}-${i}`}>
                    <span className="event-time">{e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : '—'}</span>
                    <span className="event-ip">{e.ip_address}</span>
                    <span className="event-endpoint">{e.endpoint}</span>
                    <StatusBadge status={e.prediction} />
                  </div>
                ))}
                {events.length === 0 && (
                  <div className="empty-state" style={{ padding: '32px' }}>
                    <p>Waiting for events...</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Alerts */}
          <div className="card">
            <div className="card-header">
              <h3><AlertTriangle size={14} style={{ marginRight: '6px', display: 'inline' }} />Recent Alerts</h3>
              <button className="btn btn-secondary btn-sm" onClick={fetchAll} style={{ fontSize: '0.7rem' }}>
                <RefreshCw size={10} /> Refresh
              </button>
            </div>
            <DataTable
              columns={[
                { key: 'severity', label: 'Severity', render: (val) => <StatusBadge status={val} /> },
                { key: 'title', label: 'Alert' },
                { key: 'ip_address', label: 'IP', mono: true },
                { key: 'attack_type', label: 'Type', render: (val) => val || '—' },
                { key: 'action_taken', label: 'Action' },
                { key: 'timestamp', label: 'Time', mono: true, render: (val) => val ? new Date(val).toLocaleTimeString() : '—' },
              ]}
              data={alerts.slice(0, 20)}
              emptyMessage="No alerts for your company yet"
            />
          </div>
        </>
      )}

      {/* Users Tab */}
      {tab === 'users' && (
        <div className="card">
          <div className="card-header">
            <h3><User size={14} style={{ marginRight: '6px', display: 'inline' }} />Company Users</h3>
            <CompanyBadge companyId={companyId} name={companyName} />
          </div>
          <div style={{ padding: 'var(--space-sm) 0' }}>
            {users.length === 0 && (
              <div className="empty-state" style={{ padding: '40px' }}>
                <p>No users found for {companyName}</p>
              </div>
            )}
            {users.map((u) => (
              <div key={u.id} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '14px var(--space-md)',
                borderBottom: '1px solid var(--border-primary)',
                transition: 'background 0.15s',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  <div style={{
                    width: '36px', height: '36px', borderRadius: '50%',
                    background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.85rem', fontWeight: '700', color: '#fff', flexShrink: 0,
                  }}>
                    {u.username.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                  </div>
                  <div>
                    <div style={{ fontWeight: '600', color: 'var(--text-primary)', fontSize: '0.9rem' }}>{u.username}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{u.email}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '2px' }}>Simulated IP</div>
                    <code style={{ fontSize: '0.8rem', color: 'var(--accent-blue)', fontFamily: 'var(--font-mono)' }}>{u.simulated_ip || '—'}</code>
                  </div>
                  <div>
                    {u.is_blocked ? (
                      <span style={{
                        background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)',
                        color: '#f87171', fontSize: '0.7rem', fontWeight: '700',
                        padding: '3px 10px', borderRadius: '999px', textTransform: 'uppercase',
                      }}>🔴 Blocked</span>
                    ) : (
                      <span style={{
                        background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.25)',
                        color: '#34d399', fontSize: '0.7rem', fontWeight: '700',
                        padding: '3px 10px', borderRadius: '999px', textTransform: 'uppercase',
                      }}>🟢 Active</span>
                    )}
                  </div>
                  {u.created_at && (
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={10} />
                      {new Date(u.created_at).toLocaleDateString()}
                    </div>
                  )}
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
            <h3>IP Request Logs</h3>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Last 100 · {companyName} only</span>
          </div>
          <DataTable
            columns={[
              { key: 'ip_address', label: 'IP Address', mono: true },
              { key: 'endpoint', label: 'Endpoint' },
              { key: 'method', label: 'Method' },
              { key: 'status_code', label: 'Status', mono: true },
              { key: 'prediction', label: 'Prediction', render: (val) => <StatusBadge status={val} /> },
              { key: 'confidence', label: 'Confidence', mono: true, render: (val) => val ? `${(val * 100).toFixed(1)}%` : '—' },
              { key: 'attack_type', label: 'Type', render: (val) => val || '—' },
              { key: 'timestamp', label: 'Time', mono: true, render: (val) => val ? new Date(val).toLocaleTimeString() : '—' },
            ]}
            data={logs}
            emptyMessage={`No logs for ${companyName} yet`}
          />
        </div>
      )}

      {/* Threats Tab */}
      {tab === 'threats' && (
        <div className="card">
          <div className="card-header">
            <h3><Shield size={14} style={{ marginRight: '6px', display: 'inline' }} />Threats Detected</h3>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{threats.length} events · {companyName}</span>
          </div>
          <DataTable
            columns={[
              { key: 'ip_address', label: 'IP Address', mono: true },
              { key: 'endpoint', label: 'Endpoint' },
              { key: 'method', label: 'Method' },
              { key: 'prediction', label: 'Status', render: (val) => <StatusBadge status={val} /> },
              { key: 'confidence', label: 'Confidence', mono: true, render: (val) => val ? `${(val * 100).toFixed(1)}%` : '—' },
              { key: 'attack_type', label: 'Type', render: (val) => val || '—' },
              { key: 'timestamp', label: 'Time', mono: true, render: (val) => val ? new Date(val).toLocaleTimeString() : '—' },
            ]}
            data={threats.slice(0, 50)}
            emptyMessage="No threats detected for your company yet"
          />
        </div>
      )}

      {/* Blocked IPs Tab */}
      {tab === 'blocked' && (
        <div className="card">
          <div className="card-header">
            <h3><Ban size={14} style={{ marginRight: '6px', display: 'inline' }} />Blocked IPs</h3>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{blocked.length} active · {companyName}</span>
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
                        background: 'linear-gradient(135deg,#dc2626,#ef4444)', color: '#fff',
                        fontSize: '0.6rem', fontWeight: '700', padding: '2px 8px',
                        borderRadius: '4px', letterSpacing: '0.05em', textTransform: 'uppercase',
                        boxShadow: '0 0 8px rgba(220,38,38,0.4)',
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
                    color: val === 'Brute Force' ? '#f87171' : val === 'DDoS' ? '#c084fc'
                      : val === 'SQL Injection' ? '#fb923c' : '#60a5fa',
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
              { key: 'blocked_at', label: 'Time', mono: true, render: (val) => val ? new Date(val).toLocaleTimeString() : '—' },
            ]}
            data={blocked}
            emptyMessage="No blocked IPs for your company"
          />
        </div>
      )}
    </div>
  );
}

/**
 * PHANTOM — Validation Lab
 */

import { useState, useEffect } from 'react';
import { api } from '../utils/api';
import StatusBadge from '../components/StatusBadge';
import { FlaskConical, Play, CheckCircle, XCircle, Clock, Shield } from 'lucide-react';

export default function ValidationLab() {
  const [selectedTest, setSelectedTest] = useState(null);
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState(null);
  const [history, setHistory] = useState([]);
  const [pollId, setPollId] = useState(null);

  useEffect(() => {
    api('/api/validation/history', {}, true).then((d) => setHistory(d.tests || [])).catch(() => {});
  }, []);

  // Poll for results
  useEffect(() => {
    if (!pollId) return;
    const interval = setInterval(async () => {
      try {
        const data = await api(`/api/validation/results/${pollId}`, {}, true);
        if (data.status === 'completed') {
          setResults(data);
          setRunning(false);
          setPollId(null);
          api('/api/validation/history', {}, true).then((d) => setHistory(d.tests || [])).catch(() => {});
        }
      } catch (e) { /* ignore */ }
    }, 1000);
    return () => clearInterval(interval);
  }, [pollId]);

  const startTest = async (testType) => {
    setSelectedTest(testType);
    setRunning(true);
    setResults(null);
    try {
      const data = await api('/api/validation/start', {
        method: 'POST',
        body: JSON.stringify({ test_type: testType }),
      }, true);
      setPollId(data.test_id);
    } catch (err) {
      setRunning(false);
    }
  };

  const tests = [
    {
      id: 'brute_force',
      label: 'Brute Force',
      desc: 'Simulate 20 rapid login attempts with various credentials',
      icon: <Shield size={20} />,
    },
    {
      id: 'sql_injection',
      label: 'SQL Injection',
      desc: 'Send 15 SQL injection payloads to test input validation',
      icon: <FlaskConical size={20} />,
    },
    {
      id: 'ddos',
      label: 'DDoS Attack',
      desc: 'Simulate 30 high-volume requests to test rate limiting',
      icon: <Play size={20} />,
    },
  ];

  return (
    <div>
      <div className="page-header">
        <h1>Validation Lab</h1>
        <p>Test PHANTOM's detection capabilities against simulated attacks</p>
      </div>

      {/* Test Selection */}
      <div className="test-controls">
        {tests.map((t) => (
          <div
            key={t.id}
            className={`test-card ${selectedTest === t.id ? 'active' : ''}`}
            onClick={() => !running && startTest(t.id)}
            style={{ opacity: running ? 0.6 : 1, cursor: running ? 'not-allowed' : 'pointer' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--accent-blue)' }}>
              {t.icon}
              <h4>{t.label}</h4>
            </div>
            <p>{t.desc}</p>
            {!running && (
              <button className="btn btn-primary btn-sm" style={{ marginTop: '12px' }}>
                <Play size={12} /> Run Test
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Running indicator */}
      {running && (
        <div className="card" style={{ textAlign: 'center', padding: '48px', marginBottom: 'var(--space-lg)' }}>
          <div className="spinner" style={{ margin: '0 auto 16px', width: '32px', height: '32px' }} />
          <h3 style={{ color: 'var(--text-primary)', marginBottom: '4px' }}>
            Running {selectedTest?.replace('_', ' ')} test...
          </h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            PHANTOM is analyzing incoming attack patterns
          </p>
        </div>
      )}

      {/* Results */}
      {results && (
        <div style={{ marginBottom: 'var(--space-lg)' }}>
          {/* Summary metrics */}
          <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
            <div className="metric-card">
              <div className="metric-content">
                <div className="metric-value" style={{ color: 'var(--accent-blue)' }}>{results.total_requests}</div>
                <div className="metric-label">Total Attacks Sent</div>
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-content">
                <div className="metric-value" style={{ color: 'var(--status-normal)' }}>{results.detection_rate}%</div>
                <div className="metric-label">Detection Rate</div>
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-content">
                <div className="metric-value" style={{ color: 'var(--status-attack)' }}>{results.blocked_count}</div>
                <div className="metric-label">Blocked</div>
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-content">
                <div className="metric-value" style={{ color: 'var(--accent-teal)' }}>{results.avg_detection_time_ms}ms</div>
                <div className="metric-label">Avg Detection Time</div>
              </div>
            </div>
          </div>

          {/* Timeline */}
          <div className="card">
            <div className="card-header">
              <h3>Attack Timeline</h3>
              <StatusBadge status={results.detection_rate >= 80 ? 'normal' : results.detection_rate >= 50 ? 'suspicious' : 'attack'} />
            </div>
            <div className="test-timeline">
              {results.results?.map((r, i) => (
                <div key={i} className={`timeline-item ${r.prediction === 'attack' ? 'attack' : r.action === 'blocked' ? 'blocked' : ''}`}>
                  <div className="timeline-time">
                    Attempt #{r.attempt} — {r.detection_time_ms}ms
                  </div>
                  <div className="timeline-content" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {r.prediction === 'attack' ? (
                      <XCircle size={14} color="var(--status-attack)" />
                    ) : r.prediction === 'suspicious' ? (
                      <Clock size={14} color="var(--status-suspicious)" />
                    ) : (
                      <CheckCircle size={14} color="var(--status-normal)" />
                    )}
                    <span>
                      {r.prediction === 'attack' ? 'Detected & ' : ''}
                      {r.action === 'blocked' ? 'Blocked' : r.action === 'monitored' ? 'Monitored' : 'Allowed'}
                    </span>
                    <StatusBadge status={r.prediction} />
                    <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {(r.confidence * 100).toFixed(1)}%
                    </span>
                    {r.payload && (
                      <code style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginLeft: '8px' }}>
                        {r.payload.length > 40 ? r.payload.slice(0, 40) + '...' : r.payload}
                      </code>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3>Test History</h3>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Status</th>
                <th>Requests</th>
                <th>Detected</th>
                <th>Blocked</th>
                <th>Detection Rate</th>
                <th>Avg Time</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {history.map((t) => (
                <tr key={t.id}>
                  <td>{t.test_type?.replace('_', ' ')}</td>
                  <td><StatusBadge status={t.status === 'completed' ? 'normal' : 'suspicious'} /></td>
                  <td className="mono">{t.total_requests}</td>
                  <td className="mono">{t.detected_count}</td>
                  <td className="mono">{t.blocked_count}</td>
                  <td className="mono" style={{ color: t.detection_rate >= 80 ? 'var(--status-normal)' : 'var(--status-attack)' }}>
                    {t.detection_rate}%
                  </td>
                  <td className="mono">{t.avg_detection_time_ms}ms</td>
                  <td className="mono" style={{ fontSize: '0.75rem' }}>
                    {t.started_at ? new Date(t.started_at).toLocaleString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

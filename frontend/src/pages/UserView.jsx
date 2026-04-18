/**
 * PHANTOM — User View
 * XYZ website interface with attack simulation panel for demo.
 * Shows: assigned IP, block status, normal actions, attack buttons.
 */

import { useState, useEffect, useRef } from 'react';
import { api } from '../utils/api';
import {
  Globe, Send, Database, AlertTriangle, Wifi,
  ShieldAlert, ShieldCheck, Zap, Activity
} from 'lucide-react';

const ATTACK_TYPES = [
  {
    id: 'DDoS',
    label: 'DDoS Attack',
    icon: '🌩️',
    desc: 'Flood the server with massive traffic',
    color: '#c084fc',
    hoverColor: 'rgba(192,132,252,0.15)',
    border: 'rgba(192,132,252,0.3)',
  },
  {
    id: 'SQL Injection',
    label: 'SQL Injection',
    icon: '💉',
    desc: "Inject malicious SQL into the database",
    color: '#fb923c',
    hoverColor: 'rgba(251,146,60,0.15)',
    border: 'rgba(251,146,60,0.3)',
  },
  {
    id: 'XSS',
    label: 'XSS Attack',
    icon: '🕷️',
    desc: 'Cross-site scripting exploit attempt',
    color: '#facc15',
    hoverColor: 'rgba(250,204,21,0.15)',
    border: 'rgba(250,204,21,0.3)',
  },
  {
    id: 'Brute Force',
    label: 'Brute Force',
    icon: '🔨',
    desc: 'Attempt thousands of password guesses',
    color: '#f87171',
    hoverColor: 'rgba(248,113,113,0.15)',
    border: 'rgba(248,113,113,0.3)',
  },
  {
    id: 'Port Scan',
    label: 'Port Scan',
    icon: '🔍',
    desc: 'Probe all open ports for vulnerabilities',
    color: '#60a5fa',
    hoverColor: 'rgba(96,165,250,0.15)',
    border: 'rgba(96,165,250,0.3)',
  },
];

// ── Kill chain stage metadata ─────────────────────────────────────────────────
const KC_STAGES = [
  { num: 0, label: 'CLEAN',           color: '#64748b' },
  { num: 1, label: 'RECON',           color: '#60a5fa' },
  { num: 2, label: 'INITIAL ACCESS',  color: '#f59e0b' },
  { num: 3, label: 'EXECUTION',       color: '#fb923c' },
  { num: 4, label: 'LATERAL MOVE',    color: '#f87171' },
  { num: 5, label: 'EXFILTRATION',    color: '#ef4444' },
];

function AttackIntelPanel({ lastAttack }) {
  const [showPlaybook, setShowPlaybook] = useState(false);
  const d = lastAttack?.data || {};
  const kc = d.kill_chain || {};
  const features = d.top_features || [];
  const pb = d.playbook || {};
  const stageNum = kc.stage_num ?? 0;

  const severityColor = {
    CRITICAL: '#ef4444', HIGH: '#f87171',
    MEDIUM: '#f59e0b',   LOW: '#64748b',
  }[kc.severity] || '#64748b';

  return (
    <div style={{
      margin: 'var(--space-md) var(--space-md) 0',
      background: 'rgba(239,68,68,0.06)',
      border: '1px solid rgba(239,68,68,0.25)',
      borderRadius: 'var(--radius-md)',
      overflow: 'hidden',
    }}>
      {/* ── Header ────────────────────────────────────────── */}
      <div style={{
        padding: '12px 16px',
        borderBottom: '1px solid rgba(239,68,68,0.15)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px',
      }}>
        <div style={{ fontWeight: '700', color: '#f87171', fontSize: '0.85rem' }}>
          🚨 {lastAttack.time} — {lastAttack.type}
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {d.confidence !== undefined && (
            <span style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)', padding: '2px 10px', borderRadius: '12px', fontSize: '0.71rem', fontWeight: '700', color: '#f87171' }}>
              {(d.confidence * 100).toFixed(1)}% confidence
            </span>
          )}
          {d.ml_prediction && (
            <span style={{ background: 'rgba(168,85,247,0.12)', border: '1px solid rgba(168,85,247,0.3)', padding: '2px 10px', borderRadius: '12px', fontSize: '0.71rem', fontWeight: '600', color: '#a855f7' }}>
              {d.ml_prediction}
            </span>
          )}
          {d.model_used && (
            <span style={{ background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.3)', padding: '2px 10px', borderRadius: '12px', fontSize: '0.71rem', fontWeight: '600', color: '#60a5fa' }}>
              🧠 {d.model_used}
            </span>
          )}
          {kc.severity && (
            <span style={{ background: `${severityColor}18`, border: `1px solid ${severityColor}44`, padding: '2px 10px', borderRadius: '12px', fontSize: '0.71rem', fontWeight: '700', color: severityColor }}>
              {kc.severity}
            </span>
          )}
        </div>
      </div>

      <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>

        {/* ── Kill Chain Progress ───────────────────────────── */}
        {kc.stage !== undefined && (
          <div>
            <div style={{ fontSize: '0.7rem', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>⛓️ Kill Chain · MITRE ATT&CK</span>
              {kc.mitre_id && (
                <span style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', padding: '2px 8px', borderRadius: '8px', color: '#fca5a5', fontFamily: 'var(--font-mono)', fontSize: '0.68rem' }}>
                  {kc.mitre_id} · {kc.mitre_name}
                </span>
              )}
            </div>
            <div style={{ display: 'flex', gap: '3px', alignItems: 'center' }}>
              {KC_STAGES.map((s, i) => {
                const active = stageNum >= s.num && s.num > 0;
                const current = stageNum === s.num;
                return (
                  <div key={s.num} style={{ flex: 1, textAlign: 'center' }}>
                    <div style={{
                      height: '6px',
                      borderRadius: '3px',
                      background: active ? s.color : 'rgba(255,255,255,0.08)',
                      boxShadow: current ? `0 0 8px ${s.color}` : 'none',
                      marginBottom: '5px',
                      transition: 'all 0.5s ease',
                    }} />
                    <div style={{
                      fontSize: '0.56rem',
                      color: active ? s.color : 'var(--text-muted)',
                      fontWeight: current ? '800' : '500',
                      textTransform: 'uppercase',
                      letterSpacing: '0.3px',
                      whiteSpace: 'nowrap',
                    }}>
                      {s.label}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── Feature Attribution ───────────────────────────── */}
        {features.length > 0 && (
          <div>
            <div style={{ fontSize: '0.7rem', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '10px' }}>
              🔬 Why Flagged · Top Feature Signals
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '7px' }}>
              {features.map(([name, pct], i) => {
                const barColors = ['#ef4444', '#f87171', '#fb923c', '#f59e0b', '#60a5fa'];
                return (
                  <div key={name} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ width: '110px', fontSize: '0.72rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', flexShrink: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {name}
                    </div>
                    <div style={{ flex: 1, height: '7px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{
                        width: `${(pct * 100).toFixed(1)}%`,
                        height: '100%',
                        background: barColors[i],
                        borderRadius: '4px',
                        transition: 'width 0.8s ease',
                      }} />
                    </div>
                    <div style={{ width: '38px', fontSize: '0.7rem', color: barColors[i], fontWeight: '700', textAlign: 'right' }}>
                      {(pct * 100).toFixed(1)}%
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── SOC Playbook ──────────────────────────────────── */}
        {pb.steps && (
          <div>
            <button
              onClick={() => setShowPlaybook(v => !v)}
              style={{
                display: 'flex', alignItems: 'center', gap: '8px',
                background: 'rgba(251,146,60,0.08)', border: '1px solid rgba(251,146,60,0.2)',
                borderRadius: '8px', padding: '7px 12px', cursor: 'pointer',
                color: '#fb923c', fontSize: '0.72rem', fontWeight: '700',
                width: '100%', textAlign: 'left',
                transition: 'all 0.2s',
              }}
            >
              <span>📋</span>
              <span>SOC Analyst Playbook</span>
              <span style={{ marginLeft: 'auto', opacity: 0.6 }}>{showPlaybook ? '▲' : '▼'}</span>
            </button>

            {showPlaybook && (
              <div style={{
                marginTop: '10px',
                background: 'rgba(15,23,42,0.6)',
                border: '1px solid rgba(251,146,60,0.15)',
                borderRadius: '8px',
                padding: '14px',
                fontSize: '0.78rem',
                lineHeight: '1.6',
              }}>
                <div style={{ color: '#fed7aa', fontWeight: '700', marginBottom: '8px', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                  ⚠️ Why Flagged
                </div>
                <div style={{ color: 'var(--text-secondary)', marginBottom: '14px', borderLeft: '2px solid rgba(251,146,60,0.3)', paddingLeft: '10px' }}>
                  {pb.why}
                </div>

                <div style={{ color: '#fed7aa', fontWeight: '700', marginBottom: '8px', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                  📋 Remediation Steps
                </div>
                <ol style={{ margin: '0 0 14px 0', paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {pb.steps?.map((step, i) => (
                    <li key={i} style={{ color: 'var(--text-secondary)' }}>
                      {step}
                    </li>
                  ))}
                </ol>

                <div style={{ color: '#fed7aa', fontWeight: '700', marginBottom: '6px', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                  🔍 False Positive Check
                </div>
                <div style={{ color: 'var(--text-muted)', borderLeft: '2px solid rgba(251,146,60,0.2)', paddingLeft: '10px', marginBottom: '12px' }}>
                  {pb.fp_check}
                </div>

                {pb.mitre && (
                  <div style={{
                    display: 'inline-flex', alignItems: 'center', gap: '6px',
                    background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
                    padding: '4px 10px', borderRadius: '8px',
                    fontSize: '0.68rem', color: '#fca5a5', fontFamily: 'var(--font-mono)',
                  }}>
                    🎯 {pb.mitre}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Terminal Log Component ────────────────────────────────────────────────────
function TerminalLog({ lines, isRunning }) {
  const bottomRef = useRef(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [lines]);

  if (lines.length === 0 && !isRunning) return null;

  return (
    <div style={{
      margin: '16px var(--space-md) 0',
      background: '#000d1a',
      border: '1px solid rgba(0,255,180,0.2)',
      borderRadius: 'var(--radius-md)',
      overflow: 'hidden',
      boxShadow: '0 0 20px rgba(0,255,180,0.06), inset 0 0 40px rgba(0,0,0,0.5)',
    }}>
      {/* Terminal title bar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '8px',
        padding: '8px 14px',
        background: 'rgba(0,20,40,0.9)',
        borderBottom: '1px solid rgba(0,255,180,0.12)',
      }}>
        <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#ff5f57' }} />
        <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#ffbd2e' }} />
        <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#28c840' }} />
        <span style={{
          marginLeft: '8px', fontSize: '0.7rem', fontFamily: 'var(--font-mono)',
          color: 'rgba(0,255,180,0.5)', letterSpacing: '0.1em',
        }}>phantom@defense-engine ~ ATTACK MONITOR</span>
        {isRunning && (
          <span style={{
            marginLeft: 'auto', fontSize: '0.65rem', color: '#f87171',
            fontFamily: 'var(--font-mono)', animation: 'phantom-blink 1s infinite',
          }}>● LIVE</span>
        )}
      </div>

      {/* Log lines */}
      <div style={{
        padding: '12px 14px',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.73rem',
        lineHeight: '1.8',
        maxHeight: '320px',
        overflowY: 'auto',
        scrollbarWidth: 'thin',
        scrollbarColor: 'rgba(0,255,180,0.15) transparent',
      }}>
        {lines.map((line, i) => (
          <div key={i} style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
            <span style={{ color: 'rgba(0,255,180,0.3)', flexShrink: 0 }}>{line.ts}</span>
            <span style={{ color: line.color || '#9ab0cc', flex: 1, wordBreak: 'break-word' }}>
              {line.prefix && (
                <span style={{ color: line.prefixColor, fontWeight: '700', marginRight: '6px' }}>
                  [{line.prefix}]
                </span>
              )}
              {line.text}
            </span>
          </div>
        ))}
        {isRunning && (
          <div style={{ display: 'flex', gap: '10px' }}>
            <span style={{ color: 'rgba(0,255,180,0.3)' }}>{new Date().toLocaleTimeString()}</span>
            <span style={{ color: '#0f0', fontWeight: '700' }}>█</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

export default function UserView() {
  const [loginUser, setLoginUser] = useState('demo');
  const [loginPass, setLoginPass] = useState('demo123');
  const [formName, setFormName] = useState('');
  const [formEmail, setFormEmail] = useState('');
  const [formMsg, setFormMsg] = useState('');
  const [response, setResponse] = useState(null);
  const [isBlocked, setIsBlocked] = useState(false);
  const [loading, setLoading] = useState('');
  const [attackLoading, setAttackLoading] = useState('');
  const [lastAttack, setLastAttack] = useState(null);

  // Terminal log state
  const [termLines, setTermLines] = useState([]);
  const [termRunning, setTermRunning] = useState(false);

  // IP and brute force tracking
  const [myIp, setMyIp] = useState(null);
  const [failedAttempts, setFailedAttempts] = useState(0);
  const [maxAttempts, setMaxAttempts] = useState(5);

  // ML-driven brute force state
  const [mlRiskScore,   setMlRiskScore]   = useState(0);
  const [mlSuspicious,  setMlSuspicious]  = useState(false);

  // DDoS + Port Scan demo state
  const [floodCount,      setFloodCount]      = useState(500);
  const [probeEndpoints,  setProbeEndpoints]  = useState('/admin, /api/users, /env, /config, /.git, /ssh, /backup, /db');

  // Twilio toggle status (read from global backend state)
  const [twilioEnabled, setTwilioEnabled] = useState(false);

  const fetchIp = async () => {
    try {
      const data = await api('/api/xyz/my-ip', {}, true);
      setMyIp(data.ip_address);
      setIsBlocked(data.is_blocked);
      setFailedAttempts(data.failed_attempts || 0);
      setMaxAttempts(data.max_attempts || 5);
    } catch { /* ignore */ }
  };

  // Fetch Twilio status
  const fetchTwilioStatus = async () => {
    try {
      const res = await fetch('/api/twilio/status');
      const data = await res.json();
      setTwilioEnabled(data.enabled);
    } catch { /* ignore */ }
  };

  useEffect(() => {
    fetchIp();
    fetchTwilioStatus();
    const interval = setInterval(fetchIp, 3000);
    return () => clearInterval(interval);
  }, []);

  const doRequest = async (endpoint, method, body) => {
    setLoading(endpoint);
    try {
      const options = { method };
      if (body) options.body = JSON.stringify(body);
      const data = await api(endpoint, options);
      if (data.status === 'blocked') setIsBlocked(true);
      if (data.ip_address) setMyIp(data.ip_address);
      if (data.attempts !== undefined) setFailedAttempts(data.attempts);
      // Capture ML-driven brute force signals from backend
      if (data.ml_risk     !== undefined) setMlRiskScore(data.ml_risk);
      if (data.suspicious  !== undefined) setMlSuspicious(data.suspicious);
      setResponse({ endpoint, method, data, time: new Date().toLocaleTimeString() });
    } catch (err) {
      setResponse({ endpoint, method, error: err.message, time: new Date().toLocaleTimeString() });
    }
    setLoading('');
  };

  // ── Stream terminal log lines with delay ──────────────────────────────────
  const streamLines = (lineQueue) => {
    lineQueue.forEach(({ delay, line }) => {
      setTimeout(() => {
        setTermLines(prev => [...prev, { ...line, ts: new Date().toLocaleTimeString() }]);
        if (delay === lineQueue[lineQueue.length - 1].delay) {
          setTermRunning(false);
        }
      }, delay);
    });
  };

  const launchAttack = async (attackType) => {
    setAttackLoading(attackType);
    setLastAttack(null);
    setTermLines([]);
    setTermRunning(true);

    // ── Phase 0: Pre-flight terminal lines (shown immediately while request is in flight)
    const atk = ATTACK_TYPES.find(a => a.id === attackType);
    const prelines = [
      { delay: 0,   line: { prefix: 'SYS',  prefixColor: '#60a5fa', text: `Attack simulation initiated — type: ${attackType}`, color: '#9ab0cc' } },
      { delay: 120, line: { prefix: 'SYS',  prefixColor: '#60a5fa', text: 'Generating synthetic network event (attack_probability=0.95)...', color: '#9ab0cc' } },
      { delay: 280, line: { prefix: 'INFO', prefixColor: '#34d399', text: 'SyntheticLogGenerator → sampled UNSW-NB15 traffic profile', color: '#9ab0cc' } },
      { delay: 440, line: { prefix: 'INFO', prefixColor: '#34d399', text: `attack_cat mapped → "${attackType === 'DDoS' ? 'DoS' : attackType === 'SQL Injection' || attackType === 'XSS' ? 'Exploits' : attackType === 'Port Scan' ? 'Reconnaissance' : attackType}" (label=1)`, color: '#9ab0cc' } },
      { delay: 620, line: { prefix: 'ML',   prefixColor: '#c084fc', text: 'Pipeline Step 1/6 — Building feature row (dropping non-feature keys)...', color: '#9ab0cc' } },
      { delay: 780, line: { prefix: 'ML',   prefixColor: '#c084fc', text: 'Pipeline Step 2/6 — Cleaning: replacing inf/NaN/"-" values → 0', color: '#9ab0cc' } },
      { delay: 940, line: { prefix: 'ML',   prefixColor: '#c084fc', text: 'Pipeline Step 3/6 — Feature engineering: 12 derived metrics computed', color: '#9ab0cc' } },
      { delay: 1100, line: { prefix: 'ML',  prefixColor: '#c084fc', text: '  ↳ total_bytes, packet_ratio, byte_per_packet, flow_duration_log...', color: '#566a82' } },
      { delay: 1260, line: { prefix: 'ML',  prefixColor: '#c084fc', text: '  ↳ src_load_ratio, jitter_ratio, pkt_size_asymm, loss_rate...', color: '#566a82' } },
      { delay: 1420, line: { prefix: 'ML',  prefixColor: '#c084fc', text: 'Pipeline Step 4/6 — One-hot encoding proto/service/state columns', color: '#9ab0cc' } },
      { delay: 1580, line: { prefix: 'ML',  prefixColor: '#c084fc', text: 'Pipeline Step 5/6 — Aligning to 200+ training column order (reindex)', color: '#9ab0cc' } },
      { delay: 1740, line: { prefix: 'ML',  prefixColor: '#c084fc', text: 'Pipeline Step 6/6 — MinMaxScaler.transform() → XGB feature selector', color: '#9ab0cc' } },
      { delay: 1900, line: { prefix: 'ML',  prefixColor: '#c084fc', text: 'Forwarding to LightGBM (Optuna-tuned) — predicting class probabilities...', color: '#9ab0cc' } },
    ];

    streamLines(prelines);

    // Re-fetch Twilio status right before attacking
    await fetchTwilioStatus();
    try {
      const data = await api('/api/xyz/attack', {
        method: 'POST',
        body: JSON.stringify({ attack_type: attackType, twilio_enabled: twilioEnabled }),
      });

      if (data.status === 'blocked') {
        setIsBlocked(true);
        setMyIp(data.ip_address);
      }
      setLastAttack({ type: attackType, data, time: new Date().toLocaleTimeString() });
      await fetchIp();

      // ── Phase 1: Results lines (after API returns)
      const conf = data.confidence ?? 0;
      const confPct = (conf * 100).toFixed(1);
      const modelUsed = data.model_used || 'LightGBM (Optuna-tuned)';
      const mlPred = data.ml_prediction || 'attack';
      const kc = data.kill_chain || {};
      const features = data.top_features || [];
      const ip = data.ip_address || '?';
      const cdl = data.cdl || {};
      const cdlRisk = ((cdl.risk_score || 0) * 100).toFixed(0);
      const cdlNext = cdl.prediction?.next_attack || 'RECON';
      const cdlEta  = cdl.prediction?.eta_seconds ?? 30;
      const cdlAct  = cdl.action?.action || 'MONITOR';
      const cdlProb = ((cdl.prediction?.probability || 0.45) * 100).toFixed(0);

      const resultLines = [
        { delay: 2050, line: { prefix: 'RESULT', prefixColor: '#facc15', text: `predict_proba() → raw score: ${conf.toFixed(4)}  |  threshold: 0.85`, color: '#9ab0cc' } },
        { delay: 2200, line: { prefix: 'RESULT', prefixColor: '#facc15', text: `ML Prediction: "${mlPred.toUpperCase()}"  |  Confidence: ${confPct}%  |  Model: ${modelUsed}`, color: '#f0f4ff' } },
        ...(features.length > 0 ? [
          { delay: 2340, line: { prefix: 'SHAP',  prefixColor: '#fb923c', text: 'Top feature importances (normalized):',  color: '#9ab0cc' } },
          ...features.map(([name, pct], idx) => ({
            delay: 2340 + (idx + 1) * 100,
            line: { prefix: 'SHAP', prefixColor: '#fb923c', text: `  #${idx+1} ${name.padEnd(24)} → ${(pct*100).toFixed(1)}%`, color: '#fdba74' }
          }))
        ] : []),
        { delay: 2780, line: { prefix: 'KC',    prefixColor: '#f87171',  text: `Kill Chain Stage: ${kc.stage || 'UNKNOWN'}  (${kc.mitre_id || ''} — ${kc.mitre_name || ''})`, color: '#9ab0cc' } },
        { delay: 2920, line: { prefix: 'KC',    prefixColor: '#f87171',  text: `Severity: ${kc.severity || 'HIGH'}  |  Stage #${kc.stage_num ?? '-'}`, color: '#9ab0cc' } },
        // CDL lines
        { delay: 3040, line: { text: '· · · · · · · · · · · · · · · · · · · CDL Engine · · · · · · · · · · · · · · · · · · ·', color: 'rgba(168,85,247,0.3)' } },
        { delay: 3120, line: { prefix: 'CDL', prefixColor: '#c084fc', text: `Attacker risk score → ${cdlRisk}%  (75% attack ratio + 25% activity)`, color: '#9ab0cc' } },
        { delay: 3240, line: { prefix: 'CDL', prefixColor: '#c084fc', text: `Predicted next move → ${cdlNext}  (probability: ${cdlProb}%,  ETA: ~${cdlEta}s)`, color: '#e9d5ff' } },
        { delay: 3360, line: { prefix: 'CDL', prefixColor: '#c084fc', text: `Automated countermeasure → ${cdlAct}  (${cdl.action?.description || 'Passive monitoring'})`, color: '#e9d5ff' } },
        // Action lines
        { delay: 3500, line: { prefix: 'ACTION', prefixColor: '#ef4444', text: `⚡ Confidence ${confPct}% EXCEEDS threshold 85% → BLOCK TRIGGERED`, color: '#f87171' } },
        { delay: 3640, line: { prefix: 'ACTION', prefixColor: '#ef4444', text: `Writing BlockedIP record to DB (ip=${ip}, blocked_by=ml_engine)`, color: '#9ab0cc' } },
        { delay: 3780, line: { prefix: 'ACTION', prefixColor: '#ef4444', text: `Creating CRITICAL alert → "${attackType} Attack from ${ip}"`, color: '#9ab0cc' } },
        { delay: 3920, line: { prefix: 'ACTION', prefixColor: '#ef4444', text: 'Broadcasting to admin dashboard via WebSocket...', color: '#9ab0cc' } },
        { delay: 4060, line: { prefix: 'ACTION', prefixColor: '#ef4444', text: twilioEnabled ? '📱 Twilio SMS + Voice call dispatched to admin' : '🔇 Twilio disabled — skipping SMS/call', color: twilioEnabled ? '#34d399' : '#566a82' } },
        { delay: 4200, line: { text: '─────────────────────────────────────────────────────────────', color: 'rgba(239,68,68,0.3)' } },
        { delay: 4320, line: { prefix: '██ BLOCKED', prefixColor: '#ef4444', text: `IP ${ip} has been permanently blocked. HTTP 403 returned.`, color: '#ef4444' } },
        { delay: 4460, line: { prefix: 'SYS',  prefixColor: '#60a5fa', text: `PHANTOM defense cycle complete. Threats neutralized. ✓`, color: '#34d399' } },
      ];

      // Stream result lines after the pre-flight lines
      resultLines.forEach(({ delay, line }) => {
        setTimeout(() => {
          setTermLines(prev => [...prev, { ...line, ts: new Date().toLocaleTimeString() }]);
        }, delay);
      });

      // Mark terminal done after last line
      setTimeout(() => setTermRunning(false), 4560);

    } catch (err) {
      setLastAttack({ type: attackType, error: err.message, time: new Date().toLocaleTimeString() });
      setTimeout(() => {
        setTermLines(prev => [...prev, {
          ts: new Date().toLocaleTimeString(),
          prefix: 'ERR', prefixColor: '#ef4444',
          text: `Request failed: ${err.message}`,
          color: '#f87171',
        }]);
        setTermRunning(false);
      }, 2050);
    }
    setAttackLoading('');
  };

  const attemptsRemaining = maxAttempts - failedAttempts;
  const isWarning = mlSuspicious && !isBlocked;

  return (
    <div className="user-website">
      <div className="page-header" style={{ textAlign: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
          <Globe size={24} color="var(--accent-blue)" />
          <h1>XYZ Corp</h1>
        </div>
        <p>Protected by PHANTOM Security</p>
        <div className="status-indicator" style={{ justifyContent: 'center', marginTop: '8px' }}>
          <div className={`status-dot ${isBlocked ? '' : 'operational'}`} style={isBlocked ? { background: 'var(--status-attack)' } : {}} />
          <span>{isBlocked ? 'IP Blocked' : 'System Operational'}</span>
        </div>
      </div>

      {/* Assigned IP Banner */}
      {myIp && (
        <div style={{
          background: isBlocked
            ? 'linear-gradient(135deg, rgba(220,38,38,0.15), rgba(239,68,68,0.08))'
            : 'linear-gradient(135deg, rgba(59,130,246,0.12), rgba(99,102,241,0.06))',
          border: `1px solid ${isBlocked ? 'rgba(220,38,38,0.4)' : 'rgba(59,130,246,0.2)'}`,
          borderRadius: 'var(--radius-lg)',
          padding: '16px 24px',
          marginBottom: 'var(--space-lg)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Wifi size={20} color={isBlocked ? '#ef4444' : 'var(--accent-blue)'} />
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '2px' }}>Your Assigned IP Address</div>
              <div style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '1.1rem',
                fontWeight: '600',
                color: isBlocked ? '#ef4444' : 'var(--text-primary)',
              }}>
                {myIp}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {failedAttempts > 0 && !isBlocked && (
              <div style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                background: isWarning ? 'rgba(234,179,8,0.15)' : 'rgba(255,255,255,0.05)',
                border: `1px solid ${isWarning ? 'rgba(234,179,8,0.3)' : 'var(--border-primary)'}`,
                borderRadius: 'var(--radius-md)', padding: '8px 12px',
              }}>
                <ShieldAlert size={14} color={isWarning ? '#eab308' : 'var(--text-muted)'} />
                <span style={{ fontSize: '0.8rem', color: isWarning ? '#eab308' : 'var(--text-muted)', fontWeight: '500' }}>
                  {failedAttempts}/{maxAttempts} attempts
                </span>
              </div>
            )}
            <div style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              background: isBlocked ? 'linear-gradient(135deg, #dc2626, #ef4444)' : 'rgba(34,197,94,0.15)',
              color: isBlocked ? '#fff' : '#22c55e',
              padding: '6px 14px', borderRadius: 'var(--radius-md)',
              fontSize: '0.75rem', fontWeight: '700', letterSpacing: '0.05em', textTransform: 'uppercase',
            }}>
              {isBlocked ? <><ShieldAlert size={12} /> BLOCKED</> : <><ShieldCheck size={12} /> ACTIVE</>}
            </div>
          </div>
        </div>
      )}

      {/* BLOCKED BANNER */}
      {isBlocked && (
        <div className="blocked-banner" style={{
          background: 'linear-gradient(135deg, rgba(220,38,38,0.2), rgba(239,68,68,0.1))',
          border: '2px solid rgba(220,38,38,0.5)',
          borderRadius: 'var(--radius-lg)',
          padding: '32px',
          textAlign: 'center',
          marginBottom: 'var(--space-lg)',
          animation: 'pulse 2s infinite',
        }}>
          <AlertTriangle size={40} color="#f87171" style={{ marginBottom: '12px' }} />
          <h2 style={{ color: '#f87171', marginBottom: '8px' }}>🚫 Access Denied</h2>
          <p style={{ fontSize: '1rem', color: '#fca5a5', marginBottom: '8px' }}>
            Your IP <code style={{ background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: '4px' }}>{myIp}</code> has been blocked by PHANTOM's AI defense system.
          </p>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Reason: Unusual / malicious activity detected. Contact your administrator.
          </p>
        </div>
      )}

      {/* Warning Banner */}
      {isWarning && !isBlocked && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(234,179,8,0.12), rgba(245,158,11,0.06))',
          border: '1px solid rgba(234,179,8,0.3)',
          borderRadius: 'var(--radius-lg)',
          padding: '16px 24px',
          marginBottom: 'var(--space-lg)',
          display: 'flex', alignItems: 'center', gap: '12px',
        }}>
          <AlertTriangle size={20} color="#eab308" />
          <div>
            <div style={{ fontWeight: '600', color: '#eab308', fontSize: '0.9rem' }}>
              ⚠️ Warning: Suspicious Activity Detected
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              {attemptsRemaining} login attempt{attemptsRemaining !== 1 ? 's' : ''} remaining before your IP is blocked.
            </div>
          </div>
        </div>
      )}


      {/* ── ATTACK SIMULATION PANEL ─────────────────────────────── */}
      <div className="card" style={{
        marginBottom: 'var(--space-lg)',
        border: '1px solid rgba(239,68,68,0.3)',
        background: 'linear-gradient(135deg, rgba(239,68,68,0.06), rgba(220,38,38,0.03))',
      }}>
        <div className="card-header" style={{ borderBottom: '1px solid rgba(239,68,68,0.2)' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f87171' }}>
            <Zap size={16} color="#f87171" />
            ⚔️ Attack Simulation Panel
          </h3>
          <span style={{
            fontSize: '0.7rem', color: '#f87171',
            background: 'rgba(239,68,68,0.15)',
            border: '1px solid rgba(239,68,68,0.3)',
            padding: '2px 10px', borderRadius: '20px',
            fontWeight: '600', letterSpacing: '0.05em',
          }}>ATTACKER MODE</span>
        </div>

        <div style={{ padding: 'var(--space-md) 0' }}>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 'var(--space-md)', padding: '0 var(--space-md)' }}>
            Select an attack type. PHANTOM's AI will detect it instantly, auto-block your IP, and alert the admin in real time.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '12px', padding: '0 var(--space-md)' }}>
            {ATTACK_TYPES.map((atk) => {
              const isLoading = attackLoading === atk.id;
              return (
                <button
                  key={atk.id}
                  onClick={() => !isBlocked && launchAttack(atk.id)}
                  disabled={isBlocked || !!attackLoading}
                  style={{
                    background: isBlocked ? 'var(--bg-input)' : atk.hoverColor,
                    border: `1px solid ${isBlocked ? 'var(--border-primary)' : atk.border}`,
                    borderRadius: 'var(--radius-lg)',
                    padding: '16px 14px',
                    cursor: isBlocked || !!attackLoading ? 'not-allowed' : 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.2s',
                    opacity: isBlocked ? 0.5 : 1,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px',
                  }}
                >
                  <div style={{ fontSize: '1.5rem' }}>{isLoading ? '⏳' : atk.icon}</div>
                  <div style={{ fontWeight: '700', color: isBlocked ? 'var(--text-muted)' : atk.color, fontSize: '0.9rem' }}>
                    {atk.label}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                    {atk.desc}
                  </div>
                  {isLoading && (
                    <div style={{ fontSize: '0.7rem', color: atk.color, fontWeight: '600', marginTop: '4px' }}>
                      Launching...
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* ── Live Terminal Log ────────────────────────────── */}
          <TerminalLog lines={termLines} isRunning={termRunning} />

          {/* ── Attack Intelligence Panel ───────────────────── */}
          {lastAttack && !termRunning && lastAttack.data && (
            <AttackIntelPanel lastAttack={lastAttack} />
          )}
        </div>
      </div>

      {/* ── NORMAL USER ACTIONS ────────────────────────────────── */}
      <div className="card" style={{ marginBottom: 'var(--space-lg)', border: '1px solid rgba(59,130,246,0.15)' }}>
        <div className="card-header">
          <h3 style={{ color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={16} />
            Normal User Actions
          </h3>
          <span style={{
            fontSize: '0.7rem', color: 'var(--accent-blue)',
            background: 'rgba(59,130,246,0.1)',
            border: '1px solid rgba(59,130,246,0.2)',
            padding: '2px 10px', borderRadius: '20px',
            fontWeight: '600',
          }}>STANDARD</span>
        </div>

        <div style={{ padding: '0 var(--space-md) var(--space-md)', display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>

          {/* ── 🔨 Brute Force — Login Form ─────────────────────── */}
          <div style={{
            background: 'var(--bg-input)', borderRadius: 'var(--radius-md)',
            padding: 'var(--space-md)', border: '1px solid var(--border-primary)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
              <h4 style={{ color: 'var(--text-secondary)', margin: 0 }}>Login to XYZ</h4>
              <span style={{ fontSize: '0.65rem', background: 'rgba(248,113,113,0.12)', border: '1px solid rgba(248,113,113,0.3)', color: '#f87171', padding: '2px 8px', borderRadius: '10px', fontWeight: '700' }}>🔨 Brute Force target</span>
            </div>
            <div style={{ marginBottom: '10px', padding: '8px 12px', background: 'rgba(248,113,113,0.06)', border: '1px solid rgba(248,113,113,0.15)', borderRadius: '8px', fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              <strong style={{ color: '#f87171' }}>💡 Try Brute Force:</strong> Leave username as <code style={{ background: 'rgba(255,255,255,0.08)', padding: '1px 5px', borderRadius: '3px' }}>demo</code> and type a wrong password. Repeat 5× — ML risk score escalates and blocks on attempt 5+.<br/>
              <strong style={{ color: '#fb923c' }}>💡 Try SQL Injection:</strong> Paste into Username: <code style={{ background: 'rgba(255,255,255,0.08)', padding: '1px 5px', borderRadius: '3px', userSelect: 'all' }}>' OR 1=1 --</code> &nbsp;or&nbsp; <code style={{ background: 'rgba(255,255,255,0.08)', padding: '1px 5px', borderRadius: '3px', userSelect: 'all' }}>admin'; DROP TABLE users;--</code>
            </div>
            <div className="input-group">
              <label>Username</label>
              <input className="input" value={loginUser} onChange={(e) => setLoginUser(e.target.value)} disabled={isBlocked} placeholder="demo  — or paste SQL payload here" />
            </div>
            <div className="input-group">
              <label>Password</label>
              <input className="input" type="password" value={loginPass} onChange={(e) => setLoginPass(e.target.value)} disabled={isBlocked} />
            </div>
            <button
              className="btn btn-primary"
              onClick={() => doRequest('/api/xyz/login', 'POST', { username: loginUser, password: loginPass })}
              disabled={loading === '/api/xyz/login' || isBlocked}
            >
              {loading === '/api/xyz/login' ? <span className="spinner" /> : isBlocked ? '🚫 Blocked' : 'Login'}
            </button>
          </div>

          {/* ── 🌩️ DDoS — Fetch Data + Flood ───────────────────── */}
          <div style={{
            background: 'var(--bg-input)', borderRadius: 'var(--radius-md)',
            padding: 'var(--space-md)', border: '1px solid var(--border-primary)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
              <h4 style={{ color: 'var(--text-secondary)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Database size={14} /> Fetch Product Data
              </h4>
              <span style={{ fontSize: '0.65rem', background: 'rgba(192,132,252,0.12)', border: '1px solid rgba(192,132,252,0.3)', color: '#c084fc', padding: '2px 8px', borderRadius: '10px', fontWeight: '700' }}>🌩️ DDoS target</span>
            </div>
            <div style={{ marginBottom: '10px', padding: '8px 12px', background: 'rgba(192,132,252,0.06)', border: '1px solid rgba(192,132,252,0.15)', borderRadius: '8px', fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              <strong style={{ color: '#c084fc' }}>💡 Try DDoS (Rate):</strong> Click <em>GET /api/xyz/data</em> rapidly 5+ times in 10 seconds — backend rate detector fires ML DoS pipeline.<br/>
              <strong style={{ color: '#c084fc' }}>💡 Try DDoS (Flood):</strong> Enter a packet count below and click <em>Launch Flood</em> — sends one request that triggers the ML DoS model.
            </div>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
              <button
                className="btn btn-secondary"
                onClick={() => doRequest('/api/xyz/data', 'GET')}
                disabled={loading === '/api/xyz/data' || isBlocked}
                style={{ flexShrink: 0 }}
              >
                {loading === '/api/xyz/data' ? <span className="spinner" /> : 'GET /api/xyz/data'}
              </button>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end', flex: 1, minWidth: '200px' }}>
                <div className="input-group" style={{ flex: 1, margin: 0 }}>
                  <label style={{ fontSize: '0.72rem' }}>Packet Count (DDoS Flood)</label>
                  <input
                    className="input"
                    type="number"
                    min="10" max="9999"
                    value={floodCount}
                    onChange={(e) => setFloodCount(Number(e.target.value))}
                    disabled={isBlocked}
                    style={{ fontFamily: 'var(--font-mono)' }}
                  />
                </div>
                <button
                  className="btn btn-primary"
                  onClick={() => doRequest('/api/xyz/flood', 'POST', { count: floodCount })}
                  disabled={loading === '/api/xyz/flood' || isBlocked}
                  style={{ flexShrink: 0, background: 'linear-gradient(135deg, rgba(192,132,252,0.3), rgba(168,85,247,0.2))', border: '1px solid rgba(192,132,252,0.5)', color: '#c084fc' }}
                >
                  {loading === '/api/xyz/flood' ? <span className="spinner" /> : '🌩️ Launch Flood'}
                </button>
              </div>
            </div>
          </div>

          {/* ── 🕷️ XSS — Contact Form ───────────────────────────── */}
          <div style={{
            background: 'var(--bg-input)', borderRadius: 'var(--radius-md)',
            padding: 'var(--space-md)', border: '1px solid var(--border-primary)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
              <h4 style={{ color: 'var(--text-secondary)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Send size={14} /> Contact Form
              </h4>
              <span style={{ fontSize: '0.65rem', background: 'rgba(250,204,21,0.12)', border: '1px solid rgba(250,204,21,0.3)', color: '#facc15', padding: '2px 8px', borderRadius: '10px', fontWeight: '700' }}>🕷️ XSS target</span>
            </div>
            <div style={{ marginBottom: '10px', padding: '8px 12px', background: 'rgba(250,204,21,0.06)', border: '1px solid rgba(250,204,21,0.15)', borderRadius: '8px', fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              <strong style={{ color: '#facc15' }}>💡 Try XSS:</strong> Paste into Message: <code style={{ background: 'rgba(255,255,255,0.08)', padding: '1px 5px', borderRadius: '3px', userSelect: 'all' }}>&lt;script&gt;alert('XSS')&lt;/script&gt;</code>
              &nbsp;or&nbsp; <code style={{ background: 'rgba(255,255,255,0.08)', padding: '1px 5px', borderRadius: '3px', userSelect: 'all' }}>&lt;img src=x onerror=alert(document.cookie)&gt;</code>
            </div>
            <div className="input-group">
              <label>Name</label>
              <input className="input" value={formName} onChange={(e) => setFormName(e.target.value)} placeholder="Your name" disabled={isBlocked} />
            </div>
            <div className="input-group">
              <label>Email</label>
              <input className="input" type="email" value={formEmail} onChange={(e) => setFormEmail(e.target.value)} placeholder="you@email.com" disabled={isBlocked} />
            </div>
            <div className="input-group">
              <label>Message — paste XSS payload here</label>
              <input className="input" value={formMsg} onChange={(e) => setFormMsg(e.target.value)} placeholder="Your message  — or paste XSS payload" disabled={isBlocked} />
            </div>
            <button
              className="btn btn-primary"
              onClick={() => doRequest('/api/xyz/form', 'POST', { name: formName, email: formEmail, message: formMsg })}
              disabled={loading === '/api/xyz/form' || isBlocked}
            >
              {loading === '/api/xyz/form' ? <span className="spinner" /> : 'Submit Form'}
            </button>
          </div>

          {/* ── 🔍 Port Scan — Endpoint Probe ───────────────────── */}
          <div style={{
            background: 'var(--bg-input)', borderRadius: 'var(--radius-md)',
            padding: 'var(--space-md)', border: '1px solid var(--border-primary)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
              <h4 style={{ color: 'var(--text-secondary)', margin: 0 }}>🔍 Endpoint Probe</h4>
              <span style={{ fontSize: '0.65rem', background: 'rgba(96,165,250,0.12)', border: '1px solid rgba(96,165,250,0.3)', color: '#60a5fa', padding: '2px 8px', borderRadius: '10px', fontWeight: '700' }}>Port Scan target</span>
            </div>
            <div style={{ marginBottom: '10px', padding: '8px 12px', background: 'rgba(96,165,250,0.06)', border: '1px solid rgba(96,165,250,0.15)', borderRadius: '8px', fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              <strong style={{ color: '#60a5fa' }}>💡 Try Port Scan:</strong> List the endpoints you want to "probe" (comma-separated). The ML Reconnaissance model detects the enumeration pattern and blocks the IP.
            </div>
            <div className="input-group">
              <label>Endpoints to probe (comma-separated)</label>
              <input
                className="input"
                value={probeEndpoints}
                onChange={(e) => setProbeEndpoints(e.target.value)}
                placeholder="/admin, /api/users, /env, /config, /.git"
                disabled={isBlocked}
                style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}
              />
            </div>
            <button
              className="btn btn-primary"
              onClick={() => doRequest('/api/xyz/probe', 'POST', {
                endpoints: probeEndpoints.split(',').map(e => e.trim()).filter(Boolean)
              })}
              disabled={loading === '/api/xyz/probe' || isBlocked}
              style={{ background: 'linear-gradient(135deg, rgba(96,165,250,0.25), rgba(59,130,246,0.15))', border: '1px solid rgba(96,165,250,0.4)', color: '#60a5fa' }}
            >
              {loading === '/api/xyz/probe' ? <span className="spinner" /> : '🔍 Probe Endpoints'}
            </button>
          </div>

        </div>
      </div>

      {/* Response */}
      {response && (
        <div className="card" style={{ marginTop: '16px' }}>
          <div className="card-header">
            <h3>Response</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{response.time}</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '8px', fontFamily: 'var(--font-mono)', padding: '0 var(--space-md)' }}>
            {response.method} {response.endpoint}
          </div>
          <div className="response-box">
            {response.error ? `Error: ${response.error}` : JSON.stringify(response.data, null, 2)}
          </div>
        </div>
      )}
    </div>
  );
}

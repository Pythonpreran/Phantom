/**
 * PHANTOM — Login & Sign Up Page
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Shield, UserPlus, RotateCcw, Phone, PhoneOff } from 'lucide-react';

export default function Login() {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const { login, register, loading } = useAuth();
  const navigate = useNavigate();
  const [resetting, setResetting] = useState(false);
  const [resetMsg, setResetMsg] = useState('');

  // Twilio toggle state
  const [twilioEnabled, setTwilioEnabled] = useState(false);
  const [twilioLoading, setTwilioLoading] = useState(false);
  const [twilioMsg, setTwilioMsg] = useState('');

  // Fetch Twilio status on mount
  useEffect(() => {
    const fetchTwilioStatus = async () => {
      try {
        const res = await fetch('/api/twilio/status');
        const data = await res.json();
        setTwilioEnabled(data.enabled);
      } catch { /* ignore */ }
    };
    fetchTwilioStatus();
  }, []);

  const toggleTwilio = async () => {
    setTwilioLoading(true);
    setTwilioMsg('');
    try {
      const res = await fetch('/api/twilio/toggle', { method: 'POST' });
      const data = await res.json();
      setTwilioEnabled(data.enabled);
      setTwilioMsg(data.enabled ? '✅ Twilio alerts enabled' : '🔇 Twilio alerts disabled');
      setTimeout(() => setTwilioMsg(''), 3000);
    } catch (err) {
      setTwilioMsg('Failed to toggle: ' + err.message);
    }
    setTwilioLoading(false);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    try {
      const user = await login(email, password);
      if (user.role === 'admin') navigate('/admin');
      else if (user.role === 'company') navigate('/company');
      else navigate('/user');
    } catch (err) {
      setError(err.message || 'Login failed');
    }
  };

  const handleSignUp = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (!username.trim()) {
      setError('Please enter a display name');
      return;
    }
    if (!email.trim() || !password.trim()) {
      setError('Please fill in all fields');
      return;
    }
    if (password.length < 4) {
      setError('Password must be at least 4 characters');
      return;
    }

    try {
      const user = await register(email, username, password, 'user');
      setSuccessMsg(`Account created! Welcome, ${user.username}. Redirecting...`);
      setTimeout(() => {
        navigate('/user');
      }, 1000);
    } catch (err) {
      setError(err.message || 'Registration failed');
    }
  };

  const quickLogin = async (email, password) => {
    setEmail(email);
    setPassword(password);
    setError('');
    setSuccessMsg('');
    try {
      const user = await login(email, password);
      if (user.role === 'admin') navigate('/admin');
      else if (user.role === 'company') navigate('/company');
      else navigate('/user');
    } catch (err) {
      setError(err.message || 'Login failed');
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-brand">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px', marginBottom: '8px' }}>
            <Shield size={32} strokeWidth={1.5} color="var(--accent-blue)" />
            <h1>PHANTOM</h1>
          </div>
          <p>AI-Powered Cybersecurity Defense System</p>
        </div>

        {/* Toggle: Sign In / Sign Up */}
        <div style={{
          display: 'flex',
          background: 'var(--bg-input)',
          borderRadius: 'var(--radius-md)',
          padding: '4px',
          marginBottom: '20px',
        }}>
          <button
            type="button"
            onClick={() => { setIsSignUp(false); setError(''); setSuccessMsg(''); }}
            style={{
              flex: 1,
              padding: '10px',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '0.85rem',
              transition: 'all 0.2s',
              background: !isSignUp ? 'var(--accent-blue)' : 'transparent',
              color: !isSignUp ? '#fff' : 'var(--text-muted)',
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setIsSignUp(true); setError(''); setSuccessMsg(''); }}
            style={{
              flex: 1,
              padding: '10px',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '0.85rem',
              transition: 'all 0.2s',
              background: isSignUp ? 'var(--accent-blue)' : 'transparent',
              color: isSignUp ? '#fff' : 'var(--text-muted)',
            }}
          >
            <UserPlus size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
            Sign Up
          </button>
        </div>

        <div className="login-form">
          <h2>{isSignUp ? 'Create Account' : 'Sign In'}</h2>
          {isSignUp && (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '16px' }}>
              Sign up to get your own unique IP address on the XYZ website
            </p>
          )}

          {error && <div className="login-error">{error}</div>}
          {successMsg && (
            <div style={{
              background: 'rgba(34,197,94,0.1)',
              border: '1px solid rgba(34,197,94,0.3)',
              borderRadius: 'var(--radius-md)',
              padding: '12px 16px',
              color: '#22c55e',
              fontSize: '0.85rem',
              marginBottom: '16px',
            }}>
              {successMsg}
            </div>
          )}

          <form onSubmit={isSignUp ? handleSignUp : handleLogin}>
            {isSignUp && (
              <div className="input-group">
                <label>Display Name</label>
                <input
                  type="text"
                  className="input"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Your name"
                  required
                />
              </div>
            )}

            <div className="input-group">
              <label>Email</label>
              <input
                type="email"
                className="input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
              />
            </div>

            <div className="input-group">
              <label>Password</label>
              <input
                type="password"
                className="input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <span className="spinner" /> : isSignUp ? 'Create Account' : 'Sign In'}
            </button>
          </form>
        </div>

        {/* Quick Access — Demo Accounts */}
        {!isSignUp && (
          <div className="login-demo">
            <strong>Quick Access — Demo Accounts</strong>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '8px' }}>
              <button
                className="btn btn-secondary btn-sm"
                style={{ justifyContent: 'space-between', width: '100%' }}
                onClick={() => quickLogin('admin@phantom.io', 'admin123')}
              >
                <span>Full Admin (PHANTOM)</span>
                <code>admin@phantom.io</code>
              </button>
              
              <div style={{ height: '1px', background: 'var(--border-primary)', margin: '4px 0' }} />
              
              <button
                className="btn btn-secondary btn-sm"
                style={{ justifyContent: 'space-between', width: '100%', borderColor: 'rgba(16,185,129,0.3)' }}
                onClick={() => quickLogin('abc@company.com', 'abc123')}
              >
                <span style={{ color: '#34d399' }}>ABC Corp Rep</span>
                <code>abc@company.com</code>
              </button>
              <button
                className="btn btn-secondary btn-sm"
                style={{ justifyContent: 'space-between', width: '100%', borderColor: 'rgba(99,102,241,0.3)' }}
                onClick={() => quickLogin('xyz@company.com', 'xyz123')}
              >
                <span style={{ color: '#818cf8' }}>XYZ Corp Rep</span>
                <code>xyz@company.com</code>
              </button>

              <div style={{ height: '1px', background: 'var(--border-primary)', margin: '4px 0' }} />

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                <button className="btn btn-secondary btn-sm" onClick={() => quickLogin('alice@abc.com', 'alice123')}>
                  <span>Alice (ABC)</span>
                </button>
                <button className="btn btn-secondary btn-sm" onClick={() => quickLogin('bob@abc.com', 'bob123')}>
                  <span>Bob (ABC)</span>
                </button>
                <button className="btn btn-secondary btn-sm" onClick={() => quickLogin('sarah@xyz.com', 'sarah123')}>
                  <span>Sarah (XYZ)</span>
                </button>
                <button className="btn btn-secondary btn-sm" onClick={() => quickLogin('mike@xyz.com', 'mike123')}>
                  <span>Mike (XYZ)</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Twilio Alerts Toggle ──────────────────────────────── */}
        <div style={{
          marginTop: '16px',
          padding: '16px 20px',
          background: twilioEnabled
            ? 'linear-gradient(135deg, rgba(34,197,94,0.08), rgba(16,185,129,0.04))'
            : 'linear-gradient(135deg, rgba(100,116,139,0.08), rgba(71,85,105,0.04))',
          border: `1px solid ${twilioEnabled ? 'rgba(34,197,94,0.3)' : 'rgba(100,116,139,0.2)'}`,
          borderRadius: 'var(--radius-lg)',
          transition: 'all 0.3s ease',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              {twilioEnabled
                ? <Phone size={18} color="#22c55e" />
                : <PhoneOff size={18} color="#64748b" />
              }
              <div>
                <div style={{
                  fontWeight: '700',
                  fontSize: '0.85rem',
                  color: twilioEnabled ? '#22c55e' : 'var(--text-secondary)',
                }}>
                  Twilio Alerts
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  SMS + Voice call on attack detection
                </div>
              </div>
            </div>

            {/* Toggle Switch */}
            <button
              onClick={toggleTwilio}
              disabled={twilioLoading}
              style={{
                position: 'relative',
                width: '52px',
                height: '28px',
                borderRadius: '14px',
                border: 'none',
                cursor: twilioLoading ? 'wait' : 'pointer',
                background: twilioEnabled
                  ? 'linear-gradient(135deg, #22c55e, #16a34a)'
                  : 'rgba(100,116,139,0.3)',
                transition: 'all 0.3s ease',
                padding: 0,
                flexShrink: 0,
                boxShadow: twilioEnabled
                  ? '0 0 12px rgba(34,197,94,0.3)'
                  : 'none',
              }}
            >
              <div style={{
                position: 'absolute',
                top: '3px',
                left: twilioEnabled ? '26px' : '3px',
                width: '22px',
                height: '22px',
                borderRadius: '50%',
                background: '#fff',
                transition: 'all 0.3s ease',
                boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
              }} />
            </button>
          </div>

          {twilioMsg && (
            <div style={{
              marginTop: '10px',
              fontSize: '0.78rem',
              color: twilioEnabled ? '#22c55e' : '#94a3b8',
              fontWeight: '500',
              textAlign: 'center',
              padding: '6px 12px',
              background: twilioEnabled
                ? 'rgba(34,197,94,0.1)'
                : 'rgba(100,116,139,0.1)',
              borderRadius: 'var(--radius-sm)',
            }}>
              {twilioMsg}
            </div>
          )}
        </div>

        {/* Reset System Button */}
        <div style={{
          marginTop: '16px',
          padding: '16px',
          background: 'linear-gradient(135deg, rgba(239,68,68,0.06), rgba(220,38,38,0.03))',
          border: '1px solid rgba(239,68,68,0.2)',
          borderRadius: 'var(--radius-lg)',
          textAlign: 'center',
        }}>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '10px' }}>
            Reset all logs, unblock all IPs, and start a fresh demo session
          </p>
          {resetMsg && (
            <div style={{
              background: 'rgba(34,197,94,0.1)',
              border: '1px solid rgba(34,197,94,0.3)',
              borderRadius: 'var(--radius-md)',
              padding: '8px 12px',
              color: '#22c55e',
              fontSize: '0.8rem',
              marginBottom: '10px',
            }}>
              {resetMsg}
            </div>
          )}
          <button
            className="btn"
            disabled={resetting}
            onClick={async () => {
              setResetting(true);
              setResetMsg('');
              try {
                const res = await fetch('/api/reset', { method: 'POST' });
                const data = await res.json();
                setResetMsg(data.message || 'System reset complete!');
              } catch (err) {
                setResetMsg('Reset failed: ' + err.message);
              }
              setResetting(false);
            }}
            style={{
              background: 'linear-gradient(135deg, #dc2626, #ef4444)',
              color: '#fff',
              border: '1px solid rgba(239,68,68,0.5)',
              padding: '10px 24px',
              borderRadius: 'var(--radius-md)',
              fontWeight: '700',
              fontSize: '0.85rem',
              cursor: resetting ? 'wait' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              width: '100%',
              opacity: resetting ? 0.6 : 1,
            }}
          >
            {resetting ? <span className="spinner" /> : <RotateCcw size={14} />}
            {resetting ? 'Resetting...' : 'Reset System'}
          </button>
        </div>
      </div>
    </div>
  );
}

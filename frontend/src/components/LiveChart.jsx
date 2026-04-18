/**
 * PHANTOM — LiveChart Component
 * Accepts DB-queried chart buckets (primary) or falls back to WebSocket events.
 */

import { useMemo } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend
} from 'recharts';

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: '#1e293b', border: '1px solid #334155',
      borderRadius: '8px', padding: '8px 12px', fontSize: '0.8rem',
    }}>
      <div style={{ color: '#94a3b8', marginBottom: '4px' }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, fontFamily: 'JetBrains Mono, monospace' }}>
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
}

export default function LiveChart({ events = [], chartBuckets = [] }) {
  // If we have DB chart buckets, use them (preferred)
  const dbData = useMemo(() => {
    if (chartBuckets.length > 0) return chartBuckets;
    return null;
  }, [chartBuckets]);

  // Fall back to deriving from WebSocket events if no DB data
  const wsData = useMemo(() => {
    if (dbData) return null;
    const buckets = {};
    const now = Date.now();

    events.forEach((e) => {
      const ts = new Date(e.timestamp).getTime();
      const bucket = Math.floor((now - ts) / 5000);
      if (bucket > 24) return;
      if (!buckets[bucket]) buckets[bucket] = { normal: 0, suspicious: 0, attack: 0 };
      if (e.prediction === 'attack') buckets[bucket].attack++;
      else if (e.prediction === 'suspicious') buckets[bucket].suspicious++;
      else buckets[bucket].normal++;
    });

    return Array.from({ length: 25 }, (_, i) => {
      const bucket = 24 - i;
      const secsAgo = bucket * 5;
      const label = secsAgo === 0 ? 'Now' : secsAgo <= 60 ? `${secsAgo}s` : `${Math.floor(secsAgo/60)}m`;
      return {
        time: label,
        Normal: buckets[bucket]?.normal || 0,
        Suspicious: buckets[bucket]?.suspicious || 0,
        Attack: buckets[bucket]?.attack || 0,
      };
    });
  }, [events, dbData]);

  const chartData = dbData || wsData || [];
  const hasData = chartData.some(d => d.Normal > 0 || d.Suspicious > 0 || d.Attack > 0);

  return (
    <div className="chart-container" style={{ position: 'relative' }}>
      {!hasData && (
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          color: 'var(--text-muted)', fontSize: '0.85rem', gap: '8px', zIndex: 2,
        }}>
          <div style={{ fontSize: '1.5rem', opacity: 0.4 }}>📊</div>
          <div>No activity yet — waiting for real user requests</div>
        </div>
      )}
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="normalGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="suspGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="attackGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ef4444" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={{ stroke: '#1e293b' }} tickLine={false} />
          <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
          <Tooltip content={<CustomTooltip />} />
          <Area type="monotone" dataKey="Normal" stroke="#10b981" fill="url(#normalGrad)" strokeWidth={2} />
          <Area type="monotone" dataKey="Suspicious" stroke="#f59e0b" fill="url(#suspGrad)" strokeWidth={2} />
          <Area type="monotone" dataKey="Attack" stroke="#ef4444" fill="url(#attackGrad)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

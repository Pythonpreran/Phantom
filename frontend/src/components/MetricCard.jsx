/**
 * PHANTOM — MetricCard Component (Premium)
 */

export default function MetricCard({ icon, value, label, color = 'var(--accent-blue)', trend }) {
  return (
    <div className="metric-card" style={{ '--card-accent': color }}>
      {/* Top accent bar */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '3px',
        background: `linear-gradient(90deg, ${color}, transparent)`,
        borderRadius: 'var(--radius-lg) var(--radius-lg) 0 0',
        opacity: 0.8,
      }} />

      {icon && (
        <div className="metric-icon" style={{
          background: `${color}18`,
          color,
          boxShadow: `0 0 12px ${color}22`,
        }}>
          {icon}
        </div>
      )}

      <div className="metric-content">
        <div className="metric-value" style={{
          color,
          fontFamily: 'var(--font-heading)',
          textShadow: `0 0 20px ${color}33`,
        }}>
          {typeof value === 'number' ? value.toLocaleString() : (value ?? '—')}
        </div>
        <div className="metric-label">{label}</div>
        {trend !== undefined && (
          <div style={{
            fontSize: '0.75rem',
            marginTop: '6px',
            color: trend >= 0 ? 'var(--status-normal)' : 'var(--status-attack)',
            fontWeight: '600',
          }}>
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </div>
        )}
      </div>
    </div>
  );
}

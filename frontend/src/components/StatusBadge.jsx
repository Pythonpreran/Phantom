/**
 * PHANTOM — StatusBadge Component
 */

export default function StatusBadge({ status }) {
  const s = (status || '').toLowerCase();
  let className = 'badge ';

  if (s === 'normal' || s === 'operational' || s === 'low') className += 'badge-normal';
  else if (s === 'suspicious' || s === 'medium' || s === 'monitor') className += 'badge-suspicious';
  else if (s === 'attack' || s === 'high') className += 'badge-attack';
  else if (s === 'blocked') className += 'badge-blocked';
  else if (s === 'critical') className += 'badge-critical';
  else className += 'badge-normal';

  return <span className={className}>{status}</span>;
}

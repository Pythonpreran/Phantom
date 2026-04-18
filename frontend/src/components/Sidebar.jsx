/**
 * PHANTOM — Sidebar with Dark / Light Theme Toggle
 */

import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  LayoutDashboard, Shield, Ban, FlaskConical,
  FileText, Bug, Brain, LogOut, Globe, Sun, Moon,
} from 'lucide-react';
import { useTheme } from '../hooks/useTheme';

export default function Sidebar() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/login'); };

  const initials = user?.username
    ? user.username.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : '??';

  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="brand-dot" />
        <h2>PHANTOM</h2>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {user?.role === 'user' && (
          <div className="sidebar-section">
            <div className="sidebar-section-title">Website</div>
            <NavLink to="/user" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Globe size={18} /> XYZ Website
            </NavLink>
          </div>
        )}

        {(user?.role === 'company' || user?.role === 'admin') && (
          <div className="sidebar-section">
            <div className="sidebar-section-title">Company</div>
            <NavLink to="/company" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <LayoutDashboard size={18} /> Dashboard
            </NavLink>
            <NavLink to="/company/threats" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Shield size={18} /> Threats
            </NavLink>
            <NavLink to="/company/blocked" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Ban size={18} /> Blocked IPs
            </NavLink>
            <NavLink to="/company/validation" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <FlaskConical size={18} /> Validation Lab
            </NavLink>
          </div>
        )}

        {user?.role === 'admin' && (
          <div className="sidebar-section">
            <div className="sidebar-section-title">Admin</div>
            <NavLink to="/admin" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Brain size={18} /> Overview
            </NavLink>
            <NavLink to="/admin/logs" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <FileText size={18} /> Logs
            </NavLink>
            <NavLink to="/admin/honeypot" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Bug size={18} /> Honeypot
            </NavLink>
            <NavLink to="/admin/ips" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Ban size={18} /> IP Management
            </NavLink>
          </div>
        )}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">

        {/* User row */}
        <div className="sidebar-user">
          <div className="sidebar-user-avatar">{initials}</div>
          <div className="sidebar-user-info">
            <div className="sidebar-user-name">{user?.username}</div>
            <div className="sidebar-user-role">{user?.role}</div>
          </div>
          <button
            onClick={handleLogout}
            className="theme-toggle"
            title="Logout"
            style={{ background: 'rgba(239,68,68,0.1)', borderColor: 'rgba(239,68,68,0.2)', color: '#f87171' }}
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </aside>
  );
}

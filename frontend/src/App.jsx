/**
 * PHANTOM — App Entry (Router + JWT Auth)
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { ThemeProvider, useTheme } from './hooks/useTheme';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import UserView from './pages/UserView';
import CompanyDashboard from './pages/CompanyDashboard';
import ValidationLab from './pages/ValidationLab';
import AdminDashboard from './pages/AdminDashboard';
import { Sun, Moon } from 'lucide-react';
import Landing from './components/Landing';
import Home from './pages/Home';

/** Floating theme toggle — always top-right, never hidden */
function ThemeToggleBtn() {
  const { theme, toggleTheme } = useTheme();
  // Hide on the landing page — it has its own fixed dark aesthetic
  if (window.location.pathname === '/') return null;
  return (
    <button
      onClick={toggleTheme}
      title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      style={{
        position: 'fixed',
        top: '14px',
        right: '18px',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '6px 14px',
        borderRadius: '999px',
        background: theme === 'dark'
          ? 'rgba(250,204,21,0.13)'
          : 'rgba(99,102,241,0.13)',
        border: `1.5px solid ${theme === 'dark' ? 'rgba(250,204,21,0.35)' : 'rgba(99,102,241,0.35)'}`,
        color: theme === 'dark' ? '#fde68a' : '#818cf8',
        cursor: 'pointer',
        fontSize: '0.78rem',
        fontWeight: '600',
        fontFamily: 'var(--font-body)',
        letterSpacing: '0.04em',
        boxShadow: theme === 'dark'
          ? '0 2px 12px rgba(250,204,21,0.15)'
          : '0 2px 12px rgba(99,102,241,0.15)',
        backdropFilter: 'blur(8px)',
        transition: 'all 0.2s',
      }}
    >
      {theme === 'dark' ? <Sun size={13} /> : <Moon size={13} />}
      {theme === 'dark' ? 'Light' : 'Dark'}
    </button>
  );
}

function ProtectedRoute({ children, allowedRoles }) {
  const { user } = useAuth();

  if (!user) return <Navigate to="/login" replace />;
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    if (user.role === 'admin') return <Navigate to="/admin" replace />;
    if (user.role === 'company') return <Navigate to="/company" replace />;
    return <Navigate to="/user" replace />;
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">{children}</main>
    </div>
  );
}

function AppRoutes() {
  const { user } = useAuth();

  return (
    <Routes>
      {/* Landing page — public, no auth, no sidebar */}
      <Route path="/" element={user ? <Navigate to={user.role === 'admin' ? '/admin' : user.role === 'company' ? '/company' : '/user'} replace /> : <Home />} />

      <Route path="/login" element={user ? <Navigate to={user.role === 'admin' ? '/admin' : user.role === 'company' ? '/company' : '/user'} replace /> : <Login />} />

      {/* User routes */}
      <Route path="/user" element={<ProtectedRoute allowedRoles={['user']}><UserView /></ProtectedRoute>} />

      {/* Company routes */}
      <Route path="/company" element={<ProtectedRoute allowedRoles={['company', 'admin']}><CompanyDashboard /></ProtectedRoute>} />
      <Route path="/company/threats" element={<ProtectedRoute allowedRoles={['company', 'admin']}><CompanyDashboard /></ProtectedRoute>} />
      <Route path="/company/blocked" element={<ProtectedRoute allowedRoles={['company', 'admin']}><CompanyDashboard /></ProtectedRoute>} />
      <Route path="/company/validation" element={<ProtectedRoute allowedRoles={['company', 'admin']}><ValidationLab /></ProtectedRoute>} />

      {/* Admin routes */}
      <Route path="/admin" element={<ProtectedRoute allowedRoles={['admin']}><AdminDashboard /></ProtectedRoute>} />
      <Route path="/admin/logs" element={<ProtectedRoute allowedRoles={['admin']}><AdminDashboard /></ProtectedRoute>} />
      <Route path="/admin/honeypot" element={<ProtectedRoute allowedRoles={['admin']}><AdminDashboard /></ProtectedRoute>} />
      <Route path="/admin/ips" element={<ProtectedRoute allowedRoles={['admin']}><AdminDashboard /></ProtectedRoute>} />

      {/* Default */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <ThemeToggleBtn />
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}

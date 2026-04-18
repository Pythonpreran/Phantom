/**
 * PHANTOM — Auth Hook & Context
 */

import { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../utils/api';

const AuthContext = createContext(null);

/**
 * Decode JWT payload without verification (client-side only for exp check).
 */
function decodeTokenPayload(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(base64));
  } catch {
    return null;
  }
}

/**
 * Check if a JWT token is still valid (not expired).
 */
function isTokenValid(token) {
  if (!token) return false;
  const payload = decodeTokenPayload(token);
  if (!payload || !payload.exp) return false;
  // Add 30s buffer to account for clock skew
  return payload.exp * 1000 > Date.now() + 30000;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('phantom_user');
    const token = localStorage.getItem('phantom_token');
    // Validate token on initial load — clear if expired
    if (stored && token && isTokenValid(token)) {
      return JSON.parse(stored);
    }
    // Token missing or expired — clear everything
    localStorage.removeItem('phantom_token');
    localStorage.removeItem('phantom_user');
    return null;
  });
  const [loading, setLoading] = useState(false);

  const login = async (email, password) => {
    setLoading(true);
    try {
      const data = await api('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      const userData = {
        id: data.user_id,
        username: data.username,
        role: data.role,
        token: data.access_token,
      };

      localStorage.setItem('phantom_token', data.access_token);
      localStorage.setItem('phantom_user', JSON.stringify(userData));
      setUser(userData);
      return userData;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email, username, password, role, companyName) => {
    setLoading(true);
    try {
      const data = await api('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, username, password, role, company_name: companyName }),
      });

      const userData = {
        id: data.user_id,
        username: data.username,
        role: data.role,
        token: data.access_token,
      };

      localStorage.setItem('phantom_token', data.access_token);
      localStorage.setItem('phantom_user', JSON.stringify(userData));
      setUser(userData);
      return userData;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('phantom_token');
    localStorage.removeItem('phantom_user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

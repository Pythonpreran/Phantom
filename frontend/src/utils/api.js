/**
 * PHANTOM — API Utility
 */

const API_BASE = '';

// Grace period: don't auto-logout within 5 seconds of page load
// This prevents race conditions on initial data fetches
const PAGE_LOAD_TIME = Date.now();
const AUTH_GRACE_PERIOD_MS = 5000;

// Track if we're already in the process of logging out to avoid loops
let isLoggingOut = false;

function getToken() {
  return localStorage.getItem('phantom_token');
}

export async function api(endpoint, options = {}, suppressAutoLogout = false) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  let res;
  try {
    res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });
  } catch (err) {
    throw new Error('Network error — server may be unavailable');
  }

  // Auto-logout on 401 for authenticated routes only
  // Never logout for login/register endpoints
  // Never logout during grace period after page load (prevents race conditions)
  const isAuthEndpoint = endpoint.includes('/auth/login') || endpoint.includes('/auth/register');
  const inGracePeriod = (Date.now() - PAGE_LOAD_TIME) < AUTH_GRACE_PERIOD_MS;

  if (res.status === 401 && !isAuthEndpoint && !suppressAutoLogout && !inGracePeriod && !isLoggingOut) {
    // Only clear auth if we actually had a token (expired/invalid session)
    if (token) {
      isLoggingOut = true;
      localStorage.removeItem('phantom_token');
      localStorage.removeItem('phantom_user');
      // Defer redirect slightly to let current rendering finish
      setTimeout(() => {
        isLoggingOut = false;
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }, 500);
    }
    throw new Error('Session expired. Please log in again.');
  }

  let data;
  try {
    data = await res.json();
  } catch {
    throw new Error(`Server returned ${res.status}`);
  }

  if (!res.ok) {
    throw new Error(data.detail || 'Request failed');
  }

  return data;
}

export function getWsUrl() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws`;
}

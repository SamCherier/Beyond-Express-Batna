import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import Cookies from 'js-cookie';

const AuthContext = createContext(null);

const API_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${API_URL}/api`;
const SESSION_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes
const WARNING_BEFORE_MS = 2 * 60 * 1000;   // warn 2 min before

function getAuthHeader() {
  const token = localStorage.getItem('auth_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sessionWarning, setSessionWarning] = useState(false);
  const timeoutRef = useRef(null);
  const warningRef = useRef(null);

  useEffect(() => {
    checkAuth();
    processGoogleSession();
  }, []);

  // ── Session inactivity timeout ──
  const resetInactivityTimer = useCallback(() => {
    setSessionWarning(false);
    if (warningRef.current) clearTimeout(warningRef.current);
    if (timeoutRef.current) clearTimeout(timeoutRef.current);

    warningRef.current = setTimeout(() => {
      setSessionWarning(true);
    }, SESSION_TIMEOUT_MS - WARNING_BEFORE_MS);

    timeoutRef.current = setTimeout(() => {
      forceLogout();
    }, SESSION_TIMEOUT_MS);
  }, []);

  useEffect(() => {
    if (!user) return;
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart', 'mousemove'];
    const handler = () => resetInactivityTimer();
    events.forEach(e => document.addEventListener(e, handler, { passive: true }));
    resetInactivityTimer();
    return () => {
      events.forEach(e => document.removeEventListener(e, handler));
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (warningRef.current) clearTimeout(warningRef.current);
    };
  }, [user, resetInactivityTimer]);

  const processGoogleSession = async () => {
    const hash = window.location.hash;
    if (hash && hash.includes('session_id')) {
      const params = new URLSearchParams(hash.substring(1));
      const sessionId = params.get('session_id');
      if (sessionId) {
        try {
          const response = await axios.post(
            `${API}/auth/google-session`, {},
            { headers: { 'X-Session-ID': sessionId }, withCredentials: true }
          );
          setUser(response.data.user);
          window.history.replaceState({}, document.title, window.location.pathname);
        } catch (error) {
          console.error('Google auth error:', error);
        }
      }
    }
  };

  const checkAuth = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        withCredentials: true,
        headers: getAuthHeader(),
      });
      setUser(response.data);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password }, { withCredentials: true });
    setUser(response.data.user);
    if (response.data.access_token) {
      localStorage.setItem('auth_token', response.data.access_token);
    }
    return response.data;
  };

  const register = async (email, password, name, role) => {
    const response = await axios.post(`${API}/auth/register`, { email, password, name, role });
    return response.data;
  };

  const loginWithGoogle = () => {
    const redirectUrl = encodeURIComponent(`${window.location.origin}/dashboard`);
    window.location.href = `https://auth.emergentagent.com/?redirect=${redirectUrl}`;
  };

  // ── Force logout: nuclear cleanup ──
  const forceLogout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, {
        withCredentials: true,
        headers: getAuthHeader(),
      });
    } catch { /* ignore - we're logging out anyway */ }

    setUser(null);

    // Clear all storage
    localStorage.clear();
    sessionStorage.clear();

    // Clear all cookies
    document.cookie.split(';').forEach(c => {
      const name = c.split('=')[0].trim();
      document.cookie = `${name}=;expires=${new Date(0).toUTCString()};path=/`;
    });
    Cookies.remove('session_token');

    // Clear IndexedDB
    try {
      if (window.indexedDB?.databases) {
        const dbs = await window.indexedDB.databases();
        dbs.forEach(d => window.indexedDB.deleteDatabase(d.name));
      }
    } catch { /* ok */ }

    // Clear Cache API
    try {
      const cacheNames = await caches.keys();
      await Promise.all(cacheNames.map(n => caches.delete(n)));
    } catch { /* ok */ }

    window.location.href = '/login?t=' + Date.now();
  };

  // ── Logout from all devices ──
  const logoutAllDevices = async () => {
    try {
      await axios.post(`${API}/auth/logout-all`, {}, {
        withCredentials: true,
        headers: getAuthHeader(),
      });
    } catch { /* ignore */ }
    await forceLogout();
  };

  const logout = forceLogout;

  const updateProfile = async (data) => {
    const response = await axios.patch(`${API}/users/me`, data, {
      withCredentials: true,
      headers: getAuthHeader(),
    });
    setUser(response.data);
    return response.data;
  };

  return (
    <AuthContext.Provider value={{
      user, loading, login, register, loginWithGoogle,
      logout, forceLogout, logoutAllDevices,
      updateProfile, checkAuth, sessionWarning, setSessionWarning,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

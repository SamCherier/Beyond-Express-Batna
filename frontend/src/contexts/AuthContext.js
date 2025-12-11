import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import Cookies from 'js-cookie';

const AuthContext = createContext(null);

const API_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${API_URL}/api`;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
    processGoogleSession();
  }, []);

  const processGoogleSession = async () => {
    const hash = window.location.hash;
    if (hash && hash.includes('session_id')) {
      const params = new URLSearchParams(hash.substring(1));
      const sessionId = params.get('session_id');
      
      if (sessionId) {
        try {
          const response = await axios.post(
            `${API}/auth/google-session`,
            {},
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
      const response = await axios.get(`${API}/auth/me`, { withCredentials: true });
      setUser(response.data);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password }, { withCredentials: true });
    setUser(response.data.user);
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

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Force clear all auth state
      setUser(null);
      Cookies.remove('session_token');
      localStorage.clear(); // Clear any cached data
      sessionStorage.clear();
      
      // Force redirect to login
      window.location.href = '/login';
    }
  };

  const updateProfile = async (data) => {
    const response = await axios.patch(`${API}/users/me`, data, { withCredentials: true });
    setUser(response.data);
    return response.data;
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, loginWithGoogle, logout, updateProfile, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
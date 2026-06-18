import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const API_BASE = '/api';

  const storeTokens = (access, refresh) => {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  };

  const clearTokens = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  };

  const getAccessToken = () => localStorage.getItem('access_token');

  const fetchProfile = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return null;
    }
    try {
      const res = await fetch(`${API_BASE}/auth/profile/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
        setLoading(false);
        return data;
      } else {
        // Token might be expired - try refresh
        const refreshed = await tryRefresh();
        if (refreshed) {
          const res2 = await fetch(`${API_BASE}/auth/profile/`, {
            headers: { Authorization: `Bearer ${getAccessToken()}` },
          });
          if (res2.ok) {
            const data = await res2.json();
            setUser(data);
            setLoading(false);
            return data;
          }
        }
        clearTokens();
        setUser(null);
        setLoading(false);
        return null;
      }
    } catch {
      setUser(null);
      setLoading(false);
      return null;
    }
  }, []);

  const tryRefresh = async () => {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) return false;
    try {
      const res = await fetch(`${API_BASE}/auth/login/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      });
      if (res.ok) {
        const data = await res.json();
        storeTokens(data.access, data.refresh || refresh);
        return true;
      }
    } catch {}
    return false;
  };

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const login = async (username, password) => {
    const res = await fetch(`${API_BASE}/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Login failed');
    storeTokens(data.access, data.refresh);
    setUser(data.user);
    return data;
  };

  const register = async (formData) => {
    const res = await fetch(`${API_BASE}/auth/register/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });
    const data = await res.json();
    if (!res.ok) {
      const msg = typeof data === 'object' ? Object.values(data).flat().join(', ') : 'Registration failed';
      throw new Error(msg);
    }
    storeTokens(data.access, data.refresh);
    setUser(data.user);
    return data;
  };

  const logout = async () => {
    const refresh = localStorage.getItem('refresh_token');
    try {
      await fetch(`${API_BASE}/auth/logout/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getAccessToken()}`,
        },
        body: JSON.stringify({ refresh }),
      });
    } catch {}
    clearTokens();
    setUser(null);
  };

  const isAuthenticated = !!user;
  const isCouncillor = user?.profile?.role === 'councillor';
  const isAdmin = user?.profile?.role === 'admin';

  return (
    <AuthContext.Provider value={{
      user, loading, login, register, logout, fetchProfile,
      isAuthenticated, isCouncillor, isAdmin,
      getAccessToken,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export default AuthContext;

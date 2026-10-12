import { useCallback, useEffect, useState } from 'react';
import { setAuthToken } from '../api/client';
import * as authApi from '../api/auth';
import { AuthContext } from './AuthContext';

const TOKEN_KEY = 'tms-token';

/**
 * Holds auth state. The token is kept in memory (via the API client) and also
 * mirrored to sessionStorage so a page refresh can re-validate it with a
 * /auth/me call rather than forcing a re-login.
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On load: if we have a stored token, verify it via /auth/me.
  useEffect(() => {
    let cancelled = false;

    async function restore() {
      const stored = sessionStorage.getItem(TOKEN_KEY);
      if (stored) {
        setAuthToken(stored);
        try {
          const current = await authApi.me();
          if (!cancelled) setUser(current);
        } catch {
          setAuthToken(null);
          sessionStorage.removeItem(TOKEN_KEY);
        }
      }
      if (!cancelled) setLoading(false);
    }

    restore();
    return () => { cancelled = true; };
  }, []);

  const login = useCallback(async (email, password) => {
    const { access_token, user: loggedIn } = await authApi.login(email, password);
    setAuthToken(access_token);
    sessionStorage.setItem(TOKEN_KEY, access_token);
    setUser(loggedIn);
    return loggedIn;
  }, []);

  const logout = useCallback(() => {
    setAuthToken(null);
    sessionStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

import { createContext, ReactNode, useContext, useEffect, useState } from 'react';
import { getStatus, login as apiLogin, logout as apiLogout } from '../lib/api';

type AuthContextValue = {
  authenticated: boolean;
  loading: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getStatus().then(response => {
      setAuthenticated(response.authenticated);
      setLoading(false);
    }).catch(() => {
      setAuthenticated(false);
      setLoading(false);
    });
  }, []);

  const login = async (username: string, password: string) => {
    const response = await apiLogin(username, password);
    if (response.success) {
      setAuthenticated(true);
      return true;
    }
    return false;
  };

  const logout = async () => {
    await apiLogout();
    setAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ authenticated, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

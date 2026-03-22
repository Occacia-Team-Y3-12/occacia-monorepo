'use client';

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import { customerAuthService } from '@/services/customer/authServices';

interface AuthUser {
  id: string;
  email: string;
  username: string;
  fullName: string;
}

interface AuthContextValue {
  isAuthenticated: boolean;
  user: AuthUser | null;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  isAuthenticated: false,
  user: null,
  logout: () => {},
});

export function CustomerAuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    setIsAuthenticated(customerAuthService.isAuthenticated());
    setUser(customerAuthService.getUser());
  }, []);

  const logout = useCallback(() => {
    customerAuthService.logout();
    setIsAuthenticated(false);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useCustomerAuth() {
  return useContext(AuthContext);
}

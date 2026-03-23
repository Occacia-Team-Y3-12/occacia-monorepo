'use client';

import { createContext, useContext, useState, useEffect, useCallback, createElement } from 'react';
import type { ReactNode } from 'react';
import { customerAuthService } from '@/services/customer/authServices';
import type { LoginResponse } from '@/types/customer/auth';

interface AuthUser {
  id: string;
  email: string;
  username?: string;
  fullName?: string;
  role?: string;
  status?: string;
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

const normalizeAuthUser = (
  user: NonNullable<LoginResponse['user']> | null
): AuthUser | null => {
  if (!user) {
    return null;
  }

  return {
    id: user.id || user.userId || user.email,
    email: user.email,
    username: user.username,
    fullName: user.fullName,
    role: user.role,
    status: user.status,
  };
};

export function CustomerAuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    setIsAuthenticated(customerAuthService.isAuthenticated());
    setUser(normalizeAuthUser(customerAuthService.getUser()));
  }, []);

  const logout = useCallback(() => {
    customerAuthService.logout();
    setIsAuthenticated(false);
    setUser(null);
  }, []);

  return createElement(
    AuthContext.Provider,
    { value: { isAuthenticated, user, logout } },
    children
  );
}

export function useCustomerAuth() {
  return useContext(AuthContext);
}

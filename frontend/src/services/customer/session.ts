import type { LoginResponse } from '@/types/customer/auth';

const CUSTOMER_TOKEN_COOKIE = 'customerToken';
const CUSTOMER_AUTH_FLAG = 'customerAuthVerified';

const setAuthCookie = (token: string) => {
  if (typeof document === 'undefined') return;

  document.cookie = `${CUSTOMER_TOKEN_COOKIE}=${encodeURIComponent(token)}; Path=/; Max-Age=604800; SameSite=Lax`;
};

const clearAuthCookie = () => {
  if (typeof document === 'undefined') return;

  document.cookie = `${CUSTOMER_TOKEN_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax`;
};

const getAuthCookie = (): string | null => {
  if (typeof document === 'undefined') return null;

  const match = document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${CUSTOMER_TOKEN_COOKIE}=`));

  if (!match) {
    return null;
  }

  const value = match.split('=').slice(1).join('=');
  return value ? decodeURIComponent(value) : null;
};

export const persistCustomerSession = (
  accessToken?: string,
  refreshToken?: string,
  user?: LoginResponse['user']
) => {
  if (typeof window === 'undefined') {
    return;
  }

  if (accessToken) {
    localStorage.setItem('customerToken', accessToken);
    localStorage.setItem('accessToken', accessToken);
    sessionStorage.setItem('customerToken', accessToken);
    sessionStorage.setItem('accessToken', accessToken);
    setAuthCookie(accessToken);
  }

  if (refreshToken) {
    localStorage.setItem('customerRefreshToken', refreshToken);
    sessionStorage.setItem('customerRefreshToken', refreshToken);
  }

  if (user) {
    localStorage.setItem('customerUser', JSON.stringify(user));
    sessionStorage.setItem('customerUser', JSON.stringify(user));
  }

  if (accessToken || user) {
    localStorage.setItem(CUSTOMER_AUTH_FLAG, '1');
    sessionStorage.setItem(CUSTOMER_AUTH_FLAG, '1');
  }
};

export const logoutCustomerSession = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('customerToken');
    localStorage.removeItem('accessToken');
    localStorage.removeItem('customerRefreshToken');
    localStorage.removeItem('customerUser');
    sessionStorage.removeItem('customerToken');
    sessionStorage.removeItem('accessToken');
    sessionStorage.removeItem('customerRefreshToken');
    sessionStorage.removeItem('customerUser');
    localStorage.removeItem(CUSTOMER_AUTH_FLAG);
    sessionStorage.removeItem(CUSTOMER_AUTH_FLAG);
  }

  clearAuthCookie();
};

export const getStoredCustomerToken = (): string | null => {
  if (typeof window === 'undefined') return null;

  return (
    localStorage.getItem('customerToken') ||
    localStorage.getItem('accessToken') ||
    sessionStorage.getItem('customerToken') ||
    sessionStorage.getItem('accessToken') ||
    getAuthCookie()
  );
};

export const getStoredCustomerRefreshToken = (): string | null => {
  if (typeof window === 'undefined') return null;

  return (
    localStorage.getItem('customerRefreshToken') ||
    sessionStorage.getItem('customerRefreshToken')
  );
};

export const getStoredCustomerUser = (): NonNullable<LoginResponse['user']> | null => {
  if (typeof window === 'undefined') return null;

  const stored =
    localStorage.getItem('customerUser') ||
    sessionStorage.getItem('customerUser');

  if (!stored) {
    return null;
  }

  try {
    return JSON.parse(stored) as NonNullable<LoginResponse['user']>;
  } catch {
    return null;
  }
};

export const isCustomerAuthenticated = (): boolean => {
  if (typeof window === 'undefined') return false;

  return Boolean(
    getStoredCustomerToken() ||
      localStorage.getItem(CUSTOMER_AUTH_FLAG) ||
      sessionStorage.getItem(CUSTOMER_AUTH_FLAG)
  );
};

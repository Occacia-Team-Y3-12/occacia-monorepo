import type { AxiosInstance } from 'axios';

import { ROUTES } from '@/lib/routes';
import { logoutCustomerSession } from '@/services/customer/authService.shared';
import { clearVendorSession } from '@/services/vendor/authService.shared';

const redirectTo = (path: string) => {
  if (typeof window !== 'undefined') {
    window.location.href = path;
  }
};

export const handleCustomerUnauthorized = () => {
  logoutCustomerSession();
  redirectTo(ROUTES.CUSTOMER.LOGIN);
};

export const handleVendorUnauthorized = () => {
  clearVendorSession();
  redirectTo(ROUTES.VENDOR.LOGIN);
};

export const attachCustomer401Interceptor = (api: AxiosInstance) => {
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        handleCustomerUnauthorized();
      }
      return Promise.reject(error);
    }
  );
};

export const attachVendor401Interceptor = (api: AxiosInstance) => {
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        handleVendorUnauthorized();
      }
      return Promise.reject(error);
    }
  );
};

export const handleCustomerFetchUnauthorized = (response: Response): boolean => {
  if (response.status === 401) {
    handleCustomerUnauthorized();
    return true;
  }
  return false;
};

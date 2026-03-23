'use client';

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { ROUTES } from '@/lib/routes';

type ApiErrorLike = {
  response?: {
    status?: number;
    data?: {
      detail?: string;
      message?: string;
    };
  };
  message?: string;
};

export const useVendorSessionGuard = () => {
  const router = useRouter();

  const getStatusCode = useCallback((error: unknown) => {
    const apiError = error as ApiErrorLike;
    return apiError?.response?.status;
  }, []);

  const getErrorMessage = useCallback((error: unknown, fallback: string) => {
    const apiError = error as ApiErrorLike;
    return (
      apiError?.response?.data?.detail ||
      apiError?.response?.data?.message ||
      apiError?.message ||
      fallback
    );
  }, []);

  const handleUnauthorized = useCallback(
    (error: unknown, message = 'Session expired. Please login again.') => {
      if (getStatusCode(error) !== 401) {
        return false;
      }
      toast.error(message);
      router.push(ROUTES.VENDOR.LOGIN);
      return true;
    },
    [getStatusCode, router]
  );

  return {
    getStatusCode,
    getErrorMessage,
    handleUnauthorized,
  };
};

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/routes';
import { vendorAuthService } from '@/services/vendor/authService';

export const useVendorForgotPassword = () => {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email.trim()) {
      setError('Please enter your email address.');
      return;
    }

    setLoading(true);
    try {
      const result = await vendorAuthService.forgotPassword(email);
      if (result.ok) {
        setSuccess(true);
      } else {
        setError('Unable to send reset link. Please try again.');
      }
    } catch {
      setError('Unable to send reset link. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const goToLogin = () => router.push(ROUTES.VENDOR.LOGIN);

  return {
    email,
    loading,
    success,
    error,
    setEmail,
    handleSubmit,
    goToLogin,
  };
};

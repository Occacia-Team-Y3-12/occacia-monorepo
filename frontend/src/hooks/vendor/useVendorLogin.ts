import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/routes';
import { vendorAuthService } from '@/services/vendor/authService';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const useVendorLogin = () => {
  const router = useRouter();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const email = formData.email.trim();

    if (!email || !formData.password.trim()) {
      setError('Email and password are required.');
      setLoading(false);
      return;
    }

    if (!EMAIL_PATTERN.test(email)) {
      setError('Enter a valid email address.');
      setLoading(false);
      return;
    }

    try {
      const result = await vendorAuthService.login({
        email,
        password: formData.password,
      });
      if (result.ok) {
        router.replace(ROUTES.VENDOR.DASHBOARD);
      } else {
        setError(result.message || 'Invalid credentials. Please try again.');
      }
    } catch (error) {
      setError(
        error instanceof Error && error.message
          ? error.message
          : 'Login failed. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return {
    formData,
    loading,
    error,
    handleChange,
    handleSubmit,
  };
};

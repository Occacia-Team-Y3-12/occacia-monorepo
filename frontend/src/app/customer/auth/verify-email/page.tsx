// src/app/(customer)/auth/verify-email/page.tsx
'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import Button from '@/components/ui/Button';
import { customerAuthService } from '@/services/customer/authServices';

type VerificationStatus = 'loading' | 'success' | 'error' | 'already-verified';

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<VerificationStatus>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (!token) {
      setStatus('error');
      setMessage('Invalid verification link. No token provided.');
      return;
    }

    verifyEmail(token);
  }, [searchParams]);

  const verifyEmail = async (token: string) => {
    try {
      const response = await customerAuthService.verifyEmail(token);
      setStatus('success');
      setMessage(response.message || 'Your email has been verified successfully!');
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Verification failed';
      
      if (error.response?.status === 410 || errorMessage.includes('expired')) {
        setStatus('error');
        setMessage('This verification link has expired or is invalid.');
      } else if (errorMessage.includes('already verified')) {
        setStatus('already-verified');
        setMessage('This account is already verified.');
      } else {
        setStatus('error');
        setMessage(errorMessage);
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 px-4">
      <div className="max-w-md w-full bg-white rounded-3xl shadow-xl p-8 text-center">
        {/* Loading State */}
        {status === 'loading' && (
          <>
            <Loader2 className="w-20 h-20 text-blue-600 animate-spin mx-auto mb-6" />
            <h1 className="text-3xl font-bold text-gray-900 mb-3">
              Verifying your email...
            </h1>
            <p className="text-gray-600">Please wait a moment.</p>
          </>
        )}

        {/* Success State */}
        {status === 'success' && (
          <>
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-12 h-12 text-green-600" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-3">
              Email Verified!
            </h1>
            <p className="text-gray-600 mb-8">{message}</p>
            <Button
              onClick={() => router.push('/auth/login')}
              variant="primary"
              className="w-full"
            >
              Go to Login
            </Button>
          </>
        )}

        {/* Already Verified State */}
        {status === 'already-verified' && (
          <>
            <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-12 h-12 text-blue-600" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-3">
              Already Verified
            </h1>
            <p className="text-gray-600 mb-8">{message}</p>
            <Button
              onClick={() => router.push('/auth/login')}
              variant="primary"
              className="w-full"
            >
              Go to Login
            </Button>
          </>
        )}

        {/* Error State */}
        {status === 'error' && (
          <>
            <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <XCircle className="w-12 h-12 text-red-600" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-3">
              Verification Failed
            </h1>
            <p className="text-gray-600 mb-8">{message}</p>
            <div className="space-y-3">
              <Button
                onClick={() => router.push('/auth/login')}
                variant="primary"
                className="w-full"
              >
                Go to Login
              </Button>
              <Button
                onClick={() => router.push('/auth/register')}
                variant="outline"
                className="w-full"
              >
                Register Again
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}
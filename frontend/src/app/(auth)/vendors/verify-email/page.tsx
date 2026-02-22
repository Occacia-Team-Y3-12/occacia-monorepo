'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Image from 'next/image';

export default function VerifyEmail() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'pending' | 'success' | 'error'>('pending');

  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      fetch(`/api/v1/auth/verify-email?token=${token}`)
        .then(res => res.ok ? setStatus('success') : setStatus('error'))
        .catch(() => setStatus('error'));
    }
  }, [searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden p-4">
      <Image src="/images/background.png" alt="Background" fill className="object-cover" priority/>

      <div className="bg-white rounded-3xl shadow-2xl p-12 max-w-md w-full relative z-10 text-center">
        <div className="mb-8 flex justify-center">
          <Image src="/images/logo.png" alt="Occacia Logo" width={120} height={120} priority />
        </div>
        
        <h1 className="text-3xl font-bold text-[#2c3e50] mb-4">Email Verification</h1>
        
        {status === 'pending' && (
          <div>
            <p className="text-[#5a6c7d] mb-6">Please check your email and click the verification link.</p>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#1e88e5] mx-auto"></div>
          </div>
        )}
        
        {status === 'success' && (
          <div>
            <p className="text-green-600 mb-4">✓ Email verified successfully!</p>
            <p className="text-[#5a6c7d]">Your account is now pending admin approval. You will be notified once approved.</p>
          </div>
        )}
        
        {status === 'error' && (
          <div>
            <p className="text-red-600 mb-4">✗ Verification failed</p>
            <p className="text-[#5a6c7d]">The verification link is invalid or expired.</p>
          </div>
        )}
      </div>
    </div>
  );
}

'use client';

import Image from 'next/image';
import Link from 'next/link';
import { ROUTES } from '@/lib/routes';

export default function PendingApproval() {
  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden p-4">
      <Image src="/images/background.png" alt="Background" fill className="object-cover" priority />

      <div className="bg-white rounded-3xl shadow-2xl p-6 md:p-12 max-w-md w-full relative z-10 text-center">
        <div className="mb-6 md:mb-8 flex justify-center">
          <Image src="/images/logo.png" alt="Occacia Logo" width={80} height={80} priority className="md:w-[120px] md:h-[120px]" />
        </div>

        <h1 className="text-2xl md:text-3xl font-bold text-[#2c3e50] mb-3 md:mb-4">Pending Approval</h1>

        <div className="mb-6">
          <div className="w-12 h-12 md:w-16 md:h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-3 md:mb-4">
            <svg className="w-6 h-6 md:w-8 md:h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-[#5a6c7d] mb-3 md:mb-4 text-sm md:text-base">
            Your vendor account is currently pending admin approval.
          </p>
          <p className="text-[#5a6c7d] text-sm">
            You will receive an email notification once your account has been reviewed and approved.
          </p>
        </div>

        <Link
          href={ROUTES.VENDOR.LOGIN}
          className="inline-block bg-[#1565c0] hover:bg-[#0d47a1] text-white font-medium px-4 md:px-6 py-2 md:py-3 rounded-lg transition-colors duration-200 text-sm md:text-base"
        >
          Back to Login
        </Link>

      </div>
    </div>
  );
}

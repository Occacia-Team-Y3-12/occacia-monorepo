'use client';

import { Suspense } from 'react';
import VendorResetPasswordForm from '@/components/vendor/auth/VendorResetPasswordForm';

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <VendorResetPasswordForm />
    </Suspense>
  );
}

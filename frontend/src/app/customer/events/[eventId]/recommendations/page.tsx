'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/routes';

export default function RecommendationsRedirect() {
  const params = useParams<{ eventId: string }>();
  const router = useRouter();

  useEffect(() => {
    router.replace(ROUTES.CUSTOMER.EVENT_PACKAGES(params?.eventId || ''));
  }, [params?.eventId, router]);

  return null;
}

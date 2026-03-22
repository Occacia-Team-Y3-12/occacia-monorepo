'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/routes';

export default function RecommendationsPage() {
  const params = useParams<{ eventId: string }>();
  const router = useRouter();
  const eventId = params?.eventId || '';

  useEffect(() => {
    if (!eventId) {
      return;
    }

    const timer = window.setTimeout(() => {
      router.replace(ROUTES.CUSTOMER.EVENT_PACKAGES(eventId));
    }, 400);

    return () => window.clearTimeout(timer);
  }, [eventId, router]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#F7F7FA]">
      <h1 className="text-4xl font-bold text-gray-900 mb-3">Occacia</h1>
      <p className="text-gray-500 text-lg mb-8">Preparing your recommendation packages.</p>

      <div className="flex items-center gap-3">
        <button
          onClick={() => router.replace(ROUTES.CUSTOMER.EVENT_PACKAGES(eventId))}
          className="px-6 py-3 rounded-xl bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold text-sm transition"
        >
          Continue
        </button>
      </div>
    </div>
  );
}

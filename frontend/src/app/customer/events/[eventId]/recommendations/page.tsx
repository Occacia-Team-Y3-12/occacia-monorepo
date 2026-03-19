'use client';

import { useParams, useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/routes';

const MOCK_PACKAGE_ID = 'pkg-recommended';

export default function RecommendationsPage() {
  const params = useParams<{ eventId: string }>();
  const router = useRouter();
  const eventId = params?.eventId || '';

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#F7F7FA]">
      <h1 className="text-4xl font-bold text-gray-900 mb-3">Occacia</h1>
      <p className="text-gray-500 text-lg mb-8">Plan meaningful moments, effortlessly.</p>

      <div className="flex items-center gap-3">
        <button
          onClick={() => router.push(ROUTES.CUSTOMER.EVENT_PACKAGES(eventId))}
          className="px-6 py-3 rounded-xl bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold text-sm transition"
        >
          View Recommendations
        </button>
        <button
          onClick={() => router.push(ROUTES.CUSTOMER.EVENT_PACKAGE_CUSTOMIZE(eventId, MOCK_PACKAGE_ID))}
          className="px-6 py-3 rounded-xl border border-gray-300 bg-white hover:bg-gray-50 text-gray-800 font-semibold text-sm transition"
        >
          Customize Package
        </button>
      </div>
    </div>
  );
}

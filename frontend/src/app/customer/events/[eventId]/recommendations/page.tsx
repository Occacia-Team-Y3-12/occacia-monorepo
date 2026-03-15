'use client';

import { useParams, useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/routes';

export default function CustomerEventRecommendationsPage() {
  const params = useParams<{ eventId: string }>();
  const router = useRouter();
  const eventId = params?.eventId;

  return (
    <section className="rounded-2xl border border-[#E4E8F2] bg-white p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#8B98B2]">Recommendations</p>
      <h1 className="mt-2 text-3xl font-bold text-[#141A2A]">Ready For Recommendation Generation</h1>
      <p className="mt-3 max-w-[760px] text-sm text-[#5C6780]">
        Event {eventId ? `(${eventId}) ` : ''}has been confirmed with schedule, reminders, and task context.
        Continue to recommendation generation or return to events.
      </p>

      <div className="mt-6 flex flex-wrap gap-3">
        <button
          onClick={() => router.push(ROUTES.CUSTOMER.EVENTS)}
          className="h-11 rounded-xl border border-[#D4DCEB] bg-[#F7F9FD] px-4 text-sm font-semibold text-[#2E3C58]"
        >
          Back to Events
        </button>
        <button
          onClick={() => router.push(ROUTES.CUSTOMER.EVENT_CHAT(eventId || ''))}
          className="h-11 rounded-xl bg-[#0F4FB7] px-4 text-sm font-semibold text-white"
        >
          Re-open Event Chat
        </button>
      </div>
    </section>
  );
}

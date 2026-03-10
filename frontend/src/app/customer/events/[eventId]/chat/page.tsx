'use client';

import { useParams, useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/routes';

export default function CustomerEventChatPage() {
  const params = useParams<{ eventId: string }>();
  const router = useRouter();
  const eventId = params?.eventId;

  return (
    <section className="mx-auto w-full max-w-[1040px] rounded-2xl border border-[#E4E8F2] bg-white p-6">
      <p className="text-xs font-medium text-[#8A90A1]">Events &gt; Event Chat</p>
      <h1 className="mt-2 text-3xl font-bold text-[#141A2A]">Event Chat</h1>
      <p className="mt-3 text-sm text-[#677086]">
        Draft event created successfully. Continue planning in chat for event id:
        <span className="ml-1 font-semibold text-[#1A2A60]">{eventId}</span>
      </p>

      <div className="mt-6 rounded-xl border border-[#E4E8F2] bg-[#F8F9FC] p-4 text-sm text-[#5D667E]">
        This is a starter chat screen for UC-13 handoff.
      </div>

      <button
        onClick={() => router.push(ROUTES.CUSTOMER.EVENTS)}
        className="mt-6 h-10 rounded-lg bg-[#2046C9] px-4 text-sm font-semibold text-white"
      >
        Back to Create Event
      </button>
    </section>
  );
}

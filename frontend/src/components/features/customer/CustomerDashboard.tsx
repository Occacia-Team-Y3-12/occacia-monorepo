"use client";

import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { CalendarDays, Cake, Heart } from 'lucide-react';
import { useCustomerDashboard } from '@/hooks/customer/useCustomerDashboard';
import { ROUTES } from '@/lib/routes';

export default function CustomerDashboard() {
  const router = useRouter();
  const { templates } = useCustomerDashboard();

  return (
    <div className="space-y-5 sm:space-y-8">
      <section className="relative overflow-hidden rounded-xl bg-gradient-to-r from-[#0D47A1] to-[#4285F4] px-5 py-6 text-[#FFFFFF] shadow-[0_10px_30px_rgba(13,71,161,0.25)] sm:px-8 sm:py-8 lg:px-10">
        <div className="absolute right-6 top-1 hidden h-[120px] w-[160px] opacity-15 sm:block sm:right-10">
          <svg viewBox="0 0 220 160" className="h-full w-full" fill="none" stroke="currentColor" strokeWidth="8">
            <path d="M55 120 105 20 155 120z" />
            <path d="M170 20c15 5 25 15 30 30" />
            <path d="M150 10c25 8 45 28 53 53" />
          </svg>
        </div>

        <h2 className="text-4xl leading-[1.05] font-extrabold tracking-tight sm:text-[50px]">Welcome back!</h2>
        <p className="mt-3 max-w-[860px] text-base font-medium leading-relaxed text-[#FFFFFF] sm:mt-4 sm:text-[22px]">
          <span className="block">Ready to plan your next event? We&apos;ve updated our vendor lists with top-rated</span>
          <span className="block">local catering and decor services just for you.</span>
        </p>

        <button
          type="button"
          onClick={() => router.push(ROUTES.CUSTOMER.EVENTS_NEW)}
          className="mt-6 inline-flex items-center gap-2 rounded-lg border border-[#CCCCCC] bg-[#FFFFFF] px-4 py-2.5 text-sm font-semibold text-[#0D47A1] sm:mt-8 sm:px-5 sm:py-3"
        >
          <span className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-[#0D47A1]">+</span>
          Start Planning
        </button>
      </section>

      <section>
        <div className="mb-5 flex items-center justify-between">
          <h3 className="text-xl font-bold text-[#0D47A1] sm:text-[28px]">Quick Start Templates</h3>
          <button type="button" className="text-sm font-semibold text-[#4285F4]">View all templates</button>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {templates.map((template) => (
            <button
              type="button"
              key={template.title}
              className="group relative h-[108px] overflow-hidden rounded-2xl text-left sm:h-[120px]"
            >
              <Image
                src={template.image}
                alt={template.title}
                fill
                className="object-cover transition-transform duration-300 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/55 via-black/20 to-transparent" />
              <span className="absolute bottom-3 left-3 text-base font-semibold text-white sm:text-xl">{template.title}</span>
            </button>
          ))}
        </div>
      </section>

      <section>
        <div className="mb-5 flex items-center justify-between">
          <h3 className="text-xl font-bold text-[#0D47A1] sm:text-[28px]">Upcoming Events</h3>
          <button className="inline-flex items-center gap-1 text-sm font-semibold text-[#4285F4]">
            <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 6h18M7 12h10m-7 6h4" />
            </svg>
            Filter
          </button>
        </div>

        <div className="space-y-5">
          <article className="flex flex-col gap-4 rounded-2xl border border-[#EAEAEA] bg-[#FFFFFF] px-4 py-4 shadow-[0_3px_14px_rgba(13,71,161,0.06)] sm:flex-row sm:items-center sm:justify-between sm:px-5">
            <div className="flex items-start gap-3 sm:items-center">
              <span className="inline-flex h-[46px] w-[46px] items-center justify-center rounded-full bg-[#F4F8FA]">
                <Cake className="h-6 w-6 text-[#4285F4]" strokeWidth={2.1} />
              </span>
              <div>
                <h4 className="text-base font-semibold text-[#0D47A1] sm:text-[19px]">Sarah&apos;s 30th Birthday Bash</h4>
                <p className="text-xs text-[#666666] sm:text-sm">Oct 24, 2023   New York, NY</p>
              </div>
            </div>
            <span className="inline-flex w-[96px] items-center justify-center rounded-full bg-[#FAFAFA] px-4 py-1.5 text-[11px] font-semibold text-[#FBBC05]">In 2 days</span>
          </article>

          <article className="flex flex-col gap-4 rounded-2xl border border-[#EAEAEA] bg-[#FFFFFF] px-4 py-4 shadow-[0_3px_14px_rgba(13,71,161,0.06)] sm:flex-row sm:items-center sm:justify-between sm:px-5">
            <div className="flex items-start gap-3 sm:items-center">
              <span className="inline-flex h-[46px] w-[46px] items-center justify-center rounded-full bg-[#F4F8FA]">
                <Heart className="h-6 w-6 text-[#4285F4]" strokeWidth={2.1} />
              </span>
              <div>
                <h4 className="text-base font-semibold text-[#0D47A1] sm:text-[19px]">Annual Wedding Anniversary</h4>
                <p className="text-xs text-[#666666] sm:text-sm">Sep 12, 2023   Paris, France</p>
              </div>
            </div>
            <span className="inline-flex w-[96px] items-center justify-center rounded-full bg-[#F4F8FA] px-4 py-1.5 text-[11px] font-semibold text-[#34A853]">In 20 days</span>
          </article>
        </div>
      </section>

      <section className="pt-1 sm:pt-2">
        <div className="mb-5 flex items-center justify-between">
          <h3 className="text-xl font-bold text-[#0D47A1] sm:text-[28px]">Pending Events</h3>
        </div>

        <div className="flex min-h-[220px] flex-col items-center justify-center rounded-3xl border border-dashed border-[#C9C9C9] bg-[#FAFAFA] px-4 py-6 text-center">
          <button
            type="button"
            onClick={() => router.push(ROUTES.CUSTOMER.EVENTS_NEW)}
            className="inline-flex h-16 w-16 items-center justify-center rounded-full border border-[#EAEAEA] bg-[#F4F8FA] p-1 transition-transform duration-200 hover:scale-105 sm:h-[72px] sm:w-[72px]"
            aria-label="Go to events page"
          >
            <CalendarDays className="h-8 w-8 text-[#4285F4] sm:h-9 sm:w-9" strokeWidth={2.2} />
          </button>
          <h4 className="mt-3 text-2xl font-bold text-[#0D47A1] sm:text-[30px]">No pending events</h4>
          <p className="mt-2 max-w-[410px] text-sm leading-relaxed text-[#666666] sm:text-base">
            You don&apos;t have any new events planned yet. Let&apos;s create something memorable together.
          </p>
        </div>
      </section>
    </div>
  );
}

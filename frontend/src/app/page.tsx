import Image from 'next/image';
import Link from 'next/link';
import { ROUTES } from '@/lib/routes';
import AnimatedBackground from '@/components/landing/AnimatedBackground';

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-gradient-to-br from-[#F4F8FA] via-[#FAFAFA] to-[#FFFFFF]">
      <AnimatedBackground />

      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-8 sm:px-8 sm:py-10 lg:px-12">
        <div className="mb-6 flex flex-col items-center justify-center text-center">
          <Image src="/icons/logo.svg" alt="Occacia Logo" width={108} height={108} priority className="mb-4 h-[108px] w-[108px]" />
          <h1 className="bg-gradient-to-r from-[#0D47A1] via-[#4285F4] to-[#0D47A1] bg-clip-text text-4xl font-bold text-transparent sm:text-5xl">
            Choose Your Portal
          </h1>
          <p className="mt-3 max-w-xl text-base text-[#666666] sm:text-xl">
            Select how you&apos;d like to get started with Occacia Planner
          </p>
          <span className="mt-5 rounded-full border border-[#CCCCCC] bg-[#FFFFFF]/90 px-4 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-[#666666]">
            AI-Powered Platform
          </span>
        </div>

        <section className="mx-auto grid w-full max-w-4xl flex-1 grid-cols-1 gap-6 pb-8 md:grid-cols-2">
          <article className="group flex h-full flex-col rounded-3xl border border-[#EAEAEA] bg-[#FFFFFF]/92 p-6 shadow-[0_16px_38px_-24px_rgba(13,71,161,0.32)] backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_22px_46px_-22px_rgba(13,71,161,0.42)] sm:p-7">
            <div className="relative mb-5 h-1.5 w-full overflow-hidden rounded-full bg-transparent">
              <span className="absolute inset-y-0 right-0 w-0 rounded-full bg-gradient-to-r from-[#4285F4] to-[#0D47A1] opacity-0 group-hover:opacity-100 group-hover:[animation:portalBarSweep_560ms_ease-out_forwards]" />
            </div>
            <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-[#4285F4] to-[#0D47A1] text-[#FFFFFF] shadow-[0_8px_20px_rgba(66,133,244,0.34)]">
              <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
              </svg>
            </div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#4285F4]">Plan Your Occasion</p>
            <h2 className="text-[38px] font-bold leading-[1.05] text-[#0D47A1]">For Customers</h2>
            <p className="mt-3 flex-1 text-[15px] text-[#666666]">
              Discover curated vendors, get AI-powered recommendations, and manage every detail of your dream event effortlessly.
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              <span className="rounded-full border border-[#EAEAEA] bg-[#F4F8FA] px-3 py-1 text-xs font-medium text-[#4285F4]">AI Recommendations</span>
              <span className="rounded-full border border-[#EAEAEA] bg-[#F4F8FA] px-3 py-1 text-xs font-medium text-[#4285F4]">Vendor Discovery</span>
              <span className="rounded-full border border-[#EAEAEA] bg-[#F4F8FA] px-3 py-1 text-xs font-medium text-[#4285F4]">Event Timeline</span>
            </div>
            <div className="mt-6 space-y-3">
              <Link
                href={ROUTES.CUSTOMER.LOGIN}
                className="inline-flex h-11 w-full items-center justify-center rounded-xl bg-gradient-to-r from-[#4285F4] to-[#0D47A1] text-sm font-semibold text-[#FFFFFF] shadow-[0_10px_24px_-10px_rgba(13,71,161,0.5)] transition-all duration-200 hover:brightness-110"
              >
                Login
              </Link>
              <Link
                href="/customer/auth/register"
                className="inline-flex h-11 w-full items-center justify-center rounded-xl border border-[#4285F4] bg-[#FFFFFF] text-sm font-semibold text-[#4285F4] transition-colors hover:bg-[#F4F8FA]"
              >
                Register
              </Link>
            </div>
          </article>

          <article className="group flex h-full flex-col rounded-3xl border border-[#EAEAEA] bg-[#FFFFFF]/92 p-6 shadow-[0_16px_38px_-24px_rgba(13,71,161,0.32)] backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_22px_46px_-22px_rgba(13,71,161,0.42)] sm:p-7">
            <div className="relative mb-5 h-1.5 w-full overflow-hidden rounded-full bg-transparent">
              <span className="absolute inset-y-0 right-0 w-0 rounded-full bg-gradient-to-r from-[#4285F4] to-[#0D47A1] opacity-0 group-hover:opacity-100 group-hover:[animation:portalBarSweep_560ms_ease-out_forwards]" />
            </div>
            <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-[#0D47A1] to-[#4285F4] text-[#FFFFFF] shadow-[0_8px_20px_rgba(13,71,161,0.3)]">
              <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M3 7.5h18v11H3z" />
                <path d="M8 7.5V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2.5M3 12h18" />
              </svg>
            </div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#4285F4]">Grow Your Business</p>
            <h2 className="text-[38px] font-bold leading-[1.05] text-[#0D47A1]">For Vendors</h2>
            <p className="mt-3 flex-1 text-[15px] text-[#666666]">
              List your services, receive bookings, and connect with clients planning their perfect occasions, all powered by AI.
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              <span className="rounded-full border border-[#EAEAEA] bg-[#F4F8FA] px-3 py-1 text-xs font-medium text-[#4285F4]">Manage Bookings</span>
              <span className="rounded-full border border-[#EAEAEA] bg-[#F4F8FA] px-3 py-1 text-xs font-medium text-[#4285F4]">AI Client Matching</span>
              <span className="rounded-full border border-[#EAEAEA] bg-[#F4F8FA] px-3 py-1 text-xs font-medium text-[#4285F4]">Revenue Analytics</span>
            </div>
            <div className="mt-6 space-y-3">
              <Link
                href={ROUTES.VENDOR.LOGIN}
                className="inline-flex h-11 w-full items-center justify-center rounded-xl bg-gradient-to-r from-[#0D47A1] to-[#4285F4] text-sm font-semibold text-[#FFFFFF] shadow-[0_10px_24px_-10px_rgba(13,71,161,0.5)] transition-all duration-200 hover:brightness-105"
              >
                Login
              </Link>
              <Link
                href={ROUTES.VENDOR.REGISTER}
                className="inline-flex h-11 w-full items-center justify-center rounded-xl border border-[#0D47A1] bg-[#FFFFFF] text-sm font-semibold text-[#0D47A1] transition-colors hover:bg-[#F4F8FA]"
              >
                Register
              </Link>
            </div>
          </article>
        </section>

        <footer className="mt-8 pb-1 text-center text-sm text-[#666666]">
          Copyright 2026 Occacia Planner - Powered by AI
        </footer>
      </div>
    </main>
  );
}

'use client';

import { useMemo } from 'react';
import { LayoutDashboard, ShieldCheck, Mail } from 'lucide-react';
import { ROUTES } from '@/lib/routes';
import Link from 'next/link';

const trustedDevices = [
  { device: 'MacBook Pro 16"', location: 'Colombo, LK', lastActive: 'Today • 09:12' },
  { device: 'iPhone 14', location: 'Colombo, LK', lastActive: 'Yesterday • 18:45' },
  { device: 'iPad Air', location: 'Galle, LK', lastActive: '3 days ago' },
];

export default function CustomerSettingsPage() {
  const complianceSummary = useMemo(
    () => ({
      profileCompletion: 92,
      notificationPreference: 'Email + WhatsApp',
      lastPasswordChange: '14 Feb 2026',
    }),
    []
  );

  return (
    <main className="min-h-screen bg-[#F3F5F9] py-10">
      <div className="mx-auto w-full max-w-6xl space-y-8 px-4 sm:px-6">
        <section className="overflow-hidden rounded-[28px] border border-[#E1E6EF] bg-white px-6 py-8 shadow-[0_16px_60px_-28px_rgba(15,23,42,0.35)] sm:px-8 sm:py-10">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#5B6780]">Customer settings</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight text-[#0F1F44] sm:text-4xl">Account & preferences</h1>
              <p className="mt-2 max-w-2xl text-sm leading-relaxed text-[#5B6780]">
                Keep your profile, notification preferences, and calendar in sync across Occacia and your favorite tools.
              </p>
            </div>
            <Link
              href={ROUTES.CUSTOMER.DASHBOARD}
              className="inline-flex items-center gap-2 rounded-full border border-[#D1DBF7] bg-[#F4F6FF] px-5 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[#0F1F44] transition hover:bg-[#E0E8FF]"
            >
              <LayoutDashboard className="h-3.5 w-3.5 text-[#0D47A1]" />
              Back to dashboard
            </Link>
          </div>
          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            <article className="rounded-2xl border border-[#E4E8F1] bg-[#F7F9FF] p-4 text-sm uppercase tracking-[0.2em] text-[#5B6780]">
              Profile completion
              <p className="mt-2 text-2xl font-semibold text-[#0F1F44]">{complianceSummary.profileCompletion}%</p>
            </article>
            <article className="rounded-2xl border border-[#E4E8F1] bg-[#F7F9FF] p-4 text-sm uppercase tracking-[0.2em] text-[#5B6780]">
              Notifications
              <p className="mt-2 text-base font-semibold text-[#0F1F44]">{complianceSummary.notificationPreference}</p>
            </article>
            <article className="rounded-2xl border border-[#E4E8F1] bg-[#F7F9FF] p-4 text-sm uppercase tracking-[0.2em] text-[#5B6780]">
              Password updated
              <p className="mt-2 text-base font-semibold text-[#0F1F44]">{complianceSummary.lastPasswordChange}</p>
            </article>
          </div>
        </section>

        <section className="rounded-[28px] border border-[#DCE4F2] bg-white shadow-[0_18px_48px_-32px_rgba(13,71,161,0.18)]">
          <div className="border-b border-[#EAEAEA] px-6 py-5 sm:px-8">
            <h2 className="text-lg font-semibold text-[#1D273C]">Profile & access</h2>
            <p className="mt-1 text-sm text-[#5B6780]">Update your name, email, payment preferences, and MFA settings.</p>
          </div>
          <div className="divide-y divide-[#EAEAEA] px-6 py-5 sm:px-8">
            <div className="flex flex-col gap-1 py-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-[#0D47A1]">Personal information</p>
                <p className="text-xs text-[#7A87A3]">Name, contact, and linked personas</p>
              </div>
              <button className="text-xs font-semibold uppercase tracking-[0.2em] text-[#0D47A1] hover:underline">Edit</button>
            </div>
            <div className="flex flex-col gap-1 py-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-[#0D47A1]">Security</p>
                <p className="text-xs text-[#7A87A3]">Password, multi-factor, trusted devices</p>
              </div>
              <button className="text-xs font-semibold uppercase tracking-[0.2em] text-[#0D47A1] hover:underline">Manage</button>
            </div>
            <div className="flex flex-col gap-1 py-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-[#0D47A1]">Notifications</p>
                <p className="text-xs text-[#7A87A3]">Email, SMS, and push reminders</p>
              </div>
              <button className="text-xs font-semibold uppercase tracking-[0.2em] text-[#0D47A1] hover:underline">Preferences</button>
            </div>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <article className="rounded-[26px] border border-[#DCE4F2] bg-white p-6 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.18)]">
            <div className="flex items-center gap-3">
              <ShieldCheck className="h-5 w-5 text-[#0D47A1]" />
              <h3 className="text-lg font-semibold text-[#1D273C]">Trusted devices</h3>
            </div>
            <p className="mt-2 text-sm text-[#5B6780]">
              Keep an eye on which machines can access your event planning workspace. Revoke access anytime.
            </p>
            <div className="mt-4 space-y-3">
              {trustedDevices.map((device) => (
                <div key={device.device} className="rounded-2xl border border-[#E1E6EF] bg-[#F7F9FF] px-4 py-3 text-sm">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-[#173B7A]">{device.device}</p>
                      <p className="text-xs text-[#7A87A3]">{device.location}</p>
                    </div>
                    <p className="text-xs text-[#0D47A1]">{device.lastActive}</p>
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-[26px] border border-[#DCE4F2] bg-white p-6 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.18)]">
            <div className="flex items-center gap-3">
              <Mail className="h-5 w-5 text-[#0D47A1]" />
              <h3 className="text-lg font-semibold text-[#1D273C]">Email & notifications</h3>
            </div>
            <p className="mt-2 text-sm text-[#5B6780]">
              Control the types of updates you receive. We can keep you posted about reminders, vendors, and invoices.
            </p>
            <div className="mt-4 space-y-3">
              {['Event updates', 'Calendar reminders', 'Partner program'].map((item) => (
                <div key={item} className="flex items-center justify-between rounded-2xl border border-[#E1E6EF] bg-[#F9FAFF] px-4 py-3 text-sm">
                  <div>
                    <p className="font-semibold text-[#173B7A]">{item}</p>
                    <p className="text-xs text-[#7A87A3]">Enabled</p>
                  </div>
                  <button className="rounded-full border border-[#D7DFEC] bg-white px-4 py-1 text-xs font-semibold text-[#0D47A1]">
                    Manage
                  </button>
                </div>
              ))}
            </div>
          </article>
        </section>
      </div>
    </main>
  );
}

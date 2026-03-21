"use client";

import Image from "next/image";
import Link from "next/link";
import { ROUTES } from "@/lib/routes";
import { useVendorLogin } from "@/hooks/vendor/useVendorLogin";

export default function VendorLoginForm() {
  const { formData, loading, error, handleChange, handleSubmit } =
    useVendorLogin();

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-[#F4F8FA] via-[#FAFAFA] to-[#FFFFFF] p-4">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-24 -left-16 h-72 w-72 rounded-full bg-[#4285F4]/10 blur-3xl" />
        <div className="absolute -bottom-28 -right-20 h-80 w-80 rounded-full bg-[#34A853]/10 blur-3xl" />
        <div className="absolute top-1/3 left-1/2 h-52 w-52 -translate-x-1/2 rounded-full bg-[#FBBC05]/10 blur-3xl" />
      </div>

      <div className="relative z-10 mx-auto flex min-h-[calc(100vh-2rem)] max-w-4xl items-center justify-center">
        <div className="flex w-full flex-col overflow-hidden rounded-3xl border border-[#EAEAEA] bg-[#FFFFFF] shadow-[0_24px_70px_-30px_rgba(13,71,161,0.35)] md:flex-row">
          <div className="w-full md:w-2/5 bg-gradient-to-br from-[#FFFFFF] via-[#F4F8FA] to-[#EAEAEA] p-6 md:p-12 flex flex-col items-center justify-center">
            <div className="mb-4 md:mb-8">
              <Image
                src="/icons/logo.svg"
                alt="Occacia Logo"
                width={120}
                height={120}
                priority
                className="md:w-[180px] md:h-[180px]"
              />
            </div>
            <h1 className="mb-2 text-2xl font-bold text-[#0D47A1] md:text-4xl">
              OCCACIA
            </h1>
            <p className="text-base font-medium tracking-[0.2em] text-[#666666] md:text-lg">
              VENDOR PORTAL
            </p>
            <span className="mt-6 rounded-full border border-[#CCCCCC] bg-[#FFFFFF] px-4 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-[#34A853]">
              Secure Access
            </span>
          </div>

          <div className="w-full md:w-3/5 p-6 md:p-12 flex flex-col justify-center">
            <h2 className="mb-2 text-center text-2xl font-semibold text-[#0D47A1] md:text-3xl">
              VENDOR SIGN IN
            </h2>
            <p className="mb-6 text-center text-sm text-[#666666] md:mb-8">
              Welcome back. Sign in to manage your vendor workspace.
            </p>

            <form onSubmit={handleSubmit} className="space-y-6">
              <input
                type="email"
                name="email"
                placeholder="Email Address"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full rounded-xl border border-[#CCCCCC] bg-[#FAFAFA] px-4 py-3 text-[#666666] placeholder-[#666666]/70 transition-colors duration-200 focus:border-[#4285F4] focus:outline-none focus:ring-4 focus:ring-[#4285F4]/20"
              />

              <input
                type="password"
                name="password"
                placeholder="Password"
                value={formData.password}
                onChange={handleChange}
                required
                className="w-full rounded-xl border border-[#CCCCCC] bg-[#FAFAFA] px-4 py-3 text-[#666666] placeholder-[#666666]/70 transition-colors duration-200 focus:border-[#4285F4] focus:outline-none focus:ring-4 focus:ring-[#4285F4]/20"
              />

              {error && <p className="text-sm text-[#EA4335]">{error}</p>}

              <div className="flex justify-end">
                <Link
                  href="/vendor/auth/forgot-password"
                  className="text-sm text-[#4285F4] hover:text-[#0D47A1] hover:underline"
                >
                  Forgot Password?
                </Link>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-xl bg-[#0D47A1] py-3 font-medium text-[#FFFFFF] shadow-[0_10px_20px_-12px_rgba(13,71,161,0.85)] transition-all duration-200 hover:bg-[#4285F4] hover:shadow-[0_16px_30px_-14px_rgba(66,133,244,0.7)] disabled:opacity-50"
              >
                {loading ? "Logging in..." : "Login →"}
              </button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-[#666666]">
                Don&apos;t have an account?{" "}
                <Link
                  href={ROUTES.VENDOR.REGISTER}
                  className="font-medium text-[#34A853] hover:text-[#0D47A1] hover:underline"
                >
                  Register
                </Link>
              </p>
            </div>

            <div className="mt-8 text-center text-xs text-[#666666]">
              Copyright © 2025 Occacia
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

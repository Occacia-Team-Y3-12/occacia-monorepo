"use client";

import Image from "next/image";
import Link from "next/link";
import { ROUTES } from "@/lib/routes";
import { useVendorRegister } from "@/hooks/vendor/useVendorRegister";

export default function VendorRegisterForm() {
  const {
    step,
    orgChoice,
    formData,
    errors,
    isAccountValid,
    isFinalValid,
    submitting,
    submitError,
    setStep,
    setOrgChoice,
    handleChange,
    handleAccountSubmit,
    handleFinalSubmit,
  } = useVendorRegister();
  const inputBaseClass =
    "w-full rounded-xl border bg-[#FAFAFA] px-4 py-3 text-[#666666] placeholder-[#666666]/70 transition-colors duration-200 focus:outline-none focus:ring-4 focus:ring-[#4285F4]/20";

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-[#F4F8FA] via-[#FAFAFA] to-[#FFFFFF] p-4">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-24 -left-16 h-72 w-72 rounded-full bg-[#4285F4]/10 blur-3xl" />
        <div className="absolute -bottom-28 -right-20 h-80 w-80 rounded-full bg-[#34A853]/10 blur-3xl" />
        <div className="absolute top-1/3 left-1/2 h-52 w-52 -translate-x-1/2 rounded-full bg-[#FBBC05]/10 blur-3xl" />
      </div>

      <div className="relative z-10 mx-auto flex min-h-[calc(100vh-2rem)] max-w-5xl items-center justify-center">
        <div className="flex w-full flex-col overflow-hidden rounded-3xl border border-[#EAEAEA] bg-[#FFFFFF] shadow-[0_24px_70px_-30px_rgba(13,71,161,0.35)] md:flex-row">
          <div className="w-full md:w-2/5 bg-gradient-to-br from-[#FFFFFF] via-[#F4F8FA] to-[#EAEAEA] p-6 md:p-12 flex flex-col items-center justify-center">
            <div className="mb-4 md:mb-8">
              <Image
                src="/icons/logo.svg"
                alt="Occacia Logo"
                width={120}
                height={120}
                priority
                className="md:h-[180px] md:w-[180px]"
              />
            </div>
            <h1 className="mb-2 text-2xl font-bold text-[#0D47A1] md:text-4xl">
              OCCACIA
            </h1>
            <p className="text-base font-medium tracking-[0.2em] text-[#666666] md:text-lg">
              VENDOR PORTAL
            </p>
            <span className="mt-6 rounded-full border border-[#CCCCCC] bg-[#FFFFFF] px-4 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-[#4285F4]">
              Build Your Storefront
            </span>
          </div>

          <div className="w-full md:w-3/5 p-6 md:p-12">
            <div className="mb-6 text-center md:mb-8">
              <h2 className="text-2xl font-semibold text-[#0D47A1] md:text-3xl">
                SIGN UP
              </h2>
              <p className="mt-2 text-sm text-[#666666]">
                Create your vendor profile and start listing products.
              </p>
              <p className="mt-3 text-xs font-medium uppercase tracking-[0.16em] text-[#4285F4]">
                {step === "account"
                  ? "Step 1 of 2 - Account Details"
                  : "Step 2 of 2 - Organization Setup"}
              </p>
            </div>

            {step === "account" ? (
              <form onSubmit={handleAccountSubmit} className="space-y-4">
                <div>
                  <input
                    type="text"
                    name="username"
                    placeholder="User Name"
                    value={formData.username}
                    onChange={handleChange}
                    className={`${inputBaseClass} ${errors.username ? "border-[#EA4335] focus:border-[#EA4335] focus:ring-[#EA4335]/20" : "border-[#CCCCCC] focus:border-[#4285F4]"}`}
                  />
                  {errors.username && (
                    <p className="mt-1 text-sm text-[#EA4335]">
                      {errors.username}
                    </p>
                  )}
                </div>

                <div>
                  <input
                    type="text"
                    name="fullName"
                    placeholder="Full Name"
                    value={formData.fullName}
                    onChange={handleChange}
                    className={`${inputBaseClass} ${errors.fullName ? "border-[#EA4335] focus:border-[#EA4335] focus:ring-[#EA4335]/20" : "border-[#CCCCCC] focus:border-[#4285F4]"}`}
                  />
                  {errors.fullName && (
                    <p className="mt-1 text-sm text-[#EA4335]">
                      {errors.fullName}
                    </p>
                  )}
                </div>

                <div>
                  <input
                    type="email"
                    name="email"
                    placeholder="Email Address"
                    value={formData.email}
                    onChange={handleChange}
                    className={`${inputBaseClass} ${errors.email ? "border-[#EA4335] focus:border-[#EA4335] focus:ring-[#EA4335]/20" : "border-[#CCCCCC] focus:border-[#4285F4]"}`}
                  />
                  {errors.email && (
                    <p className="mt-1 text-sm text-[#EA4335]">
                      {errors.email}
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div>
                    <input
                      type="password"
                      name="password"
                      placeholder="Password"
                      value={formData.password}
                      onChange={handleChange}
                      className={`${inputBaseClass} ${errors.password ? "border-[#EA4335] focus:border-[#EA4335] focus:ring-[#EA4335]/20" : "border-[#CCCCCC] focus:border-[#4285F4]"}`}
                    />
                    {errors.password && (
                      <p className="mt-1 text-sm text-[#EA4335]">
                        {errors.password}
                      </p>
                    )}
                  </div>
                  <div>
                    <input
                      type="password"
                      name="confirmPassword"
                      placeholder="Confirm password"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      className={`${inputBaseClass} ${errors.confirmPassword ? "border-[#EA4335] focus:border-[#EA4335] focus:ring-[#EA4335]/20" : "border-[#CCCCCC] focus:border-[#4285F4]"}`}
                    />
                    {errors.confirmPassword && (
                      <p className="mt-1 text-sm text-[#EA4335]">
                        {errors.confirmPassword}
                      </p>
                    )}
                  </div>
                </div>

                <div>
                  <input
                    type="text"
                    name="address"
                    placeholder="Address"
                    value={formData.address}
                    onChange={handleChange}
                    className={`${inputBaseClass} ${errors.address ? "border-[#EA4335] focus:border-[#EA4335] focus:ring-[#EA4335]/20" : "border-[#CCCCCC] focus:border-[#4285F4]"}`}
                  />
                  {errors.address && (
                    <p className="mt-1 text-sm text-[#EA4335]">
                      {errors.address}
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div>
                    <input
                      type="text"
                      name="nicNumber"
                      placeholder="NIC Number"
                      value={formData.nicNumber}
                      onChange={handleChange}
                      className={`${inputBaseClass} ${errors.nicNumber ? "border-[#EA4335] focus:border-[#EA4335] focus:ring-[#EA4335]/20" : "border-[#CCCCCC] focus:border-[#4285F4]"}`}
                    />
                    {errors.nicNumber && (
                      <p className="mt-1 text-sm text-[#EA4335]">
                        {errors.nicNumber}
                      </p>
                    )}
                  </div>
                  <div>
                    <select
                      name="gender"
                      value={formData.gender}
                      onChange={handleChange}
                      className={`${inputBaseClass} ${errors.gender ? "border-[#EA4335] focus:border-[#EA4335] focus:ring-[#EA4335]/20" : "border-[#CCCCCC] focus:border-[#4285F4]"}`}
                    >
                      <option value="">Select Gender</option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                    </select>
                    {errors.gender && (
                      <p className="mt-1 text-sm text-[#EA4335]">
                        {errors.gender}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex justify-center pt-4">
                  <button
                    type="submit"
                    disabled={!isAccountValid}
                    className="rounded-xl bg-[#0D47A1] px-8 py-3 font-medium text-[#FFFFFF] shadow-[0_10px_20px_-12px_rgba(13,71,161,0.85)] transition-all duration-200 hover:bg-[#4285F4] hover:shadow-[0_16px_30px_-14px_rgba(66,133,244,0.7)] disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleFinalSubmit} className="space-y-4">
                <div className="mb-6 rounded-xl border border-[#EAEAEA] bg-[#F4F8FA] p-4">
                  <p className="mb-4 font-medium text-[#666666]">
                    Do you belong to an organization?
                  </p>
                  <div className="space-y-2">
                    <label className="flex cursor-pointer items-center space-x-3">
                      <input
                        type="radio"
                        name="orgChoice"
                        value="join"
                        checked={orgChoice === "join"}
                        onChange={(e) => setOrgChoice(e.target.value as "join")}
                        className="h-4 w-4 border-[#CCCCCC] text-[#4285F4] focus:ring-[#4285F4]/30"
                      />
                      <span className="text-[#666666]">
                        Join existing organization
                      </span>
                    </label>
                    <label className="flex cursor-pointer items-center space-x-3">
                      <input
                        type="radio"
                        name="orgChoice"
                        value="create"
                        checked={orgChoice === "create"}
                        onChange={(e) =>
                          setOrgChoice(e.target.value as "create")
                        }
                        className="h-4 w-4 border-[#CCCCCC] text-[#4285F4] focus:ring-[#4285F4]/30"
                      />
                      <span className="text-[#666666]">
                        Create new organization
                      </span>
                    </label>
                  </div>
                </div>

                {orgChoice === "join" && (
                  <div>
                    <input
                      type="text"
                      name="organizationCode"
                      placeholder="Organization Code"
                      value={formData.organizationCode}
                      onChange={handleChange}
                      className={`${inputBaseClass} ${errors.organizationCode ? "border-[#EA4335] focus:border-[#EA4335] focus:ring-[#EA4335]/20" : "border-[#CCCCCC] focus:border-[#4285F4]"}`}
                    />
                    {errors.organizationCode && (
                      <p className="mt-1 text-sm text-[#EA4335]">
                        {errors.organizationCode}
                      </p>
                    )}
                  </div>
                )}

                {orgChoice === "create" && (
                  <>
                    <div>
                      <input
                        type="text"
                        name="businessName"
                        placeholder="Business Name"
                        value={formData.businessName}
                        onChange={handleChange}
                        className={`${inputBaseClass} ${errors.businessName ? "border-[#EA4335] focus:border-[#EA4335] focus:ring-[#EA4335]/20" : "border-[#CCCCCC] focus:border-[#4285F4]"}`}
                      />
                      {errors.businessName && (
                        <p className="mt-1 text-sm text-[#EA4335]">
                          {errors.businessName}
                        </p>
                      )}
                    </div>

                    <div>
                      <input
                        type="text"
                        name="businessRegNumber"
                        placeholder="Business Registration Number"
                        value={formData.businessRegNumber}
                        onChange={handleChange}
                        className={`${inputBaseClass} ${errors.businessRegNumber ? "border-[#EA4335] focus:border-[#EA4335] focus:ring-[#EA4335]/20" : "border-[#CCCCCC] focus:border-[#4285F4]"}`}
                      />
                      {errors.businessRegNumber && (
                        <p className="mt-1 text-sm text-[#EA4335]">
                          {errors.businessRegNumber}
                        </p>
                      )}
                    </div>

                    <div>
                      <input
                        type="text"
                        name="businessAddress"
                        placeholder="Business Address"
                        value={formData.businessAddress}
                        onChange={handleChange}
                        className={`${inputBaseClass} ${errors.businessAddress ? "border-[#EA4335] focus:border-[#EA4335] focus:ring-[#EA4335]/20" : "border-[#CCCCCC] focus:border-[#4285F4]"}`}
                      />
                      {errors.businessAddress && (
                        <p className="mt-1 text-sm text-[#EA4335]">
                          {errors.businessAddress}
                        </p>
                      )}
                    </div>

                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <div>
                        <input
                          type="tel"
                          name="businessPhone"
                          placeholder="Business Phone"
                          value={formData.businessPhone}
                          onChange={handleChange}
                          className={`${inputBaseClass} ${errors.businessPhone ? "border-[#EA4335] focus:border-[#EA4335] focus:ring-[#EA4335]/20" : "border-[#CCCCCC] focus:border-[#4285F4]"}`}
                        />
                        {errors.businessPhone && (
                          <p className="mt-1 text-sm text-[#EA4335]">
                            {errors.businessPhone}
                          </p>
                        )}
                      </div>

                      <div>
                        <input
                          type="email"
                          name="businessEmail"
                          placeholder="Business Email"
                          value={formData.businessEmail}
                          onChange={handleChange}
                          className={`${inputBaseClass} ${errors.businessEmail ? "border-[#EA4335] focus:border-[#EA4335] focus:ring-[#EA4335]/20" : "border-[#CCCCCC] focus:border-[#4285F4]"}`}
                        />
                        {errors.businessEmail && (
                          <p className="mt-1 text-sm text-[#EA4335]">
                            {errors.businessEmail}
                          </p>
                        )}
                      </div>
                    </div>
                  </>
                )}

                {submitError && (
                  <p className="text-sm text-[#EA4335]">{submitError}</p>
                )}

                <div className="flex flex-col-reverse gap-3 pt-4 sm:flex-row sm:justify-between">
                  <button
                    type="button"
                    onClick={() => setStep("account")}
                    className="w-full rounded-xl border border-[#CCCCCC] bg-[#FAFAFA] px-8 py-3 font-medium text-[#666666] transition-colors duration-200 hover:border-[#4285F4] hover:bg-[#F4F8FA] sm:w-auto"
                  >
                    Back
                  </button>
                  <button
                    type="submit"
                    disabled={!isFinalValid || submitting}
                    className="w-full rounded-xl bg-[#0D47A1] px-8 py-3 font-medium text-[#FFFFFF] shadow-[0_10px_20px_-12px_rgba(13,71,161,0.85)] transition-all duration-200 hover:bg-[#4285F4] hover:shadow-[0_16px_30px_-14px_rgba(66,133,244,0.7)] disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
                  >
                    {submitting ? "Creating..." : "Create vendor account"}
                  </button>
                </div>
              </form>
            )}

            <div className="mt-6 text-center">
              <p className="text-sm text-[#666666]">
                Already have an account?{" "}
                <Link
                  href={ROUTES.VENDOR.LOGIN}
                  className="font-medium text-[#4285F4] hover:text-[#0D47A1] hover:underline"
                >
                  Click here
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

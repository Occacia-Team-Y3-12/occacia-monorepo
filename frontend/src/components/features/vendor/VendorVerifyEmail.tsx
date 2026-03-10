'use client';

import { Suspense } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { ROUTES } from '@/lib/routes';
import { useVendorVerifyEmail } from '@/hooks/vendor/useVendorVerifyEmail';

function VendorVerifyEmailContent() {
	const searchParams = useSearchParams();
	const token = searchParams.get('token');
	const { status } = useVendorVerifyEmail(token);

	return (
		<div className="min-h-screen flex items-center justify-center relative overflow-hidden p-4">
			<Image src="/images/background.png" alt="Background" fill className="object-cover" priority />

			<div className="bg-white rounded-3xl shadow-2xl p-8 sm:p-10 md:p-12 max-w-md sm:max-w-lg w-full relative z-10 text-center">
				<div className="mb-6 md:mb-8 flex justify-center">
					<Image src="/images/logo.png" alt="Occacia Logo" width={100} height={100} priority className="sm:w-[120px] sm:h-[120px] md:w-[140px] md:h-[140px]" />
				</div>

				<h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-[#2c3e50] mb-3 md:mb-4">Email Verification</h1>

				{status === 'loading' && (
					<div>
						<p className="text-[#5a6c7d] mb-4 md:mb-6 text-sm md:text-base">Verifying your email...</p>
						<div className="animate-spin rounded-full h-10 w-10 md:h-12 md:w-12 border-b-2 border-[#1e88e5] mx-auto"></div>
					</div>
				)}

				{status === 'success' && (
					<div>
						<div className="w-12 h-12 md:w-16 md:h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4 md:mb-6">
							<svg className="w-6 h-6 md:w-8 md:h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
							</svg>
						</div>
						<p className="text-green-600 mb-3 md:mb-4 text-sm md:text-base font-semibold">Email verified successfully!</p>
						<p className="text-[#5a6c7d] text-sm md:text-base">Redirecting to pending approval...</p>
					</div>
				)}

				{status === 'error' && (
					<div>
						<div className="w-12 h-12 md:w-16 md:h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4 md:mb-6">
							<svg className="w-6 h-6 md:w-8 md:h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
							</svg>
						</div>
						<p className="text-red-600 mb-3 md:mb-4 text-sm md:text-base font-semibold">Verification failed</p>
						<p className="text-[#5a6c7d] text-sm md:text-base mb-6">The verification link is invalid or expired. Please try registering again.</p>
						<Link href={ROUTES.VENDOR.REGISTER} className="inline-block bg-[#1565c0] hover:bg-[#0d47a1] text-white font-medium px-6 md:px-8 py-3 md:py-4 text-base md:text-lg rounded-lg transition-colors duration-200">
							Back to Registration
						</Link>
					</div>
				)}
			</div>
		</div>
	);
}

export default function VendorVerifyEmail() {
	return (
		<Suspense
			fallback={
				<div className="min-h-screen flex items-center justify-center relative overflow-hidden p-4">
					<Image src="/images/background.png" alt="Background" fill className="object-cover" priority />
					<div className="bg-white rounded-3xl shadow-2xl p-8 sm:p-10 md:p-12 max-w-md sm:max-w-lg w-full relative z-10 text-center">
						<div className="mb-6 md:mb-8 flex justify-center">
							<Image src="/images/logo.png" alt="Occacia Logo" width={100} height={100} priority className="sm:w-[120px] sm:h-[120px] md:w-[140px] md:h-[140px]" />
						</div>
						<div className="animate-spin rounded-full h-10 w-10 md:h-12 md:w-12 border-b-2 border-[#1e88e5] mx-auto"></div>
					</div>
				</div>
			}
		>
			<VendorVerifyEmailContent />
		</Suspense>
	);
}

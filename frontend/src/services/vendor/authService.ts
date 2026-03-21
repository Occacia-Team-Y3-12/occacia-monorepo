import { VendorFormData } from '@/lib/validation';
import { featureFlags } from '@/config/featureFlags';
import { API_BASE_URL } from '@/services/api';

type RegisterResponse = {
	status?: string;
	data?: { token?: string };
	message?: string;
};

export const vendorAuthService = {
	async login(payload: { email: string; password: string }) {
		if (featureFlags.useVendorAuthMock) {
			await new Promise((resolve) => setTimeout(resolve, 350));
			return {
				ok: payload.email.trim().length > 0 && payload.password.trim().length > 0,
			};
		}

		const response = await fetch(`${API_BASE_URL}/auth/vendor/login`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(payload),
		});

		return { ok: response.ok };
	},

	async register(payload: VendorFormData & { organizationType: 'join' | 'create' }) {
		// Map frontend form fields → backend expected schema
		const backendPayload = {
			email: payload.email,
			password: payload.password,
			business_name: payload.businessName,
			display_name: payload.fullName,
			contact_phone: payload.businessPhone,
			phone: payload.businessPhone,
			location_base: payload.businessAddress,
		};

		if (featureFlags.useVendorAuthMock) {
			return {
				ok: true,
				data: {
					status: 'pending_verification',
					message: 'Please verify your email',
					data: { token: `mock_${Date.now()}` },
				},
			};
		}

		const response = await fetch(`${API_BASE_URL}/auth/vendor/register`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(backendPayload),
		});

		const responseData = (await response.json()) as Record<string, unknown>;
		const data: RegisterResponse = {
			status: response.ok ? 'pending_verification' : 'error',
			message:
				typeof responseData.detail === 'string'
					? responseData.detail
					: typeof responseData.message === 'string'
						? responseData.message
						: response.ok
							? 'Please verify your email'
							: 'Registration failed',
		};
		return { ok: response.ok, data };
	},

	async forgotPassword(email: string) {
		if (featureFlags.useVendorAuthMock) {
			await new Promise((resolve) => setTimeout(resolve, 1200));
			return { ok: email.trim().length > 0 };
		}

		return { ok: false };
	},

	async verifyEmail(token: string | null) {
		if (featureFlags.useVendorAuthMock) {
			await new Promise((resolve) => setTimeout(resolve, 2000));
			return { ok: Boolean(token && token.startsWith('mock_')) };
		}

		if (!token) {
			return { ok: false };
		}

		const response = await fetch(
			`${API_BASE_URL}/auth/vendor/verify-email?token=${encodeURIComponent(token)}`
		);
		return { ok: response.ok };
	},
};

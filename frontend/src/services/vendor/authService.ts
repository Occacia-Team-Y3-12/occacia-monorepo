import { VendorFormData } from '@/lib/validation';

type RegisterResponse = {
	status?: string;
	data?: { token?: string };
	message?: string;
};

export const vendorAuthService = {
	async login(payload: { email: string; password: string }) {
		await new Promise((resolve) => setTimeout(resolve, 350));
		return {
			ok: payload.email.trim().length > 0 && payload.password.trim().length > 0,
		};
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

		const response = await fetch('/api/v1/auth/vendor/register', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(backendPayload),
		});

		const data = (await response.json()) as RegisterResponse;
		return { ok: response.ok, data };
	},

	async forgotPassword(email: string) {
		await new Promise((resolve) => setTimeout(resolve, 1200));
		return { ok: email.trim().length > 0 };
	},

	async verifyEmail(token: string | null) {
		await new Promise((resolve) => setTimeout(resolve, 2000));
		return { ok: Boolean(token && token.startsWith('mock_')) };
	},
};
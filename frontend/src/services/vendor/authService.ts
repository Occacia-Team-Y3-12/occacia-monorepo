import { VendorFormData } from '@/lib/validation';

type RegisterResponse = {
	status?: string;
	data?: {
		token?: string;
	};
	message?: string;
};

export const vendorAuthService = {
	// TODO: Replace with real backend API call
	async login(payload: { email: string; password: string }) {
		await new Promise((resolve) => setTimeout(resolve, 350));
		return {
			ok: payload.email.trim().length > 0 && payload.password.trim().length > 0,
		};
	},

	async register(payload: VendorFormData & { organizationType: 'join' | 'create' }) {
		const response = await fetch('/api/v1/auth/register', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(payload),
		});

		const data = (await response.json()) as RegisterResponse;
		return { ok: response.ok, data };
	},

	// TODO: Replace with real backend API call
	async forgotPassword(email: string) {
		await new Promise((resolve) => setTimeout(resolve, 1200));
		return { ok: email.trim().length > 0 };
	},

	// TODO: Replace with real backend API call
	async verifyEmail(token: string | null) {
		await new Promise((resolve) => setTimeout(resolve, 2000));
		return { ok: Boolean(token && token.startsWith('mock_')) };
	},
};

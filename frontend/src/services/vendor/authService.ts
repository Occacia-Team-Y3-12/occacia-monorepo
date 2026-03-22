import { VendorFormData } from '@/lib/validation';
import { featureFlags } from '@/config/featureFlags';
import { API_BASE_URL } from '@/services/api';

type VendorLoginResponse = {
	access_token?: string;
	accessToken?: string;
	token_type?: string;
	data?: {
		access_token?: string;
		accessToken?: string;
		token_type?: string;
		role?: string;
	};
	role?: string;
	message?: string;
};

type RegisterResponse = {
	status?: string;
	data?: { token?: string };
	message?: string;
	detail?: string;
};

export const vendorAuthService = {
	async login(payload: { email: string; password: string }) {
<<<<<<< Updated upstream
		if (featureFlags.useVendorAuthMock) {
			await new Promise((resolve) => setTimeout(resolve, 350));
			return {
				ok: payload.email.trim().length > 0 && payload.password.trim().length > 0,
			};
		}

		const response = await fetch(`${API_BASE_URL}/auth/vendor/login`, {
=======
		const response = await fetch('/api/v1/auth/vendor/login', {
>>>>>>> Stashed changes
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(payload),
		});

<<<<<<< Updated upstream
		return { ok: response.ok };
=======
		const data = (await response.json()) as VendorLoginResponse;
		const accessToken =
			data.access_token ||
			data.accessToken ||
			data.data?.access_token ||
			data.data?.accessToken;

		if (!response.ok || !accessToken) {
			return {
				ok: false,
				message: data.message || 'Invalid credentials. Please try again.',
			};
		}

		localStorage.setItem('vendorToken', accessToken);
		localStorage.setItem('access_token', accessToken);
		localStorage.setItem('accessToken', accessToken);
		localStorage.setItem('vendor_role', 'VENDOR');
		localStorage.removeItem('admin_token');

		return { ok: true };
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
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
=======
		let data: RegisterResponse = {};
		try {
			data = (await response.json()) as RegisterResponse;
		} catch {
			data = {};
		}

		if (!response.ok) {
			return {
				ok: false,
				data,
				message: data.detail || data.message || 'Registration failed. Please try again.',
			};
		}

		return {
			ok: true,
			data,
			message: 'Registration successful. Please login.',
		};
>>>>>>> Stashed changes
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

export interface AdminLoginRequest {
  email: string;
  password: string;
}

export interface AdminLoginResponse {
  access_token: string;
  token_type: string;
  role: string;
}

export interface AdminRegisterRequest {
  email: string;
  password: string;
  staffRole?: string;
}

export interface AdminRegisterResponse {
  message?: string;
  admin_id?: string;
  email?: string;
  staff_role?: string;
}

export interface AdminVerifyEmailResponse {
  message: string;
}

export interface AdminForgotPasswordResponse {
  message: string;
}

export interface AdminVerifyOtpResponse {
  resetToken: string;
  message: string;
}

export interface AdminResetPasswordResponse {
  message: string;
}

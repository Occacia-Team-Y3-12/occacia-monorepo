import axios from 'axios';
import { attachAdmin401Interceptor, attachAuthHeaderInterceptor } from '@/services/http';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

attachAuthHeaderInterceptor(apiClient, () => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('admin_token') || localStorage.getItem('auth_token');
});
attachAdmin401Interceptor(apiClient);

export default apiClient;

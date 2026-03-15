import axios from 'axios';
import type { RecommendationPackage } from '@/types/customer/package';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('customerToken');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const packageService = {
  getPackages: (eventId: string) =>
    api.get<RecommendationPackage[]>(`/customers/events/${eventId}/packages`).then(r => r.data),

  getPackageById: (eventId: string, packageId: string) =>
    api.get<RecommendationPackage>(`/customers/events/${eventId}/packages/${packageId}`).then(r => r.data),

  generatePackages: (eventId: string) =>
    api.post<RecommendationPackage[]>(`/customers/events/${eventId}/recommendations`).then(r => r.data),
};

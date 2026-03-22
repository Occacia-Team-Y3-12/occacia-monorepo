import axios from 'axios';

import { API_BASE_URL } from '@/services/api';
import type { CustomerPackageService } from './packageService.types';

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('customerToken');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const apiPackageService: CustomerPackageService = {
  getPackages: (eventId) =>
    api
      .get(`/customers/events/${eventId}/packages`)
      .then((response) => response.data),

  getPackageById: (eventId, packageId) =>
    api
      .get(`/customers/events/${eventId}/packages/${packageId}`)
      .then((response) => response.data),

  generatePackages: (eventId) =>
    api
      .post(`/customers/events/${eventId}/recommendations`)
      .then((response) => response.data),

  getTaskRecommendations: (eventId, taskId) =>
    api
      .get(`/customers/events/${eventId}/tasks/${taskId}/recommendations`)
      .then((response) => response.data),

  updatePackage: (eventId, packageId, items) =>
    api
      .put(`/customers/events/${eventId}/packages/${packageId}`, { items })
      .then((response) => response.data),

  confirmPackage: (eventId, packageId, idempotencyKey) =>
    api
      .post(
        `/customers/events/${eventId}/packages/${packageId}/confirm`,
        {},
        { headers: { 'Idempotency-Key': idempotencyKey } }
      )
      .then((response) => response.data),

  clearCachedPackages: () => {},
};

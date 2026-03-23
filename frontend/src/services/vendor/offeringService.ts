import axios from 'axios';
import { Offering, CreateOfferingData, UpdateOfferingData } from '@/types/vendor/offering';
import { API_BASE_URL } from '@/services/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('vendorToken');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const offeringService = {
  getAll: async (): Promise<Offering[]> => {
    const response = await api.get('/vendors/offerings');
    return response.data;
  },

  getById: async (id: string): Promise<Offering> => {
    const response = await api.get(`/vendors/offerings/${id}`);
    return response.data;
  },

  create: async (data: CreateOfferingData): Promise<Offering> => {
    const response = await api.post('/vendors/offerings', data);
    return response.data;
  },

  update: async (id: string, data: UpdateOfferingData): Promise<Offering> => {
    const response = await api.put(`/vendors/offerings/${id}`, data);
    return response.data;
  },
};

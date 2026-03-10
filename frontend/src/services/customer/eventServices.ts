import { CreateCustomerEventPayload, CreateCustomerEventResponse } from '@/types/customer';

export const customerEventService = {
  async createDraftEvent(payload: CreateCustomerEventPayload) {
    const response = await fetch('/api/v1/customers/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = (await response.json()) as CreateCustomerEventResponse;
    return { ok: response.ok, data };
  },
};

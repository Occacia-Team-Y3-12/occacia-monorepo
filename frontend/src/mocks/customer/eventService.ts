import { getFallbackEventTypes } from '@/lib/customerEventTypeOptions';
import type {
  CreateCustomerEventPayload,
  CreateCustomerEventResponse,
  DeleteDraftEventResponse,
  EventTypesResponse,
  PaginatedCustomerEventsResponse,
  ServiceResult,
  UpdateEventPersonasPayload,
  UpdateEventPersonasResponse,
} from '@/types/customer';
import { eventStore } from '@/mocks/customer/eventStore';

const success = <T>(status: number, data: T): ServiceResult<T> => ({
  ok: true,
  status,
  data,
});

const failure = <T>(status: number, error: string, data?: T): ServiceResult<T> => ({
  ok: false,
  status,
  error,
  data,
});

export const mockCustomerEventService = {
  async listEvents(params?: {
    status?: string;
    limit?: number;
    cursor?: string;
  }): Promise<ServiceResult<PaginatedCustomerEventsResponse>> {
    return success(200, eventStore.listEvents(params));
  },

  async getEventTypes(): Promise<ServiceResult<EventTypesResponse>> {
    return success(200, {
      status: 'success',
      message: 'Event types fetched successfully.',
      data: {
        eventTypes: getFallbackEventTypes(),
      },
    });
  },

  async createEvent(
    payload: CreateCustomerEventPayload
  ): Promise<ServiceResult<CreateCustomerEventResponse>> {
    const title = payload.title?.trim();
    if (!title) {
      return failure(400, 'Event title is required.', {
        status: 'error',
        message: 'Event title is required.',
      });
    }

    const event = eventStore.createEvent({
      ...payload,
      title,
    });

    return success(201, {
      status: 'success',
      message: 'Event created successfully.',
      data: {
        eventId: event.eventId,
        state: 'draft',
      },
    });
  },

  async updatePersonas(
    eventId: string,
    payload: UpdateEventPersonasPayload
  ): Promise<ServiceResult<UpdateEventPersonasResponse>> {
    if (!Array.isArray(payload.personaIds)) {
      return failure(400, 'personaIds must be an array.', {
        status: 'error',
        message: 'personaIds must be an array.',
      });
    }

    eventStore.updatePersonas(eventId, payload.personaIds);

    return success(200, {
      status: 'success',
      message: 'Personas updated successfully.',
      data: {
        eventId,
        personaIds: payload.personaIds,
      },
    });
  },

  async deleteDraft(eventId: string): Promise<ServiceResult<DeleteDraftEventResponse>> {
    const deleted = eventStore.deleteDraft(eventId);

    if (!deleted) {
      return failure(400, 'Only draft events can be deleted or event was not found.', {
        status: 'error',
        message: 'Only draft events can be deleted or event was not found.',
      });
    }

    return success(200, {
      status: 'success',
      message: 'Draft deleted successfully.',
    });
  },
};

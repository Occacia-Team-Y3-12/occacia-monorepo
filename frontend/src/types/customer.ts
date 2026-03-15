export type CustomerEventType = 'individual' | 'group' | 'others';

export type CustomerPersonaOption = {
	id: string;
	name: string;
	role: string;
	imageUrl?: string;
};

export type EventTypeOption = {
	id: string;
	value: CustomerEventType | string;
	label: string;
	example: string;
	titlePlaceholder: string;
};

export type CreateCustomerEventPayload = {
	eventType: CustomerEventType | string;
	title: string;
	description?: string;
};

export type UpdateEventPersonasPayload = {
	personaIds: string[];
};

export type CreateCustomerEventResponse = {
	status: 'success' | 'error';
	message: string;
	data?: {
		eventId: string;
		state: 'draft';
	};
};

export type EventTypesResponse = {
	status: 'success' | 'error';
	message: string;
	data?: {
		eventTypes: EventTypeOption[];
	};
};

export type UpdateEventPersonasResponse = {
	status: 'success' | 'error';
	message: string;
	data?: {
		eventId: string;
		personaIds: string[];
	};
};

export type DeleteDraftEventResponse = {
	status: 'success' | 'error';
	message: string;
};

export type ServiceResult<T> = {
	ok: boolean;
	status: number;
	data?: T;
	error?: string;
};

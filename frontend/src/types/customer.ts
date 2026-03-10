export type CustomerEventType = 'individual' | 'group' | 'others';

export type CustomerPersonaOption = {
	id: string;
	name: string;
	role: string;
};

export type CreateCustomerEventPayload = {
	eventType: CustomerEventType;
	title: string;
	description?: string;
	personaIds?: string[];
};

export type CreateCustomerEventResponse = {
	status: 'success' | 'error';
	message: string;
	data?: {
		eventId: string;
		state: 'draft';
	};
};

'use client';

import { useState } from 'react';
import { useCreateEvent } from '@/hooks/customer/useCreateEvent';

const DEFAULT_PERSONA_IMAGE = '/icons/customer/dashboard/profile.svg';

const CustomerCreateEvent = () => {
  const {
    eventType,
    eventTypes,
    personas,
    title,
    selectedPersonaIds,
    errors,
    isLoadingEventTypes,
    isSubmitting,
    isCancelling,
    selectedEventType,
    titlePlaceholder,
    setEventType,
    setTitle,
    togglePersona,
    addNewPersona,
    handleCreate,
    handleCancel,
  } = useCreateEvent();

  const [isAddPersonOpen, setIsAddPersonOpen] = useState(false);
  const [newPersonName, setNewPersonName] = useState('');
  const [newPersonRole, setNewPersonRole] = useState('');

  const onAddNewPerson = () => {
    addNewPersona(newPersonName, newPersonRole);
    if (!newPersonName.trim() || !newPersonRole.trim()) {
      return;
    }

    setNewPersonName('');
    setNewPersonRole('');
    setIsAddPersonOpen(false);
  };

  return (
    <section className="flex min-h-[calc(100vh-140px)] w-full flex-col pb-8 pt-0">
      <div className="mb-6">
        <h1 className="text-[44px] font-bold leading-tight text-[#0D47A1]">Create New Event</h1>
        <p className="mt-2 pl-1 text-base text-[#666666]">Set up your next masterpiece. Fill in the essential details to get started.</p>
      </div>

      <div className="space-y-5">
        <div className="overflow-hidden rounded-2xl border border-[#EAEAEA] bg-[#FFFFFF] shadow-[0_2px_8px_rgba(13,71,161,0.04)]">
          <div className="flex items-center gap-2 border-b border-[#EAEAEA] bg-[#FAFAFA] px-6 py-4">
            <img
              src="/icons/customer/events/Info_Icon.svg"
              alt=""
              aria-hidden="true"
              className="h-5 w-5"
            />
            <span className="text-base font-semibold text-[#0D47A1]">General Information</span>
          </div>

          <div className="space-y-4 px-6 py-5">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-semibold text-[#666666]">Event Type</label>
                <select
                  value={eventType}
                  onChange={(event) => setEventType(event.target.value)}
                  disabled={isLoadingEventTypes}
                  className="h-11 w-full rounded-xl border border-[#CCCCCC] bg-[#FAFAFA] px-3 text-sm text-[#666666] outline-none transition-colors focus:border-[#4285F4]"
                >
                  <option value="" disabled hidden>{isLoadingEventTypes ? 'Loading event types...' : 'Select event type'}</option>
                  {eventTypes.map((type) => (
                    <option key={type.id} value={type.value}>
                      {`${type.label === 'Other' ? 'Others' : type.label} (e.g., ${type.example})`}
                    </option>
                  ))}
                </select>
                {errors.eventType && <p className="mt-1 text-xs text-[#EA4335]">{errors.eventType}</p>}
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold text-[#666666]">Event Title</label>
                <input
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder={titlePlaceholder}
                  className="h-11 w-full rounded-xl border border-[#CCCCCC] bg-[#FAFAFA] px-3 text-sm text-[#666666] outline-none transition-colors placeholder:text-[#C9C9C9] focus:border-[#4285F4]"
                />
                {errors.title && <p className="mt-1 text-xs text-[#EA4335]">{errors.title}</p>}
                {!errors.title && selectedEventType && (
                  <p className="mt-1 text-xs text-[#666666]">Example: {selectedEventType.titlePlaceholder.replace('e.g., ', '')}</p>
                )}
              </div>
            </div>

          </div>
        </div>

        <div className="overflow-hidden rounded-2xl border border-[#EAEAEA] bg-[#FFFFFF] shadow-[0_2px_8px_rgba(13,71,161,0.04)]">
          <div className="flex items-center gap-2 border-b border-[#EAEAEA] bg-[#FAFAFA] px-6 py-4">
            <img src="/icons/customer/events/Add_People_Icon.svg" alt="" aria-hidden="true" className="h-5 w-5" />
            <span className="text-base font-semibold text-[#0D47A1]">Assign People</span>
          </div>

          <div className="px-6 py-5">
            <p className="mb-4 text-sm text-[#666666]">
              Select one or more people to customize the event experience for specific audience types.
            </p>

            <div className="flex flex-col gap-3">
              <div className="flex flex-col items-stretch rounded-3xl border border-[#EAEAEA] bg-[#F4F8FA] md:flex-row">
                {personas.map((persona, index) => {
                  const selected = selectedPersonaIds.includes(persona.id);
                  return (
                    <button
                      type="button"
                      key={persona.id}
                      onClick={() => togglePersona(persona.id)}
                      className={`flex flex-1 items-center gap-4 px-6 py-6 text-left transition-all duration-200 first:rounded-t-3xl last:rounded-b-3xl md:first:rounded-l-3xl md:first:rounded-tr-none md:last:rounded-r-3xl md:last:rounded-bl-none ${
                        index !== 0 ? 'border-t border-[#EAEAEA] md:border-l md:border-t-0' : ''
                      } ${
                        selected
                          ? 'bg-[#FFFFFF] shadow-[inset_0_0_0_2px_#4285F4]'
                          : 'hover:bg-[#FAFAFA]'
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <img
                          src={persona.imageUrl || DEFAULT_PERSONA_IMAGE}
                          alt=""
                          aria-hidden="true"
                          className={`h-[56px] w-[56px] rounded-full object-cover transition-all duration-200 ${
                            selected ? 'ring-2 ring-[#4285F4] ring-offset-2 ring-offset-[#FFFFFF]' : ''
                          }`}
                        />
                        <div className="min-w-0">
                          <p className={`truncate text-[15px] font-semibold ${selected ? 'text-[#0D47A1]' : 'text-[#666666]'}`}>{persona.name}</p>
                          <p className={`truncate text-[12px] ${selected ? 'text-[#4285F4]' : 'text-[#666666]'}`}>{persona.role}</p>
                        </div>
                      </div>
                    </button>
                  );
                })}

                <div className="hidden items-center pr-6 md:flex">
                  <span className="h-9 w-9 rounded-full border-[4px] border-[#C9C9C9] bg-transparent" />
                </div>
              </div>

              <button
                type="button"
                onClick={() => setIsAddPersonOpen((prev) => !prev)}
                className="inline-flex h-[96px] w-full items-center gap-4 rounded-3xl border-[3px] border-dashed border-[#CCCCCC] bg-[#FAFAFA] px-6 text-[16px] font-semibold text-[#666666] transition-colors hover:border-[#4285F4] hover:text-[#0D47A1] sm:w-[230px]"
              >
                <span className="inline-flex h-12 w-12 items-center justify-center rounded-full border-[3px] border-[#CCCCCC]">
                  <svg viewBox="0 0 24 24" className="h-6 w-6 text-[#666666]" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round">
                    <path d="M12 6v12" />
                    <path d="M6 12h12" />
                  </svg>
                </span>
                New People
              </button>

              {isAddPersonOpen && (
                <div className="grid grid-cols-1 gap-3 rounded-2xl border border-[#EAEAEA] bg-[#F4F8FA] p-4 sm:grid-cols-[1fr_1fr_auto]">
                  <input
                    value={newPersonName}
                    onChange={(event) => setNewPersonName(event.target.value)}
                    placeholder="Person name"
                    className="h-11 rounded-xl border border-[#CCCCCC] bg-white px-3 text-sm text-[#666666] outline-none transition-colors placeholder:text-[#C9C9C9] focus:border-[#4285F4]"
                  />
                  <input
                    value={newPersonRole}
                    onChange={(event) => setNewPersonRole(event.target.value)}
                    placeholder="Role (e.g., Family Member)"
                    className="h-11 rounded-xl border border-[#CCCCCC] bg-white px-3 text-sm text-[#666666] outline-none transition-colors placeholder:text-[#C9C9C9] focus:border-[#4285F4]"
                  />
                  <button
                    type="button"
                    onClick={onAddNewPerson}
                    className="h-11 rounded-xl bg-[#0D47A1] px-5 text-sm font-semibold text-white transition-colors hover:bg-[#4285F4]"
                  >
                    Add
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {errors.form && <p className="mt-4 text-sm font-medium text-[#EA4335]">{errors.form}</p>}

      <div className="mt-auto pt-8">
        <div className="flex items-center justify-end gap-6">
        <button
          onClick={handleCancel}
          disabled={isSubmitting || isCancelling}
          className="text-sm font-semibold text-[#666666] transition-colors hover:text-[#0D47A1] disabled:opacity-60"
        >
          {isCancelling ? 'Cancelling...' : 'Cancel'}
        </button>
        <button
          onClick={handleCreate}
          disabled={isSubmitting || isCancelling}
          className="h-11 rounded-xl bg-[#0D47A1] px-8 text-sm font-semibold text-white shadow-[0_8px_20px_rgba(13,71,161,0.28)] transition-colors hover:bg-[#4285F4] disabled:opacity-60"
        >
          {isSubmitting ? 'Creating...' : 'Create Event'}
        </button>
        </div>
      </div>
    </section>
  );
};

export default CustomerCreateEvent;



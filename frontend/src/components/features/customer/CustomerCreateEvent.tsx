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
    description,
    selectedPersonaIds,
    errors,
    isLoadingEventTypes,
    isSubmitting,
    isCancelling,
    selectedEventType,
    titlePlaceholder,
    setEventType,
    setTitle,
    setDescription,
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
        <h1 className="text-[40px] font-bold leading-tight text-[#141A2A]">Create New Event</h1>
        <p className="mt-2 text-sm text-[#7B8398]">Set up your next masterpiece. Fill in the essential details to get started.</p>
      </div>

      <div className="space-y-5">
        <div className="overflow-hidden rounded-2xl border border-[#E4E8F2] bg-[#FFFFFF]">
          <div className="flex items-center gap-2 border-b border-[#E4E8F2] px-5 py-4">
            <img
              src="/icons/customer/events/Info_Icon.svg"
              alt=""
              aria-hidden="true"
              className="h-4 w-4"
            />
            <span className="text-sm font-semibold text-[#1B2237]">General Information</span>
          </div>

          <div className="space-y-4 px-5 py-5">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <div>
                <label className="mb-2 block text-xs font-medium text-[#667085]">Event Type</label>
                <select
                  value={eventType}
                  onChange={(event) => setEventType(event.target.value)}
                  disabled={isLoadingEventTypes}
                  className="h-11 w-full rounded-xl border border-[#DFE3ED] bg-[#F1F3F8] px-3 text-sm text-[#1D2538] outline-none"
                >
                  <option value="">{isLoadingEventTypes ? 'Loading event types...' : 'Select event type'}</option>
                  {eventTypes.map((type) => (
                    <option key={type.id} value={type.value}>
                      {`${type.label} (e.g., ${type.example})`}
                    </option>
                  ))}
                </select>
                {errors.eventType && <p className="mt-1 text-xs text-[#C23A3A]">{errors.eventType}</p>}
              </div>

              <div>
                <label className="mb-2 block text-xs font-medium text-[#667085]">Event Title</label>
                <input
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder={titlePlaceholder}
                  className="h-11 w-full rounded-xl border border-[#DFE3ED] bg-[#F1F3F8] px-3 text-sm text-[#1D2538] outline-none placeholder:text-[#9BA3B4]"
                />
                {errors.title && <p className="mt-1 text-xs text-[#C23A3A]">{errors.title}</p>}
                {!errors.title && selectedEventType && (
                  <p className="mt-1 text-xs text-[#8A90A1]">Example: {selectedEventType.titlePlaceholder.replace('e.g., ', '')}</p>
                )}
              </div>
            </div>

            <div>
              <label className="mb-2 block text-xs font-medium text-[#667085]">Description</label>
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Briefly describe the theme, goals, or schedule..."
                rows={4}
                className="h-[74px] w-full resize-none rounded-xl border border-[#DFE3ED] bg-[#F1F3F8] px-3 py-3 text-sm text-[#1D2538] outline-none placeholder:text-[#9BA3B4]"
              />
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-2xl border border-[#E4E8F2] bg-[#FFFFFF]">
          <div className="flex items-center gap-2 border-b border-[#E4E8F2] px-5 py-4">
            <img src="/icons/customer/events/Add_People_Icon.svg" alt="" aria-hidden="true" className="h-4 w-4" />
            <span className="text-sm font-semibold text-[#1B2237]">Assign People</span>
          </div>

          <div className="px-5 py-5">
            <p className="mb-4 text-xs text-[#6C7891]">
              Select one or more people to customize the event experience for specific audience types.
            </p>

            <div className="flex flex-col gap-3">
              <div className="flex items-stretch rounded-3xl border border-[#DEE3EC] bg-[#EFF2F7]">
                {personas.map((persona, index) => {
                  const selected = selectedPersonaIds.includes(persona.id);
                  return (
                    <button
                      type="button"
                      key={persona.id}
                      onClick={() => togglePersona(persona.id)}
                      className={`flex flex-1 items-center gap-4 px-6 py-6 text-left transition-colors first:rounded-l-3xl ${
                        index !== 0 ? 'border-l border-[#DEE3EC]' : ''
                      } ${
                        selected ? 'bg-[#EAF0FF]' : 'hover:bg-[#E8EDF5]'
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <img
                          src={persona.imageUrl || DEFAULT_PERSONA_IMAGE}
                          alt=""
                          aria-hidden="true"
                          className="h-[56px] w-[56px] rounded-full object-cover"
                        />
                        <div className="min-w-0">
                          <p className="truncate text-[15px] font-semibold text-[#141A2A]">{persona.name}</p>
                          <p className="truncate text-[12px] text-[#63728D]">{persona.role}</p>
                        </div>
                      </div>
                    </button>
                  );
                })}

                <div className="flex items-center pr-6">
                  <span className="h-9 w-9 rounded-full border-[4px] border-[#BCC8DA] bg-transparent" />
                </div>
              </div>

              <button
                type="button"
                onClick={() => setIsAddPersonOpen((prev) => !prev)}
                className="inline-flex h-[96px] w-[230px] items-center gap-4 rounded-3xl border-[3px] border-dashed border-[#D5DDEA] px-6 text-[16px] font-semibold text-[#6B7892]"
              >
                <span className="inline-flex h-12 w-12 items-center justify-center rounded-full border-[3px] border-[#D5DDEA]">
                  <svg viewBox="0 0 24 24" className="h-6 w-6 text-[#6B7892]" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round">
                    <path d="M12 6v12" />
                    <path d="M6 12h12" />
                  </svg>
                </span>
                New People
              </button>

              {isAddPersonOpen && (
                <div className="grid grid-cols-1 gap-3 rounded-2xl border border-[#DEE3EC] bg-[#F5F7FC] p-4 sm:grid-cols-[1fr_1fr_auto]">
                  <input
                    value={newPersonName}
                    onChange={(event) => setNewPersonName(event.target.value)}
                    placeholder="Person name"
                    className="h-11 rounded-xl border border-[#D6DCEA] bg-white px-3 text-sm text-[#1D2538] outline-none"
                  />
                  <input
                    value={newPersonRole}
                    onChange={(event) => setNewPersonRole(event.target.value)}
                    placeholder="Role (e.g., Family Member)"
                    className="h-11 rounded-xl border border-[#D6DCEA] bg-white px-3 text-sm text-[#1D2538] outline-none"
                  />
                  <button
                    type="button"
                    onClick={onAddNewPerson}
                    className="h-11 rounded-xl bg-[#2046C9] px-5 text-sm font-semibold text-white"
                  >
                    Add
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {errors.form && <p className="mt-4 text-sm font-medium text-[#C23A3A]">{errors.form}</p>}

      <div className="mt-auto pt-8">
        <div className="flex items-center justify-end gap-6">
        <button
          onClick={handleCancel}
          disabled={isSubmitting || isCancelling}
          className="text-sm font-semibold text-[#4F5871] disabled:opacity-60"
        >
          {isCancelling ? 'Cancelling...' : 'Cancel'}
        </button>
        <button
          onClick={handleCreate}
          disabled={isSubmitting || isCancelling}
          className="h-11 rounded-xl bg-[#2046C9] px-8 text-sm font-semibold text-white shadow-[0_8px_20px_rgba(32,70,201,0.28)] disabled:opacity-60"
        >
          {isSubmitting ? 'Creating...' : 'Create Event'}
        </button>
        </div>
        <p className="pt-24 text-center text-[10px] text-[#A4ABBC]">© 2024 Occacia Event Management Platform. All rights reserved.</p>
      </div>
    </section>
  );
};

export default CustomerCreateEvent;

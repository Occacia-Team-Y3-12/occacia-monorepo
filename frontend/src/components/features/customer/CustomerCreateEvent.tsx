'use client';

import { PERSONA_OPTIONS, useCreateEvent } from '@/hooks/customer/useCreateEvent';

const CustomerCreateEvent = () => {
  const {
    eventType,
    title,
    description,
    selectedPersonaIds,
    errors,
    isSubmitting,
    titlePlaceholder,
    setEventType,
    setTitle,
    setDescription,
    togglePersona,
    handleCreate,
    handleCancel,
  } = useCreateEvent();

  return (
    <section className="mx-auto w-full max-w-[1040px] pb-10">
      <div className="mb-6">
        <p className="text-xs font-medium text-[#8A90A1]">Events &gt; Create New Event</p>
        <h1 className="mt-2 text-[38px] font-bold leading-tight text-[#141A2A]">Create New Event</h1>
        <p className="mt-2 text-sm text-[#7B8398]">Set up your next masterpiece. Fill in the essential details to get started.</p>
      </div>

      <div className="space-y-5">
        <div className="rounded-2xl border border-[#E4E8F2] bg-[#F9FAFC]">
          <div className="flex items-center gap-2 border-b border-[#E4E8F2] px-5 py-4">
            <span className="text-sm font-semibold text-[#1B2237]">General Information</span>
          </div>

          <div className="space-y-4 px-5 py-5">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <div>
                <label className="mb-2 block text-xs font-medium text-[#667085]">Event Type</label>
                <select
                  value={eventType}
                  onChange={(event) => setEventType(event.target.value as typeof eventType)}
                  className="h-11 w-full rounded-xl border border-[#DFE3ED] bg-[#F1F3F8] px-3 text-sm text-[#1D2538] outline-none"
                >
                  <option value="individual">Individual</option>
                  <option value="group">Group</option>
                  <option value="others">Others</option>
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
              </div>
            </div>

            <div>
              <label className="mb-2 block text-xs font-medium text-[#667085]">Description</label>
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Briefly describe the theme, goals, or schedule..."
                rows={5}
                className="w-full resize-none rounded-xl border border-[#DFE3ED] bg-[#F1F3F8] px-3 py-3 text-sm text-[#1D2538] outline-none placeholder:text-[#9BA3B4]"
              />
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-[#E4E8F2] bg-[#F9FAFC]">
          <div className="flex items-center gap-2 border-b border-[#E4E8F2] px-5 py-4">
            <span className="text-sm font-semibold text-[#1B2237]">Assign People</span>
          </div>

          <div className="px-5 py-5">
            <p className="mb-4 text-xs text-[#8A90A1]">
              Select one or more people to customize the event experience for specific audience types.
            </p>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              {PERSONA_OPTIONS.map((persona) => {
                const selected = selectedPersonaIds.includes(persona.id);
                return (
                  <button
                    type="button"
                    key={persona.id}
                    onClick={() => togglePersona(persona.id)}
                    className={`flex items-center justify-between rounded-xl border px-4 py-3 text-left transition-colors ${
                      selected
                        ? 'border-[#3563E9] bg-[#EAF0FF]'
                        : 'border-[#DFE3ED] bg-[#F1F3F8] hover:border-[#BFC7D8]'
                    }`}
                  >
                    <div>
                      <p className="text-sm font-semibold text-[#141A2A]">{persona.name}</p>
                      <p className="text-xs text-[#7D8599]">{persona.role}</p>
                    </div>
                    <span
                      className={`h-5 w-5 rounded-full border ${
                        selected ? 'border-[#3563E9] bg-[#3563E9]' : 'border-[#C4CAD8] bg-transparent'
                      }`}
                    />
                  </button>
                );
              })}
            </div>

            <button
              type="button"
              className="mt-3 inline-flex h-12 items-center gap-2 rounded-xl border border-dashed border-[#CFD6E6] px-4 text-sm font-medium text-[#657089]"
            >
              <span className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-[#CFD6E6] text-base">+</span>
              New People
            </button>
          </div>
        </div>
      </div>

      {errors.form && <p className="mt-4 text-sm font-medium text-[#C23A3A]">{errors.form}</p>}

      <div className="mt-8 flex items-center justify-end gap-5">
        <button
          onClick={handleCancel}
          disabled={isSubmitting}
          className="text-sm font-semibold text-[#4F5871] disabled:opacity-60"
        >
          Cancel
        </button>
        <button
          onClick={handleCreate}
          disabled={isSubmitting}
          className="h-11 rounded-xl bg-[#2046C9] px-6 text-sm font-semibold text-white shadow-[0_8px_20px_rgba(32,70,201,0.28)] disabled:opacity-60"
        >
          {isSubmitting ? 'Creating...' : 'Create Event'}
        </button>
      </div>
    </section>
  );
};

export default CustomerCreateEvent;

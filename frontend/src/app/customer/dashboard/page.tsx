import Image from 'next/image';

export default function CustomerDashboard() {
  const templates = [
    { title: 'Birthday', image: '/images/customer/dashboard/birthday.svg' },
    { title: 'Anniversary', image: '/images/customer/dashboard/anniversary.svg' },
    { title: 'Farewell', image: '/images/customer/dashboard/farewell.svg' },
    { title: 'Get Together', image: '/images/customer/dashboard/get_together.svg' },
  ];

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-xl bg-[#2443F4] px-10 py-8 text-white shadow-[0_10px_30px_rgba(36,67,244,0.25)]">
        <div className="absolute right-10 top-1 h-[120px] w-[160px] opacity-15">
          <svg viewBox="0 0 220 160" className="h-full w-full" fill="none" stroke="currentColor" strokeWidth="8">
            <path d="M55 120 105 20 155 120z" />
            <path d="M170 20c15 5 25 15 30 30" />
            <path d="M150 10c25 8 45 28 53 53" />
          </svg>
        </div>

        <h2 className="text-[50px] leading-[1.05] font-extrabold tracking-tight">Welcome back, Alex!</h2>
        <p className="mt-4 max-w-[560px] text-[22px] font-medium leading-relaxed text-[#E4EAFF]">
          Ready to plan your next event? We&apos;ve updated our vendor lists with top-rated local catering and decor services just for
          you.
        </p>

        <button className="mt-8 inline-flex items-center gap-2 rounded-lg border border-white/30 bg-white px-5 py-3 text-sm font-semibold text-[#2443F4]">
          <span className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-[#2443F4]">+</span>
          Start Planning
        </button>
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-[32px] font-bold text-[#151A26]">Quick Start Templates</h3>
          <button className="text-sm font-semibold text-[#6736FF]">View all templates</button>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {templates.map((template) => (
            <button key={template.title} className="group relative h-[120px] overflow-hidden rounded-2xl text-left">
              <Image
                src={template.image}
                alt={template.title}
                fill
                className="object-cover transition-transform duration-300 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/55 via-black/20 to-transparent" />
              <span className="absolute bottom-3 left-3 text-xl font-semibold text-white">{template.title}</span>
            </button>
          ))}
        </div>
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-[32px] font-bold text-[#151A26]">Your Events</h3>
          <button className="inline-flex items-center gap-1 text-sm font-semibold text-[#7F13EC]">
            <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 6h18M7 12h10m-7 6h4" />
            </svg>
            Filter
          </button>
        </div>

        <div className="space-y-4">
          <article className="flex items-center justify-between rounded-2xl border border-[#ECECF0] bg-white px-5 py-4 shadow-[0_3px_14px_rgba(26,30,62,0.06)]">
            <div className="flex items-center gap-3">
              <Image src="/icons/customer/dashboard/cake.svg" alt="Birthday" width={46} height={46} className="h-[46px] w-[46px]" />
              <div>
                <h4 className="text-[21px] font-semibold text-[#1B2233]">Sarah&apos;s 30th Birthday Bash</h4>
                <p className="text-sm text-[#8890A1]">Oct 24, 2023   New York, NY</p>
              </div>
            </div>
            <span className="rounded-full bg-[#FFEDCC] px-4 py-1.5 text-xs font-semibold text-[#B26B00]">In Progress</span>
          </article>

          <article className="flex items-center justify-between rounded-2xl border border-[#ECECF0] bg-white px-5 py-4 shadow-[0_3px_14px_rgba(26,30,62,0.06)]">
            <div className="flex items-center gap-3">
              <Image src="/icons/customer/dashboard/heart.svg" alt="Anniversary" width={46} height={46} className="h-[46px] w-[46px]" />
              <div>
                <h4 className="text-[21px] font-semibold text-[#1B2233]">Annual Wedding Anniversary</h4>
                <p className="text-sm text-[#8890A1]">Sep 12, 2023   Paris, France</p>
              </div>
            </div>
            <span className="rounded-full bg-[#DDF8E5] px-4 py-1.5 text-xs font-semibold text-[#187E3D]">Completed</span>
          </article>
        </div>
      </section>

      <section className="flex min-h-[220px] flex-col items-center justify-center rounded-3xl border border-dashed border-[#D9BCFA] bg-[#F5ECFF] text-center">
        <Image src="/icons/customer/dashboard/event.svg" alt="No events" width={72} height={72} className="h-[72px] w-[72px]" />
        <h4 className="mt-3 text-[35px] font-bold text-[#262E45]">No upcoming events?</h4>
        <p className="mt-2 max-w-[410px] text-lg leading-relaxed text-[#7E869C]">
          You don&apos;t have any new events planned yet. Let&apos;s create something memorable together.
        </p>
      </section>
    </div>
  );
}